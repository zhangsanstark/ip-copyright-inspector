后端工程化：把一条 Python 接口串起来

内容导航：1 请求流程；2 类型提示；3 Pydantic；4 FastAPI；5 异步数据库；6 相似度算法；7 依赖管理；8 测试；9 部署；10 运行与排错。先读第 1 点，再按遇到的问题查对应编号。

1）先看全貌：一条请求到底经过了什么

1.1 收 JSON、检查、算分、保存、返回

仓库里的服务只做一件事：接收两段文本，计算字符片段的重合程度，保存计算信息，再把结果返回给调用方。它给的是技术相似度，不是法律判断。

把一次请求按顺序展开，就容易看懂每个组件为什么存在：

- 收 JSON：FastAPI 找到对应路由，准备接收请求体。
- 检查参数：Pydantic 检查字段有没有缺、文本是不是空白、`ngram_size` 有没有超出范围。
- 算分：普通 Python 函数切出字符片段，用集合计算 Jaccard 系数。
- 保存：SQLAlchemy 把长度、片段数量和分数等计算信息写进 SQLite，不保存原文。
- 返回：FastAPI 按响应模型整理结果，发送 JSON。

对 Java 后端来说，这条主线并不陌生：Controller 接请求，DTO 校验，Service 计算，数据库事务保存，最后返回响应。变的是工具和写法，不是要解决的问题。

1.2 每个文件管哪一段

- `main.py`：把请求接到正确的函数，安排会话、提交事务，并把失败转成合适的 HTTP 响应。这部分常叫“HTTP 适配层”。
- `schemas.py`：规定输入和输出有哪些字段、允许什么值。这份约定也叫“数据契约”，相当于请求 DTO、Bean Validation 和响应 DTO。
- `similarity.py`：只负责计算。同样的输入得到同样的结果，不需要 HTTP 或数据库，可对应无状态的 Domain Service。
- `database.py`：定义表对应的类，准备数据库引擎和会话工厂。映射类可先按 JPA Entity 理解。
- `tests/`：分别检查计算、字段规则和接口行为，不必先手动启动服务器。
- `pyproject.toml`：记录项目说明、依赖和测试配置。

`AsyncSession` 可以先理解成“这一次数据库操作的负责人”：它记住待写入的对象，执行 SQL，控制提交和回滚。这和 JPA 的 EntityManager 有相似之处，但不能照搬 Spring 代理事务或生命周期的细节，第 5 点会展开。

2）类型提示：写了 `int`，不代表运行时一定是 `int`

2.1 注解告诉工具你的打算，不自动拦住调用

在 Java 里，方法签名通常有编译器检查。Python 的类型注解主要帮助人、IDE 和静态检查工具理解代码；框架也可以读取它，但 Python 本身不会因此自动校验每次传参。

Python 3.11 可以直接写下面这些类型：`list[str]` 表示字符串列表，`str | None` 表示字符串或空值。

```python
from collections.abc import Iterable


def unique_names(names: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(name.strip() for name in names if name.strip()))


def find_name(user_id: int) -> str | None:
    return "Ada" if user_id == 1 else None
```

例如，给上面的 `find_name` 传一个字符串，函数照样会执行：

```python
find_name("1")
```

这次调用会返回 `None`，因为字符串 `"1"` 不等于整数 `1`。它甚至不一定报错，而是可能悄悄走到你没预料的分支。所以要把三件事分开：

- 类型提示：帮助写代码时发现问题，支持补全、重构和静态分析。
- Pydantic：检查外部传来的数据，必要时转换类型，让业务代码收到符合约定的对象。
- 业务代码：判断实际规则是否成立，例如输入文本不能只包含空白。这类输入规则也可以写进 Pydantic 验证器。

2.2 参数只要求“够用的能力”

如果函数只需要取长度、遍历和按下标读取，就不必把参数写死成 `list`。下面的 `Sequence` 能让列表、元组等符合要求的对象都成为合理的输入；返回值则明确写成 `float`。

```python
from collections.abc import Sequence


def average(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("values must not be empty")
    return sum(values) / len(values)
```

再往前一步，如果你想要求“传进来的对象必须有 `load` 方法”，可以用 `Protocol` 把这个要求写给静态检查器：

```python
from typing import Protocol


class TextLoader(Protocol):
    def load(self, key: str) -> str: ...


def read_document(loader: TextLoader, key: str) -> str:
    return loader.load(key)
```

