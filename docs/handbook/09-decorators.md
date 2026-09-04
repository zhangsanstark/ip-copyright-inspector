09 装饰器：把一层公共操作包在函数外面

假设十个函数都需要记录耗时。每个函数里都写开始计时、执行、结束计时，业务代码就会重复。装饰器让你单独写好这层操作，再交给指定函数使用。

这和 Java AOP 的用途有交集，但实现过程并不神秘：函数交给另一个函数，后者返回一个新的可调用对象，再把原来的名字指向它。

阅读导航：1–3 从手动包装走到 `@`；4–5 讲带参数和多层顺序；6–8 是计时、缓存、异步边界；9–10 是练习和排错。

```powershell
python scripts/check_handbook_examples.py --chapter 09 --show-output
```

---

1）不用 @，先把过程写出来

```python
# runnable: hb09_manual_wrapper
events = []

def greet(name):
    events.append("业务执行")
    return f"你好，{name}"

def decorate(func):
    def wrapper(*args, **kwargs):
        events.append("调用前")
        result = func(*args, **kwargs)
        events.append("调用后")
        return result
    return wrapper

original = greet
greet = decorate(greet)
assert events == []
assert greet("小周") == "你好，小周"
assert events == ["调用前", "业务执行", "调用后"]
assert greet is not original
```

从 `greet = decorate(greet)` 这一行拆开看：右侧先把原 `greet` 函数交给 `decorate`；`decorate` 返回 `wrapper`；左侧再让名字 `greet` 指向 wrapper。

原函数没有被改写，也没有消失。wrapper 通过闭包中的 `func` 保留着它，所以内部还能调用它。这个结构正好把第 6、7 章接起来。

wrapper 收到的参数原样交给 func，业务返回值再原样交给外面的调用者。这就是一次透明转发的基本要求。

---

2）@ 是把包装动作写在定义上方

```python
# runnable: hb09_at_syntax
from functools import wraps

def add_prefix(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return "结果：" + func(*args, **kwargs)
    return wrapper

@add_prefix
def greeting(name):
    return f"你好，{name}"

assert greeting("周") == "结果：你好，周"
assert greeting.__name__ == "greeting"
```

这段定义完成后的绑定关系相当于 `greeting = add_prefix(greeting)`。读取 `@add_prefix` 时，不要把它想成在函数体里面偷偷插了一句代码，而是把整个函数交给 add_prefix 处理。

这个例子故意要求业务返回字符串，因为包装层做了字符串拼接。并不是所有装饰器都适用于所有函数，包装层也有自己的输入输出约定。

2.1 装饰阶段与调用阶段要分开

```python
# runnable: hb09_timing_of_decoration
events = []

def traced(func):
    events.append("正在装饰 " + func.__name__)

    def wrapper(*args, **kwargs):
        events.append("开始调用")
        return func(*args, **kwargs)

    return wrapper

@traced
def work():
    events.append("业务体")
    return 7

assert events == ["正在装饰 work"]
assert work() == 7
assert work() == 7
assert events == ["正在装饰 work", "开始调用", "业务体", "开始调用", "业务体"]
```

执行到函数定义及其装饰器时，装饰阶段发生一次。每次调用 `work()`，运行的是 wrapper 的函数体。模块被首次导入时，其顶层定义也会执行，因此装饰阶段通常就在导入期间发生。

不要在装饰阶段不加考虑地连接数据库、请求网络或启动长任务。否则只是导入一个文件，也可能产生你没预期的副作用。

---

3）为什么要用 functools.wraps

3.1 名字变了，会影响日志、帮助信息与框架检查

```python
# runnable: hb09_wraps
from functools import wraps
import inspect

def transparent(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@transparent
def add(a: int, b: int = 1) -> int:
    """两个数相加。"""
    return a + b

assert add.__name__ == "add"
assert add.__doc__ == "两个数相加。"
assert str(inspect.signature(add)) == "(a: int, b: int = 1) -> int"
assert add.__wrapped__(2, 3) == 5
assert add(2, b=3) == 5
```

没有 wraps 时，你通常会看到函数名变成 wrapper，原函数说明也丢了。wraps 把常用元信息带过去，并设置 `__wrapped__` 指向被包装函数。`inspect.signature` 默认可沿这条关系展示原签名。

它没有把 wrapper 真正改造成写着 `(a, b)` 的函数体，也不负责校验参数类型，更不会自动帮你补上漏掉的 `return`。元信息保留与业务正确是两回事。

3.2 最常见的两种漏写

如果 `decorate` 最后不返回 wrapper，名字会被绑定为 None，以后调用就报不可调用。

如果 wrapper 调用业务函数后不返回结果，调用者得到 None，业务可能已经执行了但结果丢了。出现“打印有值、外面没值”时先查这一点。

---

4）带参数装饰器为什么经常有三层

4.1 三层各接一种东西

```python
# runnable: hb09_parameterized
from functools import wraps

def surround(left, right):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return left + func(*args, **kwargs) + right
        return wrapper
    return decorate

@surround("[", "]")
def label(name):
    return name.upper()

assert label("api") == "[API]"
```

