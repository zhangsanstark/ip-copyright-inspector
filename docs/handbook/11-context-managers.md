11 with 与上下文管理器：进入时准备，离开时收好

打开文件后要关闭，拿到锁后要释放，临时改配置后要还原。难点不在正常执行，而在中途 return、break 或抛异常时，收尾代码还能不能执行。

with 把这类“进入一段操作与离开一段操作的约定”写在一起。它与 Java try-with-resources 的用途相近，但不限于关闭文件，也可以管理事务、锁与临时状态。

阅读导航：1–3 解释进入退出协议与异常；4 是 contextmanager；5–7 是文件、资源组合与数据库边界；8–9 是异步预览和练习。

```powershell
python scripts/check_handbook_examples.py --chapter 11 --show-output
```

---

1）先从 try / finally 的需求开始

```python
# runnable: hb11_try_finally
from io import StringIO

stream = StringIO("alpha\nbeta\n")
try:
    first = stream.readline()
    assert first == "alpha\n"
finally:
    stream.close()
assert stream.closed
```

StringIO 是内存中的文本流，不会改真实磁盘文件。它有与文件相似的读写方法，适合观察资源状态。

finally 放在这里，是为了即使中间读失败或提前离开，也执行 close。每处都手写这套结构容易漏，于是支持上下文协议的对象可以交给 with。

```python
# runnable: hb11_with_filelike
from io import StringIO

with StringIO("alpha\nbeta\n") as stream:
    assert stream.readline() == "alpha\n"
    assert not stream.closed
assert stream.closed
```

离开代码块后，stream 这个名字仍然存在，但它指向的流已经关闭。with 不会因为代码块结束就删除这个变量，也不代表它可以继续读。

---

2）两个方法分别负责什么

2.1 `__enter__` 的返回值交给 as 后的变量

```python
# runnable: hb11_protocol
events = []

class Session:
    def __enter__(self):
        events.append("进入")
        return {"connected": True}

    def __exit__(self, exc_type, exc_value, traceback):
        events.append(("退出", exc_type, exc_value))
        return False

manager = Session()
with manager as resource:
    assert resource == {"connected": True}
    assert resource is not manager
    events.append("块内操作")

assert events == ["进入", "块内操作", ("退出", None, None)]
```

`as resource` 拿到的不是必然等于 manager，而是 `manager.__enter__()` 的返回值。很多资源对象返回 self，所以两者相同；也有管理器返回另一种更方便使用的对象。

正常离开时，传给 `__exit__` 的三个异常信息都是 None。返回 False 表示如果有异常，不把它压住；正常路径上这个真假值不会凭空制造异常。

2.2 出现异常时，退出方法能看见什么

```python
# runnable: hb11_exception_flow
events = []

class Trace:
    def __enter__(self):
        events.append("进入")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        name = exc_type.__name__ if exc_type is not None else None
        message = str(exc_value) if exc_value is not None else None
        events.append((name, message, traceback is not None))
        return False

try:
    with Trace():
        events.append("准备出错")
        raise ValueError("内容不合法")
        events.append("不会走到")
except ValueError:
    events.append("外面接住")

assert events == ["进入", "准备出错", ("ValueError", "内容不合法", True), "外面接住"]
with Trace():
    pass
assert events[-2:] == ["进入", (None, None, False)]
```

三个参数分别是异常类型、异常实例、回溯对象。流程是块内出错，后续块内语句跳过，先调用退出方法，再根据退出方法的行为决定是否继续向外抛。

可以记成：先收尾，再处理异常去向。退出方法不是让程序从出错那一行继续往下执行。

2.3 进入失败时不会再调用同一个管理器的退出方法

```python
# runnable: hb11_enter_failure
events = []

class CannotEnter:
    def __enter__(self):
        events.append("进入失败")
        raise RuntimeError("资源未准备好")

    def __exit__(self, exc_type, exc_value, traceback):
        events.append("不会自动走到这里")

try:
    with CannotEnter():
        events.append("块内不会执行")
except RuntimeError:
    pass
assert events == ["进入失败"]
```

如果 `__enter__` 已经拿到一部分资源，接着另一项初始化失败，必须在进入方法自己的失败处理里释放已拿到的部分。不能指望外面的 with 自动调用本次失败进入的 `__exit__`。

---

3）返回 True 会抑制异常，要非常具体地决定何时这么做

