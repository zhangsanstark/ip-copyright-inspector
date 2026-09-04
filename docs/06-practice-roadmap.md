可执行练习路线

这一篇不用从头背。每次选一小组：先猜结果，动手运行，再解释为什么。能改一处、补一个测试、说清一次报错，比单纯“运行成功”更有用。

路线导航：1 跑通接口；2 集合与算分；3 类型提示；4 输入校验；5 请求与响应；6 异步；7 数据库；8 测试；9 依赖；10 部署；11 服务补全；12 综合改动。

整条主线只有五步：收 JSON → 检查参数 → 算分 → 保存计算信息 → 返回 JSON。后面的练习都是拆开其中一段，看看它为什么这样写。

1）先跑通一次完整请求

1.1 准备环境，确认原项目能正常运行

- 安装 Python 3.11 或更高版本，确认 `python --version`。
- 安装 uv，确认 `uv --version`。
- 在仓库根目录运行 `uv sync`。
- 运行 `uv run pytest`，记下未修改代码时的测试结果，后面用它判断改动有没有影响原功能。
- 运行 `uv run uvicorn ip_copyright_inspector.main:app --reload`。
- 打开 `/docs`，执行一次健康检查和一次文本比较。

1.2 不急着改，先找到每一步在哪个文件

沿着请求看一遍：`main.py` 接收并安排流程，`schemas.py` 检查字段，`similarity.py` 计算分数，`database.py` 提供数据库映射和会话。保存成功后，路由再返回响应。

完成标志：能解释 `.venv`、`pyproject.toml`、锁文件和 `uv run` 各做什么；能指出 Uvicorn 导入字符串里的模块路径和应用对象。

记住：先同步，再测试，后启动。环境没确认好，先别急着改代码。

1.3 第一轮先做到什么程度，不要一上来改所有文件

先预测：执行 `uv sync` 后，当前终端直接输入 `python` 是否一定变成项目里的 Python？答案是不一定；`uv sync` 准备环境，不会自动替你激活当前终端。

操作：在仓库根目录运行 `uv run python -c "import sys; print(sys.executable)"`。核对路径是否指向项目 `.venv`，再运行 `uv run pytest`。测试先跑通，才有条件判断后面是不是自己的改动引入了问题。

接着只做一个固定请求：`left_text="abcd"`、`right_text="abce"`、`ngram_size=2`。参考答案是分数 0.5、交集 2、并集 4。如果页面能打开却返回 422，先看字段；如果 503，先看数据库；不要遇到任何错误都重新安装整个环境。

不想先处理启动端口，可以先执行 `05-backend-engineering.md` 第 4.6 点的完整 TestClient 实验。它已经准备临时数据库，能直接核对成功请求、错误请求和保存结果。

2）先不用框架，手算一次相似度

2.1 用集合把公式算明白

只读 `similarity.py`，先把下面两段文本切成连续的二元字符片段，也就是每片两个字符：

```text
abcd
abce
```

在纸上写出左右集合、交集和并集，再算分数。最后运行下面的命令，和自己的结果对一对：

```powershell
uv run python -c "from ip_copyright_inspector.similarity import compare_texts; print(compare_texts('abcd', 'abce', ngram_size=2))"
```

2.2 每次只改一个因素，观察分数为什么变

- 比较 `知识产权保护` 与 `知识 产权保护`，解释为什么结果为 1。
- 比较 `aaaa` 与 `aa`，观察集合去重带来的信息损失。
- 把 `n` 从 1 调到 4，记录短文本分数如何变化。
- 为标点、全角英文和大小写各加一个测试，不要只看最后的分数，也看看整理后的文本。
- 增加一个“保留空白”的归一化选项，也就是改变比较前的文本整理规则，并说明哪些已有测试会受影响。

做到这里，试着不用看代码说明：Jaccard 的分子是什么、分母是什么？为什么这个算法能算字符重合，却不等于理解句意，更不等于法律判断？

记住：切片成集合，交集除并集；算的是重合，不是裁决。

2.3 给自己一份能核对的中间结果

先预测 `abcd` 和 `abce` 在 `n=1、2、3、4` 时分别有哪些片段。别只猜哪个分数更大，写出交集和并集数量。

下面整段可以保存成单独脚本，用 `uv run python 文件名.py` 运行。它直接调用仓库函数，`sorted()` 只是为了让集合打印顺序固定，不改变算法。