实现类不必像 Java 一样声明 `implements TextLoader`。只要 `load` 方法的签名兼容，静态检查器就可以接受。这叫“结构化子类型”：主要看对象会做什么，不只看它继承了谁。第一次读到这里，先记住这句话就够了。

2.3 `Any` 和 `object` 不是一回事

`Any` 更像对检查器说“这里先别管了”。用得太多，很多错误也就查不出来。`object` 则表示“可能是任何对象，但你得先确认类型，再调用具体方法”。外部输入还没查清类型时可以暂用 `object`，进入业务代码后尽量变成明确类型。

下面的命令可以直接调用仓库里的计算函数，不需要启动 HTTP 服务：

```powershell
uv run python -c "from ip_copyright_inspector.similarity import compare_texts; print(compare_texts('abcd', 'abce', ngram_size=2))"
```

回头检查自己的类型提示时，重点看这几处：

- 看到注解就以为运行时一定会拦截错误类型。
- 为了省事把所有值写成 `Any`，结果 IDE 和检查器都失去作用。
- 参数写成具体 `list`，其实函数只需要遍历或按下标读取，平白限制了可用的输入。
- 使用 Python 3.12 才有的 `type Alias = ...` 语法，却把项目最低版本写成 3.11。

记住：注解先提醒，入口再校验，业务规则另外判断。

3）Pydantic：把外部数据检查好，再交给业务代码

3.1 用模型写清楚“收什么，允许什么”

比如客户端传来 `ngram_size=9`，而接口只允许 1 到 8，应该在计算之前就告诉对方哪里错了。Pydantic 正是用来做这类输入检查的。

可以把请求模型理解成 Java 的“Jackson 反序列化 + DTO + Bean Validation”。不过转换细节不同：Pydantic 默认会进行一定的类型转换，不能只凭 Java 的经验判断哪些输入会通过。

继承 `BaseModel` 后，字段注解和 `Field` 就一起构成了规则。仓库的请求模型核心写法如下：

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    left_text: str = Field(min_length=1, max_length=100_000)
    right_text: str = Field(min_length=1, max_length=100_000)
    ngram_size: int = Field(default=3, ge=1, le=8)

    @field_validator("left_text", "right_text")
    @classmethod
    def reject_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must contain visible content")
        return value
```

看这个模型时，不用逐行背，先抓住四件事：

- `Field` 适合声明长度、数值边界和接口说明，这些信息也能进入 JSON Schema。
- `extra="forbid"` 会拒绝未声明字段，能尽早暴露客户端拼写错误；Pydantic 默认会忽略多余字段。
- `str_strip_whitespace=True` 统一去掉字符串两端空白，但不会删除正文中间空白。
- `field_validator` 补充 `Field` 表达不了的输入规则。检查通过后必须返回最终值，不是“不报错就完了”。

3.2 校验、转成字典、转成 JSON，分别用哪个方法

Pydantic 2 的常用方法可以按数据要去哪儿来记：

- `Model.model_validate(data)` 从 Python 对象校验。
- `Model.model_validate_json(raw)` 从 JSON 字符串或字节校验。
- `model.model_dump()` 生成 Python 字典。
- `model.model_dump_json()` 生成 JSON 字符串。
- `Model.model_json_schema()` 生成 JSON Schema。

故意传一个越界值，看看它怎样报告错误：

```python
from pydantic import ValidationError

try:
    request = CompareRequest.model_validate(
        {"left_text": "文本甲", "right_text": "文本乙", "ngram_size": 9}
    )
except ValidationError as error:
    print(error.errors())