```python
# runnable: hb11_selective_suppression
class IgnoreMissing:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return exc_type is KeyError

with IgnoreMissing():
    {}["absent"]

reached_after = True
assert reached_after
try:
    with IgnoreMissing():
        int("bad")
except ValueError:
    print("只忽略 KeyError，其他异常仍然抛出")
else:
    raise AssertionError("ValueError 不应被吞掉")
```

第一个块的 KeyError 被抑制后，程序从 with 后面继续。不是从字典查找那行再继续执行块内剩余内容。

这个例子只匹配完全相同的 KeyError 类型。如果要包含子类，需在 exc_type 非 None 时用 `issubclass`。真实业务只忽略明确允许忽略的错误，不能一律 return True。

退出方法自己再抛新异常，也可能让原始异常不再作为最外层错误出现。收尾代码应尽量简单可靠，同时不要静默掩盖清理失败。

---

4）contextmanager：用 yield 把进入和退出隔开

4.1 yield 前准备，yield 的值给 as，后面做收尾

```python
# runnable: hb11_contextmanager
from contextlib import contextmanager

events = []

@contextmanager
def resource(label):
    events.append("准备 " + label)
    try:
        yield {"label": label}
    finally:
        events.append("清理 " + label)

with resource("A") as handle:
    assert handle == {"label": "A"}
    events.append("使用 A")
assert events == ["准备 A", "使用 A", "清理 A"]
```

`@contextmanager` 接收一个生成器函数，把它转换成可供 with 使用的管理器工厂。每次 `resource("A")` 创建新的管理器；进入时执行到 yield，退出时恢复生成器。

与普通生成器“多次 yield 产出多条数据”不同，正常进入要求产出一次；没有 yield 就正常结束会报“没有产出值”的错误，成功进入后退出时也不能再次 yield。准备阶段主动抛异常是合法的获取失败路径，不是说一切零次 yield 的情况都违背协议。

4.2 为什么清理要放 finally

```python
# runnable: hb11_contextmanager_error
from contextlib import contextmanager

events = []

@contextmanager
def managed():
    events.append("进入")
    try:
        yield
    except ValueError:
        events.append("观察到 ValueError")
        raise
    finally:
        events.append("清理")

try:
    with managed():
        raise ValueError("bad")
except ValueError:
    events.append("外层处理")
assert events == ["进入", "观察到 ValueError", "清理", "外层处理"]
```

块内异常会在生成器暂停的 yield 位置重新抛入。因此只写 `yield; cleanup()` 时，异常可能使 cleanup 那行被跳过；放到 finally 才能覆盖这条路径。

如果 except 记录后不重新 raise，就可能把异常抑制。写日志和处理失败不是同一件事：只观察错误通常应继续抛，让调用方决定怎么办。

4.3 同一个生成器式管理器实例通常只能用一次

```python
# runnable: hb11_fresh_managers
from contextlib import contextmanager

events = []

@contextmanager
def scope():
    events.append("进入")
    try:
        yield
    finally:
        events.append("退出")

for _ in range(2):
    with scope():
        pass
assert events == ["进入", "退出", "进入", "退出"]
```

正确做法是每轮调用 `scope()` 新建。不要先 `manager = scope()`，再反复 `with manager`，因为背后同一个生成器已经结束。某些类式管理器可以复用，但必须看它的协议，不是所有 with 对象都一样。

---

5）真实文件：编码、关闭与提前结束

5.1 文本用明确编码，二进制读写用 bytes

```python
# runnable: hb11_file_encoding
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    path = Path(directory) / "sample.txt"
    with path.open("w", encoding="utf-8") as output:
        output.write("第一行\n第二行\n")
    assert output.closed
    with path.open("r", encoding="utf-8") as source:
        lines = [line.rstrip("\n") for line in source]
    assert lines == ["第一行", "第二行"]
    with path.open("rb") as binary:
        content = binary.read()
    assert isinstance(content, bytes)
    assert content.decode("utf-8").splitlines() == lines
```

`w` 会创建文件，若已存在则截断；`a` 是追加；`r` 是读取，文件不存在会失败；`b` 表示二进制模式。示例只在本次新建的临时目录写文件，退出后目录一起清理。

读取未知真实文件前先确认编码与覆盖风险。不能因为 `with` 会关文件，就认为它不会覆盖数据；关闭资源与保护原始内容是两件事。

5.2 生成器持有文件时，用 closing 明确提前关闭