```python
# runnable: ngram_answers
from ip_copyright_inspector.similarity import character_ngrams, compare_texts

for size in range(1, 5):
    left = sorted(character_ngrams("abcd", size))
    right = sorted(character_ngrams("abce", size))
    result = compare_texts("abcd", "abce", ngram_size=size)
    print(size, left, right, result.intersection_count, result.union_count, round(result.score, 6))

assert compare_texts("aaaa", "aa", ngram_size=2).score == 1.0
assert compare_texts("aaaa", "aa", ngram_size=3).score == 0.0
```

核对答案：`n=1` 是交集 3、并集 5、分数 0.6；`n=2` 是 2、4、0.5；`n=3` 是 1、3、约 0.333333；`n=4` 是 0、2、0。

最后两个断言为什么差这么多？`n=2` 时，`aaaa` 虽然能切出三次 `aa`，放进集合后只剩 `{aa}`，和右边一样。`n=3` 时，左边是 `{aaa}`，右边因为太短采用兜底 `{aa}`，两边没有共同元素。把这一步说清楚，就不是只记住“集合会去重”了。

3）补类型提示，看看它能帮什么、不能帮什么

3.1 先描述清楚输入和输出

给 `similarity.py` 的每个公共函数写出输入、输出类型，再回答这些问题：

- `set[str]` 与 `list[str]` 的语义差异是什么？
- 为什么结果用不可变的 `dataclass`，而不是随手装字段的 `dict`？这会怎样影响读取和修改？
- `str | None` 和“参数有默认值”是不是同一个概念？
- `Any` 与 `object` 对静态检查器的影响有何不同？

3.2 写一个“只要求方法，不要求共同父类”的例子

定义 `SimilarityStrategy` 协议，要求对象具备 `compare(left: str, right: str) -> float`。再写一个类，让它在 `compare` 方法里调用现有 Jaccard 函数。

先别改 API，只用单元测试调用这个类。重点是看清：实现类没有显式继承协议，也能具备要求的方法；协议则把这个要求提供给静态检查器。这就是给鸭子类型补上可检查的说明。

完成标志：故意传错类型时，能解释为什么注解本身不一定拦截调用，以及外部数据应该在哪一层接受校验。

记住：类型提示能提醒，运行时入口还得另外检查。

3.3 先照着写一份完整实现，再换一个实现类

预测：下面的 `JaccardStrategy` 没有继承 `SimilarityStrategy`，能不能传给 `evaluate`？先运行，再检查它有没有协议要求的同名方法。

```python
# runnable: strategy_answer
from typing import Protocol
from ip_copyright_inspector.similarity import compare_texts


class SimilarityStrategy(Protocol):
    def compare(self, left: str, right: str) -> float: ...


class JaccardStrategy:
    def compare(self, left: str, right: str) -> float:
        return compare_texts(left, right, ngram_size=2).score


def evaluate(strategy: SimilarityStrategy, left: str, right: str) -> float:
    return strategy.compare(left, right)


score = evaluate(JaccardStrategy(), "abcd", "abce")
print(score)
assert score == 0.5
```

核对：输出 0.5。运行能成功，是因为对象确实有可调用的 `compare`；协议负责向静态检查器说明这个要求，不会在调用时自动弹出校验器。

参考答案提示：`set[str]` 不保留重复次数，`list[str]` 会；不可变 dataclass 让计算结果的字段固定、不容易被后续误改；`str | None` 只决定能否接受空值，不决定参数能否省略；`Any` 放松检查，`object` 则要求使用具体能力前确认类型。

下一步不用碰 API，另写一个 `ExactMatchStrategy`，完全相同返回 1.0，否则返回 0.0，再交给同一个 `evaluate`。这时你只替换了“怎么算”，没有重写调用流程。

4）用 Pydantic 把输入错误拦在计算之前

4.1 先观察正常输入被整理成什么样

在仓库根目录执行 `uv run python`，进入使用项目环境的 Python 交互窗口（REPL），再执行下面的代码。`uv sync` 不会自动切换当前终端使用的 Python，所以这里用 `uv run` 确保能找到项目和依赖：

```python
from ip_copyright_inspector.schemas import CompareRequest

print(CompareRequest.model_validate(
    {"left_text": " 甲 ", "right_text": "乙"}
).model_dump())
print(CompareRequest.model_json_schema())
```