```

3.3 能转换成功，不等于符合你的接口要求

字符串 `"3"` 和整数 `3` 对调用方来说可能是两种输入，但默认校验可能把前者转换成后者。如果接口必须严格区分，就要使用严格模式（strict mode），不能把“字段写了 `int`”当成已经严格检查。

另一个要留心的方法是 `model_construct()`：它绕过校验。不要因为名字看着方便就拿它接外部请求；只有数据已经可信，而且实测确有必要时才考虑。

想看正常输入校验后的样子，直接运行：

```powershell
uv run python -c "from ip_copyright_inspector.schemas import CompareRequest; print(CompareRequest(left_text='甲', right_text='乙').model_dump())"
```

实际写模型时，最容易漏掉这些细节：

- 从 Pydantic 1 迁移后继续使用 `dict()`、`parse_obj()` 等旧习惯，却不核对迁移文档。
- 验证器只在失败时 `raise`，成功路径忘记 `return value`。
- 不设置 `extra="forbid"`，客户端字段拼错后被静默忽略。
- 把数据库查询写进字段验证器，让一个简单模型校验偷偷产生 I/O。

记住：范围用 `Field`，单字段规则用 `field_validator`，字段之间的关系用模型验证器。

4）FastAPI：请求进来以后，由哪个函数处理

4.1 路由函数就是入口

`@app.post(...)` 和 Spring MVC 的映射注解很像：它把一个 URL、HTTP 方法和处理函数关联起来。FastAPI 还会读取函数签名，判断参数从哪里来、按什么规则检查、最后返回什么。

参数类型是 `BaseModel` 时，请求体会按 JSON 读取并校验。输入不符合规则时，通常返回 422，错误详情会指出字段位置。响应模型则检查、转换并过滤返回字段，避免把内部对象里的东西一股脑发出去。

下面只展示路由结构，不是可直接独立运行的完整代码。`CompareRequest` 和 `CompareResponse` 需要从数据模型模块导入；`build_response` 是表示“生成响应”的占位函数，仓库里没有这个函数。实际路由在 `main.py` 中完成计算、保存和响应构造：

```python
from fastapi import FastAPI

app = FastAPI()


@app.post("/comparisons")
async def create_comparison(request: CompareRequest) -> CompareResponse:
    return build_response(request)
```

4.2 错误要说清楚，但别把原文带出去

默认校验错误里可能包含用户提交的 `input`。如果用户传的是未公开文本，就不应把这个字段原样回显或写进日志。

本仓库专门处理了校验异常：保留字段位置、错误类型和提示，删除原始输入。这样调用方知道“哪个字段错了”，错误响应又不会带出整段正文。

启动服务后，FastAPI 默认还提供三个查看和调试接口的入口：

- `/docs` 是 Swagger UI。
- `/redoc` 是 ReDoc。
- `/openapi.json` 是机器可读的 OpenAPI 文档。

生产环境要另外决定谁能访问这些文档，不能因为默认能打开，就直接放到公网。

4.3 会话从哪里来：让 `Depends` 准备好再交给路由

路由需要数据库会话，但没必要每次都自己创建、关闭。仓库用 `Depends` 提供会话，并把这一组写法起了一个类型别名：

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

SessionDependency = Annotated[AsyncSession, Depends(get_session)]
```

这和 Spring 的依赖注入解决的是类似问题。不过 FastAPI 通常通过普通函数准备依赖，通过带 `yield` 的依赖在请求结束时清理资源，不要直接套用 Spring 代理对象的工作方式。

4.4 写了 `async def`，也不能随便放阻塞代码

异步的好处是：当前请求在等数据库或其他 I/O 时，事件循环可以处理别的任务。例如第 5 点的 `await session.commit()` 会等待数据库操作。

但普通的相似度计算仍然占用 CPU，不会因为放进 `async def` 就自动并行。如果大文本让计算明显变慢，要先测耗时，再决定限制输入、使用进程池，还是交给任务系统。

同理，不要在事件循环中直接调用 `time.sleep()`、同步数据库驱动或慢速同步 HTTP 客户端。应该选择异步版本，并在等待的位置写出 `await`。

应用用 `lifespan` 安排启动和退出时的工作：启动时创建示例表，退出时释放引擎。正式服务的表结构会持续变化，不能只靠 `create_all()`；需要 Alembic 等迁移工具记录每次改动，并规划回滚。

现在可以把服务启动起来：

```powershell
uv run uvicorn ip_copyright_inspector.main:app --reload
```

打开 `http://127.0.0.1:8000/docs` 就能直接试请求。

检查路由时，可以顺手问自己四个问题：

- 有没有用同步调用堵住事件循环？
- 有没有声明响应模型，防止内部字段意外暴露？
- 失败时是否返回了合适的状态码，而不是一律 200？
- 开发用的 `/docs`、`--reload` 和宽松配置，是否未经处理就带到了公网？

记住：路由安排流程，模型检查字段，业务函数计算，会话负责数据库操作。