这里三层分别接收：

| 层 | 本次参数 | 什么时候运行 | 返回什么 |
| --- | --- | --- | --- |
| surround | `"["`、`"]"` 配置 | 求值装饰器表达式时 | decorate 函数 |
| decorate | 原 label 函数 | 包装定义时 | wrapper 函数 |
| wrapper | `"api"` 业务实参 | 真正调用 label 时 | `"[API]"` 业务结果 |

可以脑中展开为先 `configured = surround("[", "]")`，再 `label = configured(label)`，最后才 `label("api")`。

三层不是装饰器的硬性规定，只是“要先接配置、再接函数、最后接业务参数”时很自然的写法。对象实现 `__call__` 也能承担包装工作，第 13 章会讲。

4.2 配置校验适合在最外层做

如果参数是重试次数，负数从定义开始就不合法，没必要等业务调用到一半再发现。最外层确认配置有效，中间层负责包装，最内层执行具体行为，职责就清楚了。

---

5）多个装饰器：构建由内向外，调用由外向内

```python
# runnable: hb09_stacked_order
from functools import wraps

events = []

def layer(name):
    def decorate(func):
        events.append("装饰 " + name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            events.append(name + " 前")
            result = func(*args, **kwargs)
            events.append(name + " 后")
            return result
        return wrapper
    return decorate

@layer("外层")
@layer("内层")
def business():
    events.append("业务")
    return 42

assert events == ["装饰 内层", "装饰 外层"]
events.clear()
assert business() == 42
assert events == ["外层 前", "内层 前", "业务", "内层 后", "外层 后"]
print(" → ".join(events))
```

得到的关系是 `外层(内层(业务))`。调用时先进最外层，然后向里；正常返回时按相反顺序往外。

上面的记录在 decorate 函数内，不在 `layer(...)` 配置表达式里；装饰器表达式本身的求值顺序不要与“应用包装的顺序”混为一谈。

先鉴权再查缓存，与先查缓存再鉴权，可能产生不同的安全结果。装饰器顺序会影响行为，不只是排版喜好。真实鉴权逻辑必须明确每个返回分支是否都经过授权检查。

---

6）计时：成功和异常都要走收尾

```python
# runnable: hb09_timer
from functools import wraps
from time import perf_counter

records = []

def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        started = perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            records.append((func.__name__, perf_counter() - started))
    return wrapper

@timed
def divide(a, b):
    return a / b

assert divide(10, 2) == 5
try:
    divide(10, 0)
except ZeroDivisionError:
    print("异常仍交给调用者")
else:
    raise AssertionError("计时器不该吞异常")
assert len(records) == 2
assert all(name == "divide" and elapsed >= 0 for name, elapsed in records)
```

`try` 中正常返回前，会先执行 finally；抛异常时也执行 finally，然后原异常继续向外传。这里不在 finally 写 return，否则可能覆盖业务返回值，甚至把异常压住。

`perf_counter` 适合计算耗时，不是业务日期时间。不要断言这个小函数必须运行某个固定毫秒数，调度与机器负载会变。

真实记录日志时避免原样打印密码、令牌或完整敏感请求。装饰器可以集中加日志，也可能集中造成泄露；默认只记录必要元信息。

---

7）缓存：省重复计算，也会保存对象与旧结果

```python
# runnable: hb09_cache
from functools import lru_cache

calls = []

@lru_cache(maxsize=2)
def square(value):
    calls.append(value)
    return value * value

assert square(3) == 9
assert square(3) == 9
assert calls == [3]
assert square.cache_info().hits == 1
assert square(4) == 16
assert square(5) == 25
assert square.cache_info().currsize == 2
square.cache_clear()
assert square.cache_info().currsize == 0
```

相同调用参数再次出现时，可以直接取之前结果。`maxsize=2` 限制最多保留两项；空间满了按最近使用情况淘汰。它不是缓存两秒，也不是自动按业务更新失效。

适合缓存的函数通常是相同输入得到相同结果的计算。如果结果依赖当前时间、外部数据库或不断变化的配置，缓存就可能返回过时结果。

7.1 参数要可哈希，结果也不能随意被外部修改

```python
# runnable: hb09_cache_mutability
from functools import lru_cache

@lru_cache(maxsize=8)
def build_list(size):
    return [0] * size

first = build_list(2)
first[0] = 99
assert build_list(2) == [99, 0]

@lru_cache(maxsize=8)
def total(values):
    return sum(values)

assert total((1, 2)) == 3
try:
    total([1, 2])
except TypeError:
    print("列表不能直接用作这个缓存的参数键")
else:
    raise AssertionError("预期不可哈希错误")
```

缓存返回的是同一个结果对象，不是每次自动复制。想避免共享修改，可以返回不可变结构，或在对外边界明确复制。