接着试五种错误输入：缺字段、纯空白、文本过长、`ngram_size=0`、额外字段。捕获 `ValidationError`，打印 `errors()`，找出每种错误对应的字段和提示。

4.2 分别试字段规则、严格类型和跨字段规则

- 增加可选 `request_id`，使用 UUID 类型，看看 OpenAPI 里怎样描述这个字段。
- 将 `ngram_size` 改成严格整数类型（strict integer），验证字符串 `"3"` 是否还能通过。
- 写一个跨字段 `model_validator`，让左右文本完全相同时报错。然后反问一句：接口是否真的应该禁止这种输入？“写得出校验”不代表“业务需要这条规则”。
- 对比 `model_validate()`、`model_validate_json()` 和 `model_construct()`，指出最后一个绕过了什么检查。

完成标志：给你一条规则，你能选出该放进 `Field`、字段验证器还是模型验证器；检查通过的路径都记得返回值。

记住：简单范围写进 `Field`，额外规则写验证器，成功别忘返回值。

4.3 每次只改一个输入，并写下预期错误

先用 `05-backend-engineering.md` 第 3.4 点的完整循环运行七组输入，再把结果遮住，独立回答：

- 不传 `ngram_size`：得到 3，因为字段有默认值。
- 传 `ngram_size=None`：失败，None 不是“没传”，字段也没允许空值。
- 传 `ngram_size="2"`：默认模式下转换成整数 2；同一次调用加 `strict=True` 后失败。
- 传纯空白左文本：先去两端空白，长度变成 0，触发 `min_length`，不必等自定义验证器报错。
- 多传 `ngram_szie`：触发额外字段错误；模型不会猜测你其实想写 `ngram_size`。

下面只验证“普通模式与严格模式”的差别，不修改仓库模型：

```python
# runnable: strict_input_answer
from pydantic import ValidationError
from ip_copyright_inspector.schemas import CompareRequest

payload = {"left_text": "abcd", "right_text": "abce", "ngram_size": "2"}
normal = CompareRequest.model_validate(payload)
print("normal:", normal.ngram_size, type(normal.ngram_size).__name__)
try:
    CompareRequest.model_validate(payload, strict=True)
except ValidationError as error:
    print("strict:", error.errors()[0]["type"])
else:
    raise AssertionError("strict mode should reject this string")
```

预期为 `normal: 2 int` 和 `strict: int_type`。若要完成 UUID 扩展题，先在单独脚本定义一个继承 `CompareRequest` 的新模型，添加 `request_id: UUID | None = None`，记得 `from uuid import UUID`。先证明省略、合法 UUID 和非法字符串三种输入的行为，再考虑改正式接口。

5）看清 FastAPI 收到了什么，又返回了什么

5.1 用两种方式发同一个请求

启动服务后，用 Swagger UI 和 PowerShell 各发送一次请求：

```powershell
$payload = @{
    left_text = "角色使用红色披风和圆形徽章"
    right_text = "红色披风角色佩戴星形徽章"
    ngram_size = 2
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/api/v1/comparisons" `
    -ContentType "application/json" `
    -Body $payload
```

先看状态码、响应字段和固定免责声明，再把 `ngram_size` 改为 9。读一遍 422 响应，找到字段位置，并确认错误详情里没有回显提交的原始输入。

5.2 逐个补充查询、文档和请求限制

- 增加 `GET /api/v1/comparisons/{record_id}`，查不到时返回 404。
- 为路由加入 `summary`、响应示例和明确的错误响应文档。
- 使用 FastAPI 依赖覆盖，让测试使用临时数据库会话，而不是实际开发库。
- 给 `/docs` 是否在生产开放做一个配置开关。
- 让过大的请求体尽早被拒绝，再比较：应用里的字段长度检查和反向代理的请求体大小限制，各自挡住的是什么问题？

完成标志：能解释 400、404、422、500、503 各适合表达什么失败；不会把所有异常都改成“200 加一个错误字符串”。

记住：路由安排处理流程，状态码告诉调用方这次到底成没成。

5.3 不要只看“页面有返回”，把每种分支都核对

以 `05-backend-engineering.md` 第 4.6 点 TestClient 实验为起点，每次只修改 payload 的一项：