5）SQLAlchemy 异步 ORM：对象怎么存进去，事务怎么算完成

5.1 先分清引擎、工厂、会话

这三个名字经常一起出现，但各管一件事：

- `create_async_engine()` 创建引擎，管理如何连接数据库、使用哪种驱动以及连接池。
- `async_sessionmaker()` 创建会话工厂，用它给每次独立操作准备一个会话。
- `AsyncSession` 记住本次待处理的对象，执行查询或写入，并控制事务。

这里的会话有点像 JPA EntityManager：它跟踪对象和数据库之间的状态，这部分也叫“持久化上下文”。但本例的提交、回滚和 `await` 都直接写在代码里，不是靠 Spring 事务代理代劳。

连接 URL 也要写对驱动。仓库默认用异步 SQLite：

```text
sqlite+aiosqlite:///./ip_copyright_inspector.db
```

SQLite 可以保存时间值，但本身没有完整的“带时区时间类型”。模型写了 `timezone=True`，不代表读出来的对象一定带时区。涉及跨时区时，要统一存储约定，并用测试确认写进去、读出来分别是什么样子。

切换 PostgreSQL 时需要安装相应异步驱动，并把环境变量改成类似 `postgresql+asyncpg://...` 的 URL。不要把口令写入仓库。

5.2 映射类：哪张表、哪一列，写在类里

SQLAlchemy 2 的声明式映射把 Python 类型和数据库列放在一起。可以先按 JPA Entity 理解：下面的类对应 `comparison_records` 表，`id` 是主键，`score` 保存分数。

```python
from sqlalchemy.orm import Mapped, mapped_column


class ComparisonRecord(Base):
    __tablename__ = "comparison_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    score: Mapped[float]
```

5.3 `add`、`flush`、`commit`，不是三个同义词

下面沿用上方只包含 id、score 的精简映射，展示新增记录的执行顺序；session 和异常类型需要在上下文中准备。这不是仓库真实映射的完整创建代码：真实 `ComparisonRecord` 还有 ngram_size、长度和计数等必填字段，不能只传 score。可运行实现见 `src/ip_copyright_inspector/main.py`：

```python
record = ComparisonRecord(score=0.75)
session.add(record)

try:
    await session.flush()
    record_id = record.id
    await session.commit()
except SQLAlchemyError:
    await session.rollback()
    raise
```

`add()` 先登记“这个对象要写入”，本身不等于已经执行 INSERT。`flush()` 才在当前事务中把改动发给数据库，通常这时已经能拿到自增主键。`commit()` 表示真正提交这次事务。

`refresh()` 是另一件事：重新查询数据库，用查到的值刷新对象。它不是拿主键的必经步骤。如果只是想返回主键，先 `flush()` 取到 `record.id`，再提交即可。

为什么不在提交后再 `refresh()`？因为后面那次查询也可能失败，结果就是“数据库明明已经保存成功，接口却说失败”。此时再回滚，也撤不回已经提交的数据。异常路径仍然要调用 `rollback()`，避免继续使用处于失败事务状态的会话。

5.4 一个并发任务一个会话，别共用一个来抢着操作

`AsyncSession` 会记录当前事务和对象状态，不能让多个并发 task 同时共享。尤其不要把同一个 session 塞给多个 `asyncio.gather()` 子任务。

本例由 FastAPI 依赖为每个请求提供一个会话。如果一个请求内部还要并发跑多个数据库任务，各任务也应有自己的会话，而不是因为“都在同一次请求里”就可以共享。

查询则使用 2.0 风格的 `select()`：

```python
from sqlalchemy import select

statement = select(ComparisonRecord).where(ComparisonRecord.score >= 0.8)
result = await session.execute(statement)
records = result.scalars().all()
```

5.5 看着像读属性，也可能在查数据库

访问尚未加载的关联对象时，ORM 可能临时发一条查询。这就是“隐式 I/O”：代码里没有明显的查询调用，却发生了数据库访问。在异步场景中，这类访问可能引发 `MissingGreenlet`。

先记住一个排查方向：可能查库的地方，要能看见清楚的 `await`。遇到关联数据问题，再查预加载、显式查询或 `AsyncAttrs`，不用一开始把所有机制背下来。

本例只保存长度、n-gram 数量、交集、并集和分数，不保存原文。这能减少内容泄露风险，但不代表数据安全已经做完；真实服务仍需要数据分级、保留周期、访问审计和删除机制。