```python
# runnable: hb11_generator_resource
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

events = []

def read_lines(path):
    with path.open(encoding="utf-8") as source:
        try:
            for line in source:
                yield line.strip()
        finally:
            events.append("生成器清理")

with TemporaryDirectory() as directory:
    path = Path(directory) / "sample.txt"
    path.write_text("A\nB\n", encoding="utf-8")
    with closing(read_lines(path)) as lines:
        assert next(lines) == "A"
    assert events == ["生成器清理"]
    assert list(lines) == []
```

closing 在退出时调用对象的 close。生成器开始执行后，close 让其 finally 和内部 with 的收尾执行，于是提前只读一行也有明确关闭点。

如果调用方本来就负责文件，更简单的设计是外层 `with open(...) as source`，再把 source 传给处理生成器。谁拥有资源、谁负责关闭，应该一眼能看出来。

---

6）多个资源：后进入的先退出

```python
# runnable: hb11_nested_order
from contextlib import contextmanager

events = []

@contextmanager
def tagged(name):
    events.append(name + " 进入")
    try:
        yield name
    finally:
        events.append(name + " 退出")

with tagged("A") as a, tagged("B") as b:
    assert (a, b) == ("A", "B")
    events.append("块内")
assert events == ["A 进入", "B 进入", "块内", "B 退出", "A 退出"]
```

相当于 A 包着 B。B 进入时若出错，已经成功进入的 A 仍会退出；尚未成功进入的 B 则要按自己的进入失败逻辑清理。

6.1 数量运行时才知道，用 ExitStack

```python
# runnable: hb11_exitstack
from contextlib import ExitStack
from io import StringIO

with ExitStack() as stack:
    streams = [stack.enter_context(StringIO(text)) for text in ["A", "B", "C"]]
    assert "".join(stream.read() for stream in streams) == "ABC"
    assert all(not stream.closed for stream in streams)
assert all(stream.closed for stream in streams)
```

每次成功进入的资源都登记到 stack。离开时按反向顺序退出，后续资源获取失败时，前面已经登记的也能收好。适合“文件个数来自配置”的情况，不需要手写十层嵌套。

ExitStack 的 callback 还能登记普通清理函数，但函数该接什么参数、清理是否可能失败仍需由你确定，它不会自动理解资源语义。

6.2 suppress：只忽略明知允许的异常

```python
# runnable: hb11_suppress
from contextlib import suppress

mapping = {"a": 1}
with suppress(KeyError):
    del mapping["absent"]
assert mapping == {"a": 1}
```

这个例子约定“删除不存在的键也算完成”。但支付失败、数据库写入失败等通常不应直接忽略。`suppress(Exception)` 范围过大，很容易把程序错误伪装成成功。

---

7）with 的退出语义由对象决定，不一定是 close

7.1 sqlite3 连接上下文管理事务，不自动关闭连接

```python
# runnable: hb11_sqlite_boundary
import sqlite3
from contextlib import closing

with closing(sqlite3.connect(":memory:")) as connection:
    connection.execute("CREATE TABLE item (id INTEGER PRIMARY KEY, name TEXT)")
    with connection:
        connection.execute("INSERT INTO item (name) VALUES (?)", ("A",))
    assert connection.execute("SELECT COUNT(*) FROM item").fetchone()[0] == 1
    try:
        with connection:
            connection.execute("INSERT INTO item (name) VALUES (?)", ("B",))
            raise ValueError("本次操作失败")
    except ValueError:
        pass
    assert connection.execute("SELECT COUNT(*) FROM item").fetchone()[0] == 1

try:
    connection.execute("SELECT 1")
except sqlite3.ProgrammingError:
    print("最外层 closing 已关闭连接")
else:
    raise AssertionError("连接应已关闭")
```

内层 `with connection` 在本例默认事务配置下负责成功提交或异常回滚；退出后仍可使用连接。最外层 closing 才负责 close。

所以看到 with 必须查清这个对象管理什么。SQLAlchemy 的 session、事务对象与 engine 各有不同职责，第 19 章会展开；不能把所有 with 都翻译成“关闭数据库”。

7.2 with 不能保证任何情况下都能收尾

正常 return、break、Python 异常的退出路径可以被协议覆盖。进程被强制终止、机器掉电或某些底层崩溃时，不能保证清理代码执行。

重要数据仍需事务、持久化与恢复设计。with 是语言层面的资源管理工具，不是断电恢复机制。

---

8）选读：异步进入与退出要用 async with