| 操作 | 预期状态与结果 | 应该检查的原因 |
| --- | --- | --- |
| `abcd` / `abce`，`n=2` | 201，分数 0.5，新增一条记录 | 模型、算法、事务都走成功路径 |
| 删除 `ngram_size` 字段 | 201，默认 `n=3`，分数约 1/3 | 默认值实际改变了切片长度 |
| `ngram_size=9` | 422，不新增记录 | 模型在计算前拒绝输入 |
| 左文本只包含空白 | 422，不新增记录 | 接口不接受空文本，即使库函数对空值另有规则 |
| 两段文本完全相同 | 201，分数 1.0 | 当前业务规则允许完全相同，不能擅自当成错误 |

数据库失败不要靠删目录、改共享数据库口令来模拟。仓库已有可重复的失败测试，在根目录运行 `uv run pytest tests/test_api.py -k persistence_failure -q`：它分别让 `flush` 和 `commit` 抛异常，检查是否回滚并返回 503。

参考答案提示：400 表示请求存在一般性问题，404 表示目标未找到，422 用在本例的请求校验失败，500 表示服务端未正确处理的内部错误，503 用于本例的保存失败。不是每个状态都已经有一个专门路由，也不是所有项目都必须用同一套错误划分。

6）亲眼看看异步等待和阻塞的区别

6.1 同样等一秒，别的请求还能不能继续

在路由中分别实验 `await asyncio.sleep(1)` 与 `time.sleep(1)`，同时发出多个请求并观察区别。实验结束后恢复代码。

6.2 对照现象，把四个“为什么”讲清楚

- `async def` 为什么不会让 CPU 密集循环自动使用多核？
- 数据库驱动为什么也必须是异步版本？
- 哪些函数只是普通计算，不应该为了外观写成 `async def`？
- 同一个 `AsyncSession` 为什么不能交给多个 `asyncio.gather()` 子任务并发使用？

完成标志：看一段异步代码，能指出哪个调用可能把事件循环堵住；能区分“轮流推进多个任务”的并发、“同时执行”的并行，以及异步等待机制。

记住：异步等待时可以让别的任务继续，CPU 重活不会因为 `async def` 自动变快。

6.3 先在小脚本里看时间线，再改路由

先预测：三个任务各等 0.05 秒，一起交给 `gather()` 后，总耗时接近一份等待，还是三份等待？关键不在函数有没有写 `async`，而在等待时有没有把控制权交回去。

```python
# runnable: waiting_answer
import asyncio
import time


async def wait_async(number):
    await asyncio.sleep(0.05)
    return number


async def wait_blocking(number):
    time.sleep(0.05)
    return number


async def measure(worker):
    started = time.perf_counter()
    result = await asyncio.gather(*(worker(i) for i in range(3)))
    print(worker.__name__, result, round(time.perf_counter() - started, 3))
    assert result == [0, 1, 2]


async def main():
    await measure(wait_async)
    await measure(wait_blocking)


if __name__ == "__main__":
    asyncio.run(main())
```

一般会看到异步版本约 0.05 秒，阻塞版本约 0.15 秒；系统调度会影响数字，所以不把这两个时长写成严格断言。异步版本的三个任务能重叠等待；阻塞版本第一个任务睡觉时，事件循环没法切到第二个任务。

这证明的是“等待能否重叠”，不是 CPU 运算自动并行。核对这点以后，再回到路由检查数据库驱动、HTTP 客户端和 `sleep` 的具体版本，才能定位真正的阻塞点。

7）跟着一条记录，看懂数据库事务

7.1 先确认操作的是可丢弃的本地示例库

先关闭服务，确认目标只是本次练习生成、没有需要保留数据的本地数据库文件。保留副本后移走它，再启动服务，观察表被重新创建。不要操作共享库或生产库，也不要按一个模糊文件名批量删除。

7.2 分清发 SQL、提交、重新查询

- 用 `select(ComparisonRecord)` 查询最近十条记录。
- 为 `created_at` 和 `score` 设计索引，并用查询场景说明理由。
- 把 `flush()` 和 `commit()` 前后的对象状态、`record.id` 打印出来，再单独调用一次 `refresh()`，观察它是“重新查询”而不是“专门生成主键”。本例先 `flush()` 取主键再提交，不把提交后的 `refresh()` 当作接口成功的必经步骤。
- 人为制造违反检查约束的写入，确认异常路径回滚后会话还能继续使用。
- 用临时 SQLite 写一次真实的数据库集成测试：写入后再查询，不只检查内存里的对象。
- 引入 Alembic，生成第一份迁移，再增加一个可空列并生成第二份迁移，看看表结构改动怎样被记录下来。