启动 API 时，初始化逻辑就会在当前目录创建 SQLite 文件和示例表；成功提交一次比较请求后，才会新增对应记录：

```powershell
uv run uvicorn ip_copyright_inspector.main:app --reload
```

如果数据库代码出错，先核对这些常见原因：

- URL 写成同步方言 `sqlite:///...`，却交给异步引擎。
- `commit()` 失败后不 `rollback()`，继续复用失败状态的会话。
- 多个并发 task 共享同一个 `AsyncSession`。
- 访问未加载关系，意外触发异步隐式 I/O 和 `MissingGreenlet`。
- 用 `create_all()` 代替生产迁移。

记住：会话不并发共享；`flush` 发 SQL，`commit` 才提交，失败要回滚。

6）相似度算法：分数到底是怎么算出来的

6.1 先整理文本，再切成片段

本例不理解句子的含义。它把文本切成小片段，放进集合，再看两个集合重合多少。你用 Java 的两个 `Set<String>`，通过 `retainAll` 求交集，再求并集数量，也能做出同样的核心计算。

切片之前，文本先做三步处理：Unicode NFKC 归一化、`casefold()` 大小写折叠、删除 Unicode 空白。可以先理解为“把约定可统一的写法统一，再比较”。标点会保留，不做分词，也不推断语义。

6.2 用四个字母手算一次

当 `n=2` 时：

```text
abcd -> {ab, bc, cd}
abce -> {ab, bc, ce}
交集 -> {ab, bc}
并集 -> {ab, bc, cd, ce}
Jaccard -> 2 / 4 = 0.5
```

公式就是“去重后的共同片段数 ÷ 去重后的全部片段数”，结果在 0 到 1 之间。上面两边共有 `ab`、`bc` 两种片段，合起来有四种，所以分数是 0.5。这就是 Jaccard 系数。

如果整理后的文本比 `n` 还短，就切不出足够长的片段。本仓库把整段短文本当成一个兜底 token（一个比较单元）。例如 `n=3` 时，`"甲乙"` 得到 `{甲乙}`，但它不是真正的 3-gram。两段相同短文本得 1，不同得 0，所以短文本分数可能从一个极端跳到另一个极端，更需要人工复核。

6.3 集合去重会丢信息，改 `n` 也会改分数含义

集合不保留出现次数，因此“一段话重复十次”不一定比“重复一次”更相似。如果你需要比较频率，可以继续试 multiset（保留次数的集合）、余弦相似度或编辑距离。

`n` 小时，更容易撞上相同的小片段；`n` 大时，要求更长的连续内容相同，短文本能切出的片段也更少。换了 `n`，就不能不重新评估还照用旧阈值。

6.4 分数能提示重合，不能直接判定权属

这个算法只回答：按指定规则整理后，两组字符片段重合多少。它不知道作者、授权链、创作时间，也不能识别改写后的语义等价，更不能代替对合理使用或实质性相似等问题的专业判断。因此接口固定返回免责声明。

不要凭感觉写“0.8 就侵权”。阈值应基于标注样本评估，最终判断还需要更多事实和具备相应职责的人参与。

下面这些做法容易让人误读结果，要特别避免：

- 把 0.8 之类的经验阈值写成法律结论。
- 只换 `n` 不重做评估，却继续沿用原阈值。
- 忘记集合会丢掉重复次数。
- 预处理版本变化后不记录，导致同一文本前后得分不同。

记住：切片、去重、交集除并集；分数用来筛查，不替人下结论。

7）uv 与 Poetry：换台电脑也能装出同一套环境

7.1 配置、锁文件、虚拟环境，各记住一个作用

用 Maven 或 Gradle 时，你会关心“声明了哪些依赖”“最后用了哪些版本”“运行时从哪里加载”。Python 项目同样要把这三件事分清：

- `pyproject.toml`：声明项目、构建方式和依赖范围。
- 锁文件：记录这次解析后具体选中了哪些版本。
- `.venv`：当前项目自己的 Python 环境，实际安装的包放在这里。

uv 和 Poetry 都能按项目配置准备环境、安装依赖、执行命令。重点不是两个都用熟，而是同一仓库选定一条路线，避免不同电脑各装出一套。

7.2 本仓库默认走 uv

