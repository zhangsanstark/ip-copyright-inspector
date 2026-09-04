SQLAlchemy 异步数据库：从一个 Python 对象，到真正提交的一行记录

数据库部分最容易混淆的地方，不是 SQL 怎么拼，而是“我现在改的是 Python 对象，还是已经改了数据库；如果改了，其他事务是否已经能看见”。本章沿着这个问题逐步展开。

阅读导航：1 对象分工；2 模型；3 完整增查改删；4 查询结果；5 事务过程；6 会话与并发；7 仓库流程；8 三道完整练习；9 SQLite 边界与资料。

所有 runnable 实验只使用内存数据库或临时数据库，不连接外部服务。执行 `python scripts/check_handbook_examples.py --chapter 19 --show-output` 可以统一核对。

1）先把引擎、会话工厂、会话和事务分开

1.1 引擎负责怎么连接，不代表某一次业务操作

`create_async_engine(url)` 创建异步引擎。URL 包含数据库类型、驱动和位置，例如 `sqlite+aiosqlite:///./demo.db`。

这里 `sqlite` 是数据库方言，`aiosqlite` 是异步驱动，`./demo.db` 是相对于进程当前工作目录的文件。换一个启动目录，可能就创建了另一个同名数据库。

创建引擎通常不会立即建立数据库连接；真正执行工作时才需要连接。引擎可以在应用范围内复用，里面还负责连接管理。

Java 背景可以把它与数据源、连接池所在的这一层联系起来，但不要直接记成“engine 就是一条 JDBC Connection”。它不是某一次事务专用的连接对象。

1.2 会话工厂是配置好的创建方式

`async_sessionmaker(engine, expire_on_commit=False)` 返回一个会话工厂。之后调用 `factory()`，才得到具体的 AsyncSession。

工厂适合集中保存公共配置。它本身不是业务事务，也不会因为被调用了一次，就帮你插入数据。

1.3 会话记录这一次操作正在管理哪些对象

会话会跟踪对象状态、待发送的变化、当前事务以及已加载的对象。它不是一个适合全局共享的无状态工具类。

同一个会话中，针对同一数据库身份加载的对象通常会复用同一实例。这有助于避免一次业务操作内部拿到几个互相矛盾的对象副本，但也意味着旧值可能仍在会话中，需要根据情况刷新。

1.4 事务决定这一组数据库修改一起成功还是一起放弃

一次转账不能只扣款、不入账。事务就是让这两项修改作为一组处理的机制。会话与事务有关，但它们不是同一个概念：一个会话可以先完成一个事务，再开始下一个。

`async with factory() as session` 保证离开时关闭会话，不保证自动提交。想成功时提交、异常时回滚，可以明确使用事务上下文 `async with session.begin()`。

2）模型类：把表的结构写成可检查的 Python 声明

2.1 Mapped 和 mapped_column 各管一部分

`id: Mapped[int] = mapped_column(primary_key=True)` 中，`Mapped[int]` 给 Python 工具和 ORM 描述映射属性的类型；`mapped_column` 配置数据库列。

类名通常用于 Python 代码，`__tablename__` 用于数据库表名。二者可以不同。

主键用于标识一行。普通字符串字段即使“看起来不会重复”，也不会自动得到唯一约束；需要明确声明 `unique=True` 或相应约束。

`nullable=False` 是数据库不允许空值，`Mapped[str | None]` 是 Python 侧的可空类型表达。让两边设计一致，可以减少“类型工具允许、数据库拒绝”的意外。

2.2 创建表，不等于维护所有后续结构变更

`Base.metadata.create_all` 可以创建缺失的表，适合最小实验。它不会自动把已有表安全升级到任意新结构。

项目演进需要迁移工具，例如 Alembic。新增列、数据回填、约束变化，通常需要检查和计划，不能只把模型类改掉就认为数据库同步完成。

3）一个完整实验：新增、读取、修改、删除

3.1 先预测每一步的对象状态

刚构造 `Document(...)` 时，只存在一个普通 Python 对象，编号尚未由数据库生成。

`session.add(document)` 让会话管理它，登记“待新增”。`await session.flush()` 发出 INSERT，数据库生成编号，但还没有完成最终提交。

事务上下文正常退出时提交。下一个会话可以再按编号查询这条记录。下面每个步骤都有断言，不需要猜终端输出是否“差不多”。