`lru_cache` 的内部缓存结构有线程安全措施，但并不保证并发下同一计算永远只执行一次；如果两个线程都在首个结果产生前到达，业务函数可能重复执行。不要拿它保证扣款、发消息等副作用只发生一次。

---

8）异步函数要等真正执行完，普通计时包装不够

异步语法会在第 16 章详细讲。这里先看容易提前踩到的一点：调用 `async def` 得到的是协程对象，业务通常要等 await 时才执行。普通同步 wrapper 只调用 func 而不 await，量到的可能只是创建协程对象的时间。

```python
# runnable: hb09_async_wrapper
import asyncio
from functools import wraps

events = []

def traced_async(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        events.append("前")
        try:
            return await func(*args, **kwargs)
        finally:
            events.append("后")
    return wrapper

@traced_async
async def fetch_value():
    await asyncio.sleep(0)
    events.append("业务")
    return 7

assert asyncio.run(fetch_value()) == 7
assert events == ["前", "业务", "后"]
```

这个装饰器明确面向异步函数，不自动兼容所有同步函数、生成器和异步生成器。包装哪种执行模型，就要理解哪种调用过程。

同样，不要直接把普通 `lru_cache` 套到 async 函数上当作异步结果缓存；它会缓存协程对象，协程对象不能像普通结果一样被反复 await。

---

9）练习与完整答案

9.1 题目一：成功调用次数统计

只统计正常返回的次数；业务抛错不计数。装饰后的函数提供 `calls` 属性用于查看。这个例子不处理多线程计数同步。

```python
# runnable: hb09_exercise_count
from functools import wraps

def count_success(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        wrapper.calls += 1
        return result
    wrapper.calls = 0
    return wrapper

@count_success
def divide(a, b):
    return a / b

assert divide(4, 2) == 2
try:
    divide(4, 0)
except ZeroDivisionError:
    pass
assert divide.calls == 1
```

计数写在业务调用之后，所以抛异常时走不到它。若需求改为“统计所有尝试次数”，应把自增放在调用前，或放进合适的 finally。位置决定统计含义。

9.2 题目二：指定异常才重试

配置 `attempts=3` 表示最多尝试三次，不是初次执行后再重试三次。只捕获 `TransientError`；其余错误立刻交给调用者。测试用本地状态模拟失败，不请求网络，也不真正等待。

```python
# runnable: hb09_exercise_retry
from functools import wraps

class TransientError(Exception):
    pass

def retry(attempts):
    if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 1:
        raise ValueError("attempts 必须是正整数")
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except TransientError:
                    if attempt == attempts:
                        raise
        return wrapper
    return decorate

calls = 0

@retry(3)
def unstable():
    global calls
    calls += 1
    if calls < 3:
        raise TransientError("临时失败")
    return "ok"

assert unstable() == "ok"
assert calls == 3

@retry(2)
def always_fails():
    raise TransientError("仍然失败")

try:
    always_fails()
except TransientError as error:
    assert str(error) == "仍然失败"
else:
    raise AssertionError("用完次数仍必须抛异常")
```

捕获块中的裸 `raise` 重新抛出当前异常，保留原因。不要用一个普通 `False` 替代最终失败，除非调用方明确就是按这个返回约定处理。

真实服务还需考虑总超时、间隔退避、取消与幂等性。请求超时不代表对端没完成；盲目重试有副作用的请求可能重复写入或重复扣款。上例只是控制流程，不是完整生产重试策略。

9.3 题目三：只接受非空字符串返回值

装饰器先执行业务，再检查返回值；不是字符串抛 TypeError，去两端空白后为空抛 ValueError。通过后返回清理过的字符串。

```python
# runnable: hb09_exercise_result
from functools import wraps

def nonempty_result(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if not isinstance(result, str):
            raise TypeError("结果必须是字符串")
        cleaned = result.strip()
        if not cleaned:
            raise ValueError("结果不能为空")
        return cleaned
    return wrapper

@nonempty_result
def title(value):
    return value

assert title("  report  ") == "report"
for value, error_type in [("  ", ValueError), (3, TypeError)]:
    try:
        title(value)
    except error_type:
        pass
    else:
        raise AssertionError("错误结果应被拦截")
```

这个装饰器改变了返回值，不是完全透明的代理。命名与说明必须让使用者知道它会清理字符串，否则调用方可能以为收到的是原始数据。

---

10）排错时沿着调用链查

先问名字现在指向哪个对象，再检查包装层有没有返回函数、有没有转发参数、有没有返回业务结果。随后检查异常是否被吞、finally 是否覆盖返回、多层顺序是否符合预期。

装饰器越多，越有必要让每层只做一件清楚的事。理解不了调用过程时，先手动展开成 `f = outer(inner(f))`，再从最外层一步一步往里走。

相关行为可对照 [functools.wraps](https://docs.python.org/3.11/library/functools.html#functools.wraps)、[lru_cache](https://docs.python.org/3.11/library/functools.html#functools.lru_cache) 和 [函数定义与装饰器](https://docs.python.org/3.11/reference/compound_stmts.html#function-definitions)。