完成标志：每个请求独立使用会话，并发子任务不共享 `AsyncSession`；事务成功才提交，失败明确回滚；保存的仍是计算信息，不是原文。

记住：`flush` 发 SQL，`commit` 才提交，`refresh` 重新查；会话不并发共享。

7.3 用已有的完整脚本做三次改动

先运行 `05-backend-engineering.md` 第 5.6 点事务实验，确认看到：新对象没 id，flush 后有 id，回滚后查到 0 条，第二次提交后换会话仍能查到分数 0.5。

接着在你自己的实验副本中，一次只做一个改动：

- 把第二次 `commit()` 改成 `rollback()`。预测换会话查询会得到 `None`，原来的“存在”断言会失败；这正好说明 flush 不是提交。
- 把第一段 `flush()` 去掉，在 `add()` 后执行 `await session.execute(select(ComparisonRecord))`。预测 ORM 查询前自动 flush，主键可能已填好；仍然要提交才算这次事务完成。
- 在成功提交后执行 `await session.refresh(record)`。可以给 `create_async_engine` 增加 `echo=True` 看 SQL：刷新会发 SELECT，不是再生成一次主键。日志可能包含 SQL 参数，只用无敏感内容的示例。

查询最近十条的参考写法是在已有会话里使用 `select(ComparisonRecord).order_by(ComparisonRecord.created_at.desc(), ComparisonRecord.id.desc()).limit(10)`，再 `await session.execute(...)`、`result.scalars().all()`。加 id 是为了创建时间相同时有明确的先后顺序。

索引题不要先背答案：按时间排序常查最近记录，就分析时间相关索引；按分数区间筛选才考虑分数索引。索引会增加写入维护成本，不是看到一个字段就加一个。

8）把正常、边界和失败都写进测试

8.1 别让所有测试都依赖整个服务

从当前测试开始，按检查对象分开写：

- 纯函数单元测试：不访问文件、网络或数据库。
- Schema 测试：验证输入输出的字段约定，覆盖正常值、边界值和错误输入。
- 路由测试：验证状态码、响应结构和依赖覆盖。
- 数据库集成测试：使用独立临时库验证事务与映射。

8.2 一次练一种测试工具

- 用 `@pytest.mark.parametrize` 合并重复边界用例。
- 用 `pytest.approx` 比较非精确浮点数。
- 使用 `tmp_path` 为每个测试创建隔离文件。
- 先写一个会失败的测试，再补功能让它通过，最后整理代码并重跑测试。这三步常叫“红、绿、重构”。
- 故意让一个断言失败，阅读 pytest 如何展示差异，然后修复。

完成标志：同一个测试能反复运行；换个顺序也能通过；不使用生产地址，不共享开发数据库。

记住：测试彼此独立，输入覆盖边界，失败原因看得明白。

8.3 先把手算结果写成可重复检查

把下面代码保存成你自己的 `test_compare_example.py`，从仓库根目录运行 `uv run pytest test_compare_example.py -q`。也能直接当脚本执行；它不创建数据库。

```python
# runnable: parametrize_answer
import pytest
from ip_copyright_inspector.similarity import compare_texts


@pytest.mark.parametrize(("size", "expected"), [(1, 0.6), (2, 0.5), (3, 1 / 3), (4, 0.0)])
def test_score_by_ngram_size(size, expected):
    result = compare_texts("abcd", "abce", ngram_size=size)
    assert result.score == pytest.approx(expected)


if __name__ == "__main__":
    for size, expected in [(1, 0.6), (2, 0.5), (3, 1 / 3), (4, 0.0)]:
        test_score_by_ngram_size(size, expected)
    print("four cases passed")
```

先预测会产生几个用例，再运行；pytest 模式下是四个。把 `n=2` 的预期值故意改成 0.8，读清失败信息里 expected 与 obtained 的差异，再恢复 0.5。这个动作让你练的是“用测试发现错误”，不是追求屏幕永远全绿。