```python
# runnable: hb19_crud
import asyncio
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    reviewed: Mapped[bool] = mapped_column(default=False, nullable=False)

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with factory() as session:
            async with session.begin():
                document = Document(title="文本 A", reviewed=False)
                assert document.id is None
                session.add(document)
                assert document.id is None
                await session.flush()
                assert isinstance(document.id, int)
                document_id = document.id

        async with factory() as session:
            document = await session.get(Document, document_id)
            assert document is not None
            assert document.title == "文本 A"
            assert document.reviewed is False

        async with factory() as session:
            async with session.begin():
                document = await session.get(Document, document_id)
                assert document is not None
                document.title = "文本 A：已核对"
                document.reviewed = True

        async with factory() as session:
            statement = select(Document).where(Document.reviewed.is_(True))
            result = await session.execute(statement)
            documents = result.scalars().all()
            assert len(documents) == 1
            assert documents[0].title == "文本 A：已核对"

        async with factory() as session:
            async with session.begin():
                document = await session.get(Document, document_id)
                assert document is not None
                await session.delete(document)

        async with factory() as session:
            assert await session.get(Document, document_id) is None
        print("新增、读取、修改、删除均已核对")
    finally:
        await engine.dispose()

asyncio.run(main())
```

3.2 逐个解释调用，而不是只背 CRUD 名字

`session.get(Document, document_id)` 按主键找对象；不存在返回 `None`，不是自动抛“找不到”的异常。

`select(Document)` 先构造查询表达式，还没有发送 SQL。继续 `.where(...)` 是添加条件，仍然在构造表达式。`await session.execute(statement)` 才真正执行查询。

读取到的对象被当前会话跟踪。给 `document.title` 赋值之后，会话知道它有变化；后续 flush 或 commit 会安排 UPDATE。不是每赋值一个属性就马上发送一条 UPDATE。

`await session.delete(document)` 把对象登记为删除；事务提交前会发出 DELETE。删除操作同样受事务控制，不是 Python 对象从内存消失就自动删表里的行。

3.3 为什么例子反复打开新会话

这是为了让每个核对点更清楚：上一步提交以后，下一步用另一份会话去观察。否则同一会话中已经存在的对象，可能让你误以为自己验证了“数据库中的最终结果”。

真实业务不必为每个字段都开会话。应按完整业务操作划定边界，既避免无限拉长事务，也避免把本应一起成功的操作拆散。

4）execute 的返回值不是一个实体列表

4.1 先看查询选了几项

`select(Document)` 选的是一项 ORM 实体；`select(Document.id, Document.title)` 选的是两列。Result 先按结果行组织内容，因此常要再选择“取整行”还是“只取第一列”。

`result.all()` 取得行列表。`result.scalars().all()` 每行只取第一项，形成标量列表。如果选了两列却用 scalars，第二列不会跟着保留。

这里的 scalar 可以是整数，也可以是 Document 对象；意思是“每行的一项”，不是“只能是数字”。

4.2 one、one_or_none、first 不是随意替换

`scalar_one()` 要求恰好一行，再取该行第一项。零行或多行都会报错。

`scalar_one_or_none()` 允许零行，返回 `None`；多行仍报错。适合业务上“最多一条”的场景，可以帮你暴露重复数据。

`first()` 只取第一行，不帮你断言数据唯一；要限制数据库返回的行数，应在语句上写 `.limit(1)`，不要把 Result 的 first 当作自动替 SQL 添加 LIMIT。

Result 是已经执行后的结果对象。普通 `await session.execute(...)` 返回的非流式 Result，调用 `.scalars().all()` 不再写 `await`。流式接口另有异步迭代方式，不应混写。

```python
# runnable: hb19_result_shapes
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.connect() as connection:
            statement = text("SELECT 1 AS id, 'A' AS title UNION ALL SELECT 2, 'B'")
            rows = (await connection.execute(statement)).all()
            assert [tuple(row) for row in rows] == [(1, "A"), (2, "B")]
            first_columns = (await connection.execute(statement)).scalars().all()
            assert first_columns == [1, 2]
            mappings = (await connection.execute(statement)).mappings().all()
            assert [dict(row) for row in mappings] == [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}]
            single = (await connection.execute(text("SELECT 42"))).scalar_one()
            assert single == 42
        print("同一组结果可以取整行、第一列或字段名映射")
    finally:
        await engine.dispose()

asyncio.run(main())
```

为了分别演示三种读取方式，例子执行了三次语句。不要把一个已经消费完的结果集当成可以无限重复遍历的普通列表。

5）flush、commit、rollback、refresh：四个动作四个问题

5.1 flush 回答：把当前待处理变化交给数据库了吗

flush 会发送必要的 INSERT、UPDATE、DELETE，使数据库在当前事务里处理这些修改。数据库约束也可能在此时拒绝数据，例如唯一键冲突。

对象得到自增编号，通常只证明 INSERT 已经发生，不证明事务已经提交。即使稍后回滚，这个 Python 对象上仍可能保留曾获得的编号；不要只看编号是否为空判断保存成功。