仓库用 PEP 621 的 `pyproject.toml` 描述项目，最低 Python 版本是 3.11。运行依赖在 `[project].dependencies`，开发依赖在 `[dependency-groups].dev`。uv 默认会同步名为 `dev` 的组，所以 pytest 也会一起安装。

按已提交的锁文件准备环境，再测试、启动：

```powershell
uv sync --locked
uv run pytest
uv run uvicorn ip_copyright_inspector.main:app --reload
```

`uv run` 会在项目环境中执行命令，并在需要时检查锁文件和环境。提交 `uv.lock`，别人才能按同一份版本清单安装。CI 可使用 `uv sync --locked` 或 `uv sync --frozen`，避免构建时悄悄改动依赖解析结果。

7.3 Poetry 是另一条路线，不是再叠一层环境

Poetry 2.4 也能读取 `[project]` 主依赖和 PEP 735 的 `[dependency-groups]`，因此当前配置里的 dev group 也能给它使用：

```powershell
poetry install
poetry run pytest
poetry run uvicorn ip_copyright_inspector.main:app --reload
```

如果统一用 Poetry，就由它生成并提交 `poetry.lock`；统一用 uv，就以 `uv.lock` 为准。不要把两份锁文件混着用，还期待它们总能选出完全相同的版本。

只写依赖范围也不等于能复现环境：范围说的是“这些版本都允许”，锁文件才说明“这一套到底选了谁”。

环境问题经常出在这些地方：

- 同时维护两种锁文件，却没有明确 CI 到底信哪一个。
- 提交 `.venv`，把本机二进制和路径一起塞进仓库。
- 只写宽泛版本范围但不提交锁文件，导致不同电脑解析出不同组合。
- 安装后直接调用系统 `pytest`，实际没在项目环境里运行。

记住：配置说要什么，锁文件说用哪版，运行交给项目工具的 `run`。

8）pytest：把“我觉得没问题”变成能重复验证的结果

8.1 从最简单的一次断言开始

pytest 的基本用法很直接：准备输入，调用函数，写 `assert` 检查结果。可以按 JUnit 的测试方法理解普通测试函数；fixture 用来准备和清理资源；`parametrize` 对应参数化测试。

测试失败时，pytest 会展示断言两边的差异，帮你看清“期望什么，实际得到什么”。当前仓库把测试分成三层：

- `test_similarity.py` 验证确定性的纯函数、边界情况和可审计计数。
- `test_schemas.py` 验证空白、数值范围、多余字段和固定免责声明。
- `test_api.py` 用 FastAPI `TestClient` 和临时 SQLite 验证 201、422、503、数据库写入、失败回滚以及敏感原文不回显。

多组输入要检查同一种规则时，不用复制好几个函数，可以参数化：

```python
import pytest


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [("", "", 1.0), ("", "内容", 0.0), ("Python", "PYTHON", 1.0)],
)
def test_cases(left: str, right: str, expected: float) -> None:
    assert compare_texts(left, right).score == expected
```

除法得出的浮点数不一定能被二进制精确表示，比较这类结果时优先用 `pytest.approx()`，别把一个很小的表示误差当成算法写错了。

8.2 计算归计算，外部资源另测

纯函数测试只检查输入和输出，不应因为数据库或网络不可用而失败。接口集成测试才连接临时 SQLite，验证路由、字段规则和事务能否串起来。

本仓库给每个接口用例准备独立的临时库，用依赖覆盖模拟数据库失败；不访问真实网络，也不碰开发数据库。`TestClient` 放在 `with` 里，才能真正执行应用启动、退出和连接清理。

全部测试和单文件测试分别这样运行：

```powershell
uv run pytest
uv run pytest tests/test_similarity.py -q
```

测试结果不可靠时，先检查有没有这些问题：

- 测试之间共享可变全局状态，单独运行能过、一起运行失败。
- 用真实开发库或生产地址跑自动化测试。
- 浮点数一律用 `==` 比较。
- 只测正常路径，不测空值、边界和失败路径。

记住：纯函数先测，边界也测；外部资源要隔离，失败原因要能复现。

9）Uvicorn 与 Docker：代码写好了，由谁来运行

9.1 应用、服务器、运行环境，不是一个东西

FastAPI 负责应用逻辑，Uvicorn 负责接收连接并调用应用，Docker 则把运行时、依赖和代码打包起来。可以把 Uvicorn 粗略类比为承载 Java 应用的 Web Server，把镜像类比为包含 JRE、依赖和应用产物的部署包。