下一步再补失败输入，例如 `ngram_size=0` 应抛 `ValueError`。参考结构是 `with pytest.raises(ValueError): compare_texts("abcd", "abce", ngram_size=0)`；不要拿 HTTP 422 去测试纯函数，因为这一层还没有 HTTP。

9）只凭仓库内容，还原一套运行环境

9.1 选一条依赖管理路线

本仓库默认使用 uv，相关命令是：

```powershell
uv lock
uv sync --locked
uv run pytest
uv tree
```

如果另一个项目统一使用 Poetry，则走它的命令：

```powershell
poetry install
poetry run pytest
poetry show --tree
```

一个仓库只选定其中一条路线，以对应锁文件为准，别把两套解析结果混着用。

9.2 分清“允许哪些版本”和“实际装了哪版”

读一遍 `pyproject.toml` 和锁文件，找出下面几项：

- `[project].dependencies` 是应用运行依赖。
- 开发组里的 pytest 只用于开发和测试。
- 版本范围表达兼容边界。
- 锁文件保存解析出的具体版本。
- 构建后端负责把 `src` 里的代码做成可安装的项目包。

完成标志：换一台电脑，只靠仓库就能重建环境；不用复制 `.venv` 或 site-packages，也不把它们提交进去。

记住：范围说可以选谁，锁文件说这次选了谁，虚拟环境不进仓库。

9.3 做一次环境定位，不靠猜包装到哪了

预测：项目依赖装好后，运行系统里的 pytest 为什么仍可能提示找不到包？因为运行程序的 Python 和安装包的 Python 可能不是同一个。

操作：分别查看 `python -c "import sys; print(sys.executable)"` 与 `uv run python -c "import sys; print(sys.executable)"`。路径可以不同；后者应定位到项目环境。再用 `uv tree` 找到 pytest 与运行依赖的位置，对照 `pyproject.toml` 看它们在哪一组。

参考答案：想按已提交的版本清单安装，用 `uv sync --locked`；准备更新依赖解析结果，才有理由修改约束并生成新的锁文件。不要为了“重装试试”每次都随手更新锁文件，那会把环境排错和版本升级混在一起。

10）从“能启动”继续走到“知道怎么部署”

10.1 先看懂启动参数

先用不同参数启动 Uvicorn：

```powershell
uv run uvicorn ip_copyright_inspector.main:app --host 127.0.0.1 --port 8001
uv run uvicorn ip_copyright_inspector.main:app --reload
```

分别解释 `127.0.0.1`、`0.0.0.0`、端口、reload 和 worker 各管什么。确认 reload 只用于开发，不把它带进生产命令，也不和多 worker 混用。

10.2 把代码装进容器，但别忽略容器外的工作

- 写一个多阶段或缓存友好的 Dockerfile。
- 使用固定的 Python 基础镜像版本，避免下一次构建时环境悄悄变化。
- 以非 root 用户启动应用。
- 只复制锁文件和项目必需内容，使用 `.dockerignore` 排除 `.venv`、数据库和缓存。
- 添加 `/health` 健康检查，并区分“进程还活着”和“服务已准备好接请求”，也就是存活检查与就绪检查。
- 通过环境变量注入 `DATABASE_URL`，不要把口令写入镜像层。

完成标志：能说明镜像、容器和进程的区别；也能解释为什么多开几个 worker，并不代表数据库、下游服务和整个系统就不会故障。

记住：镜像是模板，容器是实例，真正执行代码的是进程。

10.3 把启动命令拆成几个能回答的问题

对于 `uv run uvicorn ip_copyright_inspector.main:app --host 127.0.0.1 --port 8001`，逐段核对：uv 选项目环境；uvicorn 启动服务器；冒号左侧找到 Python 模块，右侧取出 `app`；host 决定监听接口；port 决定监听端口。

操作后访问 `http://127.0.0.1:8001/health`，参考响应是 `{"status":"ok"}`。访问 8000 失败不一定是代码坏了，可能只是你这次启动在 8001。先关闭当前服务器再试另一条启动命令，避免把端口占用误认为业务错误。

容器题先做到三项可核对结果：没有把本机 `.venv` 和本地数据库复制进镜像；进程不是 root；没有把数据库口令写入镜像。镜像构建时可以自行创建虚拟环境并安装依赖，不能把它和复制本机环境混为一谈。至于“能否接真实流量”，还得另查端口发布、入口认证、数据库容量和持久化存储，不能靠 `/health` 返回 ok 一项包办。