5.2 commit 回答：当前事务是否按数据库规则完成提交

commit 会先处理尚未 flush 的变化，再提交事务。因此很多简单场景不必显式先 flush；本仓库提前 flush，是因为需要先获取生成的记录编号。

提交成功以后，结果的可见性仍受其他连接正在使用的事务隔离和快照影响。“其他事务随时立刻刷新成新值”并不是 commit 的保证。

断电级持久性还依赖数据库、日志和存储配置。本章所说“提交保存”，指业务层完成数据库事务提交，不是承诺任何硬件故障下绝不丢失。

5.3 rollback 回答：放弃这个事务的修改了吗

rollback 撤销当前事务尚未提交的修改，也让会话从相应的失败状态恢复。它不能撤销已经完成的前一个 commit，更不能把已经发送出去的邮件或 HTTP 请求收回来。

数据库失败后如果还要复用同一会话，应正确 rollback。只捕获异常、打印一行文字，然后继续用处于失败状态的会话，常常会得到第二个异常。

5.4 refresh 回答：要不要重新从数据库取这个对象的值

`await session.refresh(record)` 是读取动作：重新查询数据库，更新对象属性。它不是“加强版 commit”，也不会替你提交。

例如数据库生成时间戳，或者数据库端规则修改了字段，可以考虑刷新。是否需要取决于映射、返回值支持以及属性当前是否已加载，而不是每次 commit 后机械补一行。

`expire_on_commit=False` 避免提交后把已加载属性全部标为过期，方便异步代码继续读取。它不是“对象永远与数据库一致”；其他事务更新后，仍可能需要重新查询或刷新。

5.5 自动 flush 为什么会让错误出现在 SELECT 前后

会话默认可能在执行 ORM 查询之前自动 flush 待处理变化。因此你刚 add 了一条非法记录，下一句写的是查询，也可能先因为 INSERT 失败而报错。

临时使用 `with session.no_autoflush:` 可以避免某些查询触发的自动 flush，但它不是“不保存”的开关。显式 flush 和 commit 仍会处理变化。

6）每个并发任务要有自己的会话

6.1 原因不是语法限制，而是事务状态不能乱交叉

AsyncSession 包含当前事务、待保存对象和执行状态。如果两个任务共用它，一个正在 flush，另一个又开始查询或回滚，操作边界就互相干扰。

`asyncio.gather()` 可以安排多个协程并发，但不会自动给它们复制会话。正确做法是让每个任务在自己的函数里创建会话。

多个会话可以复用同一引擎和会话工厂。把“共享连接配置”与“共享一份活动事务”区分开即可。

6.2 并发不等于每个数据库都能同时高速写

SQLite 有自身的写入并发限制。多个异步任务各有会话，只是正确划分了应用状态，并没有取消数据库的锁。

长事务、过多写任务、较短超时都可能导致锁等待或失败。可以先缩短事务和控制并发，再根据负载选择其他数据库；不要看到锁错误就无条件重试十次。

7）仓库真实记录的一次回滚实验

7.1 用真实模型观察“有编号但没有保存”

下面先 flush，再主动 rollback，然后用新会话数行数。随后做一次真正提交，对照两种结果。

```python
# runnable: hb19_repository_transaction
import asyncio
from dataclasses import asdict
from sqlalchemy import func, inspect, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from ip_copyright_inspector.database import Base, ComparisonRecord
from ip_copyright_inspector.similarity import compare_texts

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    fields = asdict(compare_texts("abcd", "abce", ngram_size=2))
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with factory() as session:
            record = ComparisonRecord(**fields)
            assert inspect(record).transient
            session.add(record)
            assert inspect(record).pending
            await session.flush()
            assert inspect(record).persistent
            assert record.id is not None
            await session.rollback()
        async with factory() as session:
            count = await session.scalar(select(func.count()).select_from(ComparisonRecord))
            assert count == 0
        async with factory() as session:
            record = ComparisonRecord(**fields)
            session.add(record)
            await session.flush()
            saved_id = record.id
            await session.commit()
        async with factory() as session:
            saved = await session.get(ComparisonRecord, saved_id)
            assert saved is not None and saved.score == 0.5
            assert saved.left_normalized_length == 4
        print("flush 后可有编号；rollback 后仍是零行；commit 后才核对到记录")
    finally:
        await engine.dispose()

asyncio.run(main())
```

这里 `inspect(record).persistent` 是 ORM 对象状态名称，表示它已属于会话中对应数据库身份的持久对象状态；不要把这个英文单词误读成“事务已持久提交”。上面的断言明确证明两者不是一回事。

8）三道练习，答案都包含最后一次数据库核对

8.1 练习一：两次更新必须一起成功