这里应用与服务器遵循 ASGI 接口约定：FastAPI 是 ASGI 应用，Uvicorn 是 ASGI 服务器。启动时给 Uvicorn 的这一段是导入字符串：

```text
ip_copyright_inspector.main:app
```

冒号左侧是模块路径，右侧是模块里的应用对象。也就是说，这条命令是在告诉 Uvicorn：“到这个模块里，找到名叫 `app` 的对象。”

`--reload` 用来在开发时监听代码变化，不用于生产；它和多 worker 是不同运行模式，不应一起使用。

9.2 能启动，不代表部署工作都完成了

正式部署时，各层还得把这些事接住：

- Uvicorn 处理 ASGI 生命周期与 HTTP 连接。
- 进程管理或编排系统负责重启、扩缩容和健康检查。
- 反向代理或入口网关负责 TLS、请求体限制、超时和可信代理头。
- 应用负责认证授权、业务限流、结构化日志和可观测性。

9.3 镜像装得下代码，装不下所有运维工作

Docker 镜像让一套运行环境可以反复部署，但密钥管理、数据库迁移、日志持久化和水平扩容仍需单独安排。

写 Dockerfile 时，先复制依赖文件并安装，再复制经常改的源码，这样更容易复用构建缓存。生产容器用非 root 用户运行，配置由环境变量或密钥系统提供，不把口令写进镜像。

容器里启动服务的命令可以是：

```text
uv run uvicorn ip_copyright_inspector.main:app --host 0.0.0.0 --port 8000
```

`0.0.0.0` 表示监听容器所有网络接口，不等于自动安全地暴露公网。端口发布、防火墙和入口认证仍由部署层决定。

看到“已经启动”以后，还要检查有没有这些误区：

- 把 `--reload` 当生产性能开关。
- 认为监听 `0.0.0.0` 就已经完成公网安全配置。
- 容器中以 root 运行，并把数据库口令写进 Dockerfile。
- 只增加 worker，不评估数据库连接数、内存和下游容量。

记住：FastAPI 处理业务，Uvicorn 接请求，Docker 打包环境；安全和运维还要单独做。

10）把服务跑通，再按现象排错

10.1 在仓库根目录启动

先准备环境，再测试，最后启动服务：

```powershell
uv sync
uv run pytest
uv run uvicorn ip_copyright_inspector.main:app --reload
```

浏览器打开 `http://127.0.0.1:8000/docs`，或者在另一个 PowerShell 发送：

```powershell
$body = @{
    left_text = "原创角色的红色披风和星形徽章"
    right_text = "角色佩戴星形徽章并穿红色披风"
    ngram_size = 2
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/api/v1/comparisons" `
    -ContentType "application/json" `
    -Body $body
```

第一次启动会在当前目录创建 `ip_copyright_inspector.db`。它是运行产物，不应当作为知识资料提交。接口返回的 `record_id` 对应数据库记录，但记录中没有左右原文。

10.2 出错时，先看错误出现在哪一段

- `ModuleNotFoundError`：确认在仓库根目录运行，并先执行 `uv sync`。
- Uvicorn 找不到 `app`：核对导入字符串左右两部分以及包名下划线。
- 请求得到 422：读取响应中的 `detail`，它会指出字段位置和失败规则；本仓库会删掉错误详情里的原始输入。
- SQLite 无法写入：检查当前目录权限，以及数据库文件是否被其他工具独占。
- `MissingGreenlet`：检查是否在异步上下文外触发了 ORM 隐式 I/O。
- 会话报失败事务：确认异常路径执行了 `rollback()`，并且没有跨并发任务共享会话。
- 端口占用：换用 `--port 8001`，或关闭占用 8000 的进程。

10.3 这份示例做到哪里，还没做到哪里

当前代码是最小示例，还没有认证、授权、速率限制、任务队列、数据库迁移、结构化日志、指标、追踪、CORS 策略和生产 Dockerfile。这些是后续要补的工作，不是因为示例没写就可以省略。不要直接把它当公网生产服务。

最后再守住一个界限：相似度只是筛查信号。判断具体内容是否侵权、权属属于谁、许可是否有效或是否涉及合理使用，需要更多事实、规则和适当的专业审查。