11）从演示代码走向真实服务，还缺哪些事

11.1 先补出问题时损失最大的部分

不要只盯着“多加几个接口”。按风险优先级安排这些工作：

- 身份认证，以及“这个人能不能操作这条记录”的资源授权。
- 请求大小、并发量和频率限制。
- 超时、取消传播和下游失败策略：请求不再需要结果时，后续任务如何停止；依赖服务失败时，又该怎样返回。
- Alembic 迁移与部署顺序。
- 结构化日志、请求关联 ID、指标和追踪，让一条请求经过了哪里、慢在哪里可以查清楚。
- 敏感内容分级、加密、保留周期和删除流程。
- 用标注数据离线评估阈值，分析误报漏报，并提供人工复核队列。
- 依赖漏洞扫描、最小容器权限和密钥轮换。

11.2 换算法，也要把“为什么信这个分数”补齐

可以继续试 token Jaccard、编辑距离、TF-IDF 余弦相似度或向量模型。但每加一种算法，都要说明：输入怎样整理、算法版本是什么、拿哪些标注数据评估、看什么指标、阈值从哪来，以及旧功能有没有被改坏。

也就是补齐确定的预处理、版本记录、标注数据、指标、阈值来源和回归测试，并保留明确的“这不是法律结论”说明。

11.3 用一条失败故事，把待办变成明确要求

先选“同一请求因网络超时重试”这一种场景，不必一次补所有工程能力。预测：当前服务第一次已经提交、响应却没被客户端收到，第二次重试可能怎样？参考答案是可能新增第二条记录；它没有幂等键，不能自动知道这是同一次业务请求。

把改进要求写具体：由谁生成请求标识、重复标识如何查已有结果、两次并发请求怎样避免都插入、哪些字段需要唯一约束、失败时返回什么。先把这些问题讲清再写代码，比单独加一个 `request_id` 字段更接近真正解决问题。

再做阈值题：准备几组人工确认过的相同、改写、不相关文本，记录每组分数，分别数误报和漏报。参考答案不应是一个凭感觉挑的“神奇阈值”，而是一份说明“在这批样本上，这个阈值会错哪些情况”的记录。

12）最后做一个贯穿整条链路的小改动

12.1 接口接收算法版本，并把版本保存、返回

独立完成这个需求：“比较接口接受可选的算法版本名，并把版本写入记录与响应。”改动虽小，却会经过前面大多数知识点：

- Pydantic 输入与输出字段。
- 纯函数参数及默认行为。
- SQLAlchemy 字段和迁移。
- FastAPI 路由映射。
- 单元测试、Schema 测试和数据库集成测试。
- OpenAPI 示例与兼容性说明。
- 一条只描述技术筛查意义的免责声明。

12.2 合上文件，用自己的话讲一遍

从 JSON 进入开始，依次说明：Pydantic 在哪里校验，纯函数在哪里计算，SQLAlchemy 怎样提交事务，响应模型怎样整理结果，Uvicorn 怎样把 HTTP 响应发出去。每一步都说出负责的文件或对象。

讲到卡住的地方，就回到对应编号再跑一次。不必复述术语；能说清“数据从哪里来、谁处理、失败怎么办、最后去哪里”，这条链路就串起来了。

12.3 综合改动按什么顺序下手

先写预期：不传版本名仍走旧算法；传支持的版本正常返回；传未知版本明确失败；数据库与响应都能看见最终采用的版本。不要先往三个文件里随意加一个同名字段，再想怎么拼起来。

建议在自己的练习副本按以下顺序动手：

- 在输入模型定义支持的版本及默认值，先测省略、合法、未知三种输入。
- 让计算入口明确接收版本或选择对应策略；旧版本的已有分数测试必须保持通过。
- 给数据库增加保存版本的字段与迁移；旧记录填什么默认值也要提前决定。
- 在路由把输入选择的版本传给计算，再把实际使用版本写入记录和响应，不只在最后返回时随手补个字符串。
- 写集成测试：发请求，拿到记录编号，查询临时数据库，逐项比对版本、分数和响应。

参考答案提示：如果目前其实只有一种算法，先限制唯一合法版本，比接受任意版本名却始终运行同一算法更诚实。完成以后，从响应中的版本往回追到数据库、路由、模型，每一处都应该能解释它来自哪里。