要求：A 有 100，B 有 20。从 A 转 30 给 B，中途模拟异常，最终仍应是 100 与 20。然后再正常转一次，最终应是 70 与 50。

```python
# runnable: hb19_answer_atomic_transfer
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    balance: Mapped[int]

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with factory.begin() as session:
            session.add_all([Account(id=1, balance=100), Account(id=2, balance=20)])

        async def transfer(fail: bool):
            async with factory.begin() as session:
                left = await session.get(Account, 1)
                right = await session.get(Account, 2)
                assert left is not None and right is not None
                left.balance -= 30
                await session.flush()
                if fail:
                    raise RuntimeError("模拟中途失败")
                right.balance += 30

        try:
            await transfer(True)
        except RuntimeError:
            pass
        async with factory() as session:
            values = (await session.scalars(select(Account.balance).order_by(Account.id))).all()
            assert values == [100, 20]
        await transfer(False)
        async with factory() as session:
            values = (await session.scalars(select(Account.balance).order_by(Account.id))).all()
            assert values == [70, 50]
        print("失败一起回滚，成功一起提交")
    finally:
        await engine.dispose()

asyncio.run(main())
```

这个例子验证的是单次事务原子性，不是完整资金系统。它没有处理并发扣款、余额约束、幂等请求等问题；不要把演示代码当作可直接接入支付的实现。

8.2 练习二：唯一键失败之后，恢复会话再继续

要求：同名标签只能存在一条。重复插入应失败，rollback 后再插入另一个名称，最终得到两个不同标签。

```python
# runnable: hb19_answer_recover
import asyncio
from sqlalchemy import String, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with factory() as session:
            session.add(Tag(name="python"))
            await session.commit()
            session.add(Tag(name="python"))
            try:
                await session.flush()
            except IntegrityError:
                await session.rollback()
            else:
                raise AssertionError("重复标签本应失败")
            session.add(Tag(name="api"))
            await session.commit()
            names = (await session.scalars(select(Tag.name).order_by(Tag.name))).all()
            assert names == ["api", "python"]
        print("错误事务回滚后，会话才能继续处理下一次操作")
    finally:
        await engine.dispose()

asyncio.run(main())
```

先查再插入不能替代唯一约束：两个并发请求可能都先查到不存在。最终仍需要数据库约束，并在业务上处理冲突。

8.3 练习三：绑定参数，让内容只是内容

要求：保存看起来像 SQL 语句的文本，表不能被删除。答案使用绑定参数，不把输入拼成 SQL。

```python
# runnable: hb19_answer_bound_parameters
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    suspicious_text = "x'); DROP TABLE notes; --"
    try:
        async with engine.begin() as connection:
            await connection.execute(text("CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT NOT NULL)"))
            await connection.execute(
                text("INSERT INTO notes (body) VALUES (:body)"),
                {"body": suspicious_text},
            )
        async with engine.connect() as connection:
            values = (await connection.execute(text("SELECT body FROM notes"))).scalars().all()
            assert values == [suspicious_text]
        print("输入作为绑定值保存，没有变成 SQL 结构")
    finally:
        await engine.dispose()

asyncio.run(main())
```

绑定值保护的是值的位置，不能把用户输入直接当作表名、列名或排序方向。动态选择字段时，应先映射到程序允许的有限选项。

9）SQLite 的适用范围、排查顺序与资料

9.1 本地方便，不代表与所有数据库行为一致

SQLite 适合单机实验和许多轻量场景。它的写锁、类型行为、外键设置、日期时间处理与 PostgreSQL 等数据库存在差异。

声明 `DateTime(timezone=True)` 不意味着 SQLite 自动提供完整时区语义。应用需要明确如何存储和恢复时间；涉及迁移数据库时，应补上真实目标数据库测试。

内存 SQLite 与文件 SQLite 的连接和共享行为也不同。不要在不同进程分别连 `:memory:`，然后以为它们会操作同一个数据库。

9.2 发现“不见了的数据”，按这条顺序排查

先看数据库 URL 和当前工作目录；再看是否只 add、没有 flush 或 commit；再看后续是否 rollback；再看查询是否在旧事务或旧会话中；最后检查条件和数据库约束。

可以在隔离实验里给引擎加 `echo=True` 观察 SQL，但真实业务日志可能包含参数内容，应先考虑脱敏。不要为了排错把敏感文本长期写进日志。

9.3 官方资料

[SQLAlchemy 异步扩展](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) 解释 AsyncSession 的使用与并发边界；[Session 基础](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) 解释 flush、commit、rollback 和对象管理。

[ORM 查询指南](https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html)、[事务管理](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)、[SQLite 方言](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html) 对应结果读取、事务上下文和数据库差异。