```python
# runnable: hb11_async_context
import asyncio
from contextlib import asynccontextmanager

events = []

@asynccontextmanager
async def async_resource():
    await asyncio.sleep(0)
    events.append("异步进入")
    try:
        yield "ready"
    finally:
        await asyncio.sleep(0)
        events.append("异步退出")

async def main():
    async with async_resource() as value:
        assert value == "ready"
        events.append("使用")

asyncio.run(main())
assert events == ["异步进入", "使用", "异步退出"]
```

同步协议是 `__enter__` / `__exit__`，异步协议是可等待的 `__aenter__` / `__aexit__`。区别在于进入与退出本身可能需要异步 I/O，不是随意给 with 加一个 async 就能让普通对象兼容。

这部分可以在第 16 章之后回看。取消期间的清理也要考虑超时与资源实现，不能把一个 sleep 示例当成所有异步资源都可靠关闭的证明。

---

9）练习与参考实现

9.1 题目一：临时改字典配置，结束后恢复

已有键恢复旧值，原来不存在的键应删除。即使块内抛异常也恢复。本题只修改顶层键，不对整个对象做快照，也不支持并发修改同一字典。

```python
# runnable: hb11_exercise_setting
from contextlib import contextmanager

@contextmanager
def temporary_value(mapping, key, value):
    missing = object()
    previous = mapping.get(key, missing)
    mapping[key] = value
    try:
        yield mapping
    finally:
        if previous is missing:
            mapping.pop(key, None)
        else:
            mapping[key] = previous

settings = {"mode": "normal"}
with temporary_value(settings, "mode", "debug"):
    assert settings["mode"] == "debug"
assert settings == {"mode": "normal"}
try:
    with temporary_value(settings, "new", 1):
        raise ValueError("bad")
except ValueError:
    pass
assert settings == {"mode": "normal"}
```

用独有哨兵区分“原值就是 None”和“原来没有这个键”。退出时恢复的是保存的对象引用，不是深拷贝；如果块内修改这个对象内部结构，需要另行约定是否也恢复。

9.2 题目二：让计时结果在 with 后可读取

创建一个字典作为结果，进入时 `elapsed` 为 None，退出后写入秒数。业务成功或失败都记录。不要对具体耗时写脆弱断言。

```python
# runnable: hb11_exercise_timer
from contextlib import contextmanager
from time import perf_counter

@contextmanager
def timer():
    result = {"elapsed": None}
    started = perf_counter()
    try:
        yield result
    finally:
        result["elapsed"] = perf_counter() - started

with timer() as measurement:
    assert measurement["elapsed"] is None
    total = sum(range(100))
assert total == 4950
assert measurement["elapsed"] >= 0
print(measurement)
```

yield 给调用方的是字典引用。退出时修改同一个字典，调用方在 with 后就能看到更新结果。这里把对象共享用在了有明确约定的地方。

9.3 题目三：后一个资源进入失败，前一个仍退出

用 ExitStack 先登记一个成功资源，再进入一个会抛错的资源。验证前一个被清理，块内业务没有运行，失败资源自己的退出方法没被调用。

```python
# runnable: hb11_exercise_partial_failure
from contextlib import ExitStack, contextmanager

events = []

@contextmanager
def good():
    events.append("good 进入")
    try:
        yield
    finally:
        events.append("good 退出")

class Bad:
    def __enter__(self):
        events.append("bad 失败")
        raise RuntimeError("无法准备")

    def __exit__(self, *exc):
        events.append("bad 不应退出")

try:
    with ExitStack() as stack:
        stack.enter_context(good())
        stack.enter_context(Bad())
        events.append("不应执行的业务")
except RuntimeError:
    pass
assert events == ["good 进入", "bad 失败", "good 退出"]
```

这也是资源管理最值得测的路径之一。只有正常路径通过，不能说明遇到第二个文件打不开、第二个连接失败时就没有泄漏。

---

10）读到 with 时，问清三个约定

进入时获得什么？退出时做什么？遇到哪种异常会继续抛、哪种会被抑制？这三个问题比“with 会自动释放资源”更具体，也更不容易误用。

协议细节见 [with 语句](https://docs.python.org/3.11/reference/compound_stmts.html#the-with-statement)，工具见 [contextlib](https://docs.python.org/3.11/library/contextlib.html)，数据库特例见 [sqlite3 连接上下文管理器](https://docs.python.org/3.11/library/sqlite3.html#how-to-use-the-connection-context-manager)。
