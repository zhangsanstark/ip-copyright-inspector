函数与 Pythonic 进阶

这份笔记承接基础容器，重点说明函数参数、作用域、递归、lambda、高阶函数、闭包、装饰器、上下文管理器和生成器。对 Java 后端开发者而言，可以把它们分别类比为方法调用规则、词法作用域、函数式接口、AOP、`try-with-resources` 和惰性迭代，但 Python 的运行机制与 Java 并不完全相同。

配套代码在 `examples/functions_lab.py`。在仓库根目录执行：

```powershell
python examples/functions_lab.py
```

先用人话建立画面

- 函数像一台小机器：参数是投料口，`return` 是出料口。
- 作用域像找联系人：先找自己房间，再找外层房间，然后找整栋楼，最后查公共通讯录。
- 闭包像带记忆的小机器：外层函数结束后，它还背着当时需要的变量。
- 装饰器像给原机器套一个外壳：不改核心零件，也能在进出时加日志、鉴权或计时。
- 上下文管理器像借钥匙：进入时领钥匙，离开时一定归还，即使中途出错。
- 生成器像按需出餐：叫到一份才做一份，不一次把所有菜摆满桌。

总口诀：参数按规则进，返回结果出；找名字按 LEGB；闭包能记事，装饰器包函数；`with` 管收尾，`yield` 管暂停。

函数是对象

Python 使用 `def` 定义函数。函数也是对象，可以赋给变量、放进容器、作为参数传入，或作为返回值返回。

```python
def greet(name: str) -> str:
    """Return a short greeting."""
    return f"hello, {name}"


alias = greet
print(alias("Ada"))
print(greet.__name__)  # greet
print(greet.__doc__)   # Return a short greeting.
```

这对应“函数是一等公民”。Java 在引入 lambda 和函数式接口后也能传递行为，但 Python 不需要先声明 `Function<T, R>` 一类接口。

函数体在调用时执行。`return` 会立刻结束当前函数；没有显式 `return` 时，默认返回 `None`。

```python
def classify(value: int) -> str:
    if value < 0:
        return "negative"
    if value == 0:
        return "zero"
    return "positive"


def log_only(message: str) -> None:
    print(message)
```

文档字符串

函数体第一条语句若是字符串字面量，它会成为函数的文档字符串，可通过 `help()` 或 `__doc__` 查看：

```python
def divide(total: float, count: int) -> float:
    """Divide total by a positive count.

    Raises:
        ValueError: If count is not positive.
    """
    if count <= 0:
        raise ValueError("count must be positive")
    return total / count
```

普通注释解释“为什么”，文档字符串说明可调用对象“做什么、参数是什么、返回什么、可能抛什么异常”。

返回多个值与拆包

逗号分隔的多个返回值会自动打包成元组：

```python
def min_max(values: list[int]) -> tuple[int, int]:
    return min(values), max(values)


result = min_max([3, 1, 8])
print(result)  # (1, 8)

smallest, largest = result
print(smallest, largest)  # 1 8
```

如果返回值字段较多或容易混淆，生产代码可使用 `dataclasses.dataclass`、`typing.NamedTuple` 或 Pydantic 模型，而不是依赖位置记忆。

参数绑定的核心规则

理解 Python 参数的关键不是背“四种参数”，而是理解调用时如何把实参绑定到形参。

```python
def create_user(name: str, age: int = 18, active: bool = True) -> dict[str, object]:
    return {"name": name, "age": age, "active": active}
```

位置参数按顺序绑定：

```python
create_user("Ada", 30, False)
```

关键字参数按名称绑定，可提升可读性：

```python
create_user("Ada", active=False, age=30)
```

默认参数允许省略。没有默认值的参数必须放在普通默认参数之前，否则定义阶段就会产生 `SyntaxError`。

调用时，普通位置参数必须出现在普通关键字参数之前：

```python
create_user("Ada", age=30)
```

下面这种写法语法错误，文件甚至无法正常解析：

```text
create_user(name="Ada", 30)
```

同一个参数不能重复绑定：

```python
try:
    create_user("Ada", name="Lin")
except TypeError as exc:
    print(exc)
```

不定长位置参数

`*args` 收集额外位置参数，类型是元组。名字 `args` 是约定，不是关键字，但应遵循惯例。

```python
def total(*numbers: float) -> float:
    print(type(numbers))  # <class 'tuple'>
    return sum(numbers)


print(total(1, 2, 3.5))  # 6.5
```

`*` 也能在调用端拆开可迭代对象：

```python
values = [1, 2, 3]
print(total(*values))
```

不定长关键字参数

`**kwargs` 收集额外关键字参数，类型是字典：

```python
def build_profile(name: str, **attributes: object) -> dict[str, object]:
    return {"name": name, **attributes}


profile = build_profile("Ada", city="London", active=True)
print(profile)
```

调用端也可用 `**` 拆开映射，键必须是字符串，并且不能与已绑定参数冲突：

```python
options = {"age": 30, "active": False}
user = create_user("Ada", **options)
```

万能转发参数

包装函数、适配器和装饰器常用 `*args, **kwargs` 完整转发调用：

```python
from collections.abc import Callable
from typing import Any


def traced_call(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    print(f"calling {func.__name__}")
    return func(*args, **kwargs)
```

这是一张“万能接收网”，但业务函数若全部写成 `*args, **kwargs`，会损失接口清晰度和类型检查价值。它更适合透明代理。

仅限位置与仅限关键字参数

Python 还可以精确限制调用方式：

```python
def request(path: str, /, method: str = "GET", *, timeout: float = 3.0) -> str:
    return f"{method} {path}, timeout={timeout}"


print(request("/users", method="POST", timeout=5.0))
```

- `/` 之前的 `path` 只能按位置传入。
- `*` 之后的 `timeout` 只能按关键字传入。
- 中间的 `method` 两种方式都可用。

仅限关键字参数很适合布尔开关、超时、重试次数等，避免 `connect(url, True, False, 3)` 这种难读调用。

参数顺序速记

定义函数时，常见顺序为：

```python
def sample(pos_only, /, normal, default=1, *args, keyword_only, **kwargs):
    ...
```

日常代码不需要同时用齐所有形式。接口越公开，越应选择可读、稳定的参数设计。

参数记忆口诀：普通参数按位置，关键字参数按名字；`*args` 收位置变元组，`**kwargs` 收关键字变字典；星号后的参数只按名字传。

小练习：写一个 `connect(host, port=5432, *, timeout=3.0)`。让 `timeout` 只能按关键字传入，并预测 `connect("db", 5432, 5)` 会发生什么。

参数传递与对象引用

Python 常被描述为“按对象共享传递”或“按赋值传递”。调用时，形参成为指向同一对象的新名字：

```python
def add_item(items: list[str]) -> None:
    items.append("new")


values = ["old"]
add_item(values)
print(values)  # ['old', 'new']
```

函数内重新绑定形参，不会改变调用方变量的绑定：

```python
def replace_items(items: list[str]) -> None:
    items = ["replacement"]
    print(items)


values = ["old"]
replace_items(values)
print(values)  # ['old']
```

对不可变对象，“修改”实际是重新绑定：

```python
def increment(value: int) -> None:
    value += 1


number = 10
increment(number)
print(number)  # 10
```

因此不要机械套用“可变对象按引用传递，不可变对象按值传递”。两者都遵循同一绑定规则，只是对象是否支持原地修改不同。

可变默认参数陷阱

默认参数表达式在函数定义时求值一次，不是每次调用都重新求值：

```python
def append_bad(value: int, bucket: list[int] = []) -> list[int]:
    bucket.append(value)
    return bucket


print(append_bad(1))  # [1]
print(append_bad(2))  # [1, 2]，跨调用累积
```

正确做法是用 `None` 作为哨兵，在函数体内创建新列表：

```python
def append_good(value: int, bucket: list[int] | None = None) -> list[int]:
    if bucket is None:
        bucket = []
    bucket.append(value)
    return bucket
```

不要写 `bucket = bucket or []` 代替精确判断，因为调用方若明确传入空列表，它也会被替换，原列表不会收到修改。

有状态缓存确实可以利用默认对象只创建一次的特性，但这种隐式状态难以维护。明确使用闭包、对象或 `functools.cache` 更好。

默认参数记忆口诀：默认值在定义时只做一次；可变容器用 `None`，进入函数再新建。

类型提示

类型提示改善 IDE 补全、静态检查、代码阅读和框架集成，但 Python 运行时默认不强制：

```python
def repeat(text: str, times: int) -> str:
    return text * times


print(repeat("py", 2))
```

即使写了 `str`，解释器也不会在进入函数前自动验证。若传入不合适类型，可能在函数内部报错，也可能意外成功。

Python 3.9 及以后可直接写内置泛型：

```python
def index_users(users: list[dict[str, object]]) -> dict[int, dict[str, object]]:
    return {int(user["id"]): user for user in users}
```

Python 3.10 及以后用 `|` 表示联合类型：

```python
def normalize_name(name: str | None) -> str:
    return "anonymous" if name is None else name.strip()
```

运行时数据校验需要显式逻辑或 Pydantic 等库，类型提示本身不等于 Java 编译器约束。

作用域与 LEGB

名字查找遵循 LEGB：

- Local：当前函数局部作用域。
- Enclosing：外层嵌套函数作用域。
- Global：当前模块全局作用域。
- Built-in：内置名字，如 `len`、`sum`。

```python
label = "global"


def outer() -> str:
    label = "enclosing"

    def inner() -> str:
        label = "local"
        return label

    return inner()


print(outer())  # local
```

函数内赋值默认创建或重绑定局部变量。若在赋值前读取同名变量，会出现 `UnboundLocalError`：

```python
count = 10


def broken() -> None:
    try:
        print(count)
        count = 11
    except UnboundLocalError as exc:
        print(type(exc).__name__)
```

解释器发现函数体中存在 `count = 11`，就把 `count` 认定为整个函数的局部变量，而不是先读全局再写局部。

global

确实需要在函数内重新绑定模块全局变量时使用 `global`：

```python
request_count = 0


def record_request() -> None:
    global request_count
    request_count += 1
```

`global` 会增加隐藏状态和测试耦合。后端项目中更推荐把状态放进对象、依赖容器、数据库或明确的状态管理结构。

如果只修改全局可变对象内部，而不重新绑定名字，不需要 `global`：

```python
events: list[str] = []


def record_event(event: str) -> None:
    events.append(event)
```

语法上不需要不代表设计上适合；共享可变全局状态仍需谨慎。

nonlocal

嵌套函数需要重新绑定最近一层外部函数变量时使用 `nonlocal`：

```python
def make_counter(start: int = 0):
    count = start

    def increment(step: int = 1) -> int:
        nonlocal count
        count += step
        return count

    return increment


counter = make_counter(10)
print(counter())   # 11
print(counter(5))  # 16
```

`nonlocal` 不能指向模块全局变量。它寻找外层函数中已经存在的绑定。

Python 没有普通块级作用域

`if`、`for`、`while` 不创建新的局部作用域：

```python
if True:
    message = "visible"

print(message)  # visible

for index in range(3):
    pass

print(index)  # 2
```

函数、类体、模块和推导式有各自作用域规则。现代 Python 的推导式循环变量不会泄漏到外部：

```python
value = "outside"
numbers = [value for value in range(3)]
print(value)  # outside
```

不要遮蔽内置名字

```python
len = 10
```

此时调用 `len([1, 2])` 会报 `TypeError`，因为名字 `len` 已经指向整数。

常见危险名字包括 `list`、`dict`、`str`、`id`、`type`、`input`、`sum`、`max`。若在交互环境误遮蔽，可删除变量或重启解释器；源文件中应直接改名。

作用域记忆口诀：L 是自己，E 是外层，G 是模块，B 是内置；改全局用 `global`，改外层函数用 `nonlocal`，能不改共享状态就不改。

小练习：用 `make_balance(initial)` 返回 `deposit(amount)`。每次存钱后返回余额；要求两个余额实例互不影响。

递归

递归函数必须有明确出口，并让每次调用向出口靠近：

```python
def factorial(number: int) -> int:
    if number < 0:
        raise ValueError("number must be non-negative")
    if number <= 1:
        return 1
    return number * factorial(number - 1)


print(factorial(5))  # 120
```

目录树、语法树、组织结构等天然递归数据适合递归。线性计数通常用循环更稳妥，因为 CPython 不做尾递归优化，递归层数过深会抛 `RecursionError`。

递归遍历嵌套结构：

```python
def flatten(values: list[object]) -> list[object]:
    result: list[object] = []
    for value in values:
        if isinstance(value, list):
            result.extend(flatten(value))
        else:
            result.append(value)
    return result


print(flatten([1, [2, [3]], 4]))  # [1, 2, 3, 4]
```

业务数据若可能形成环或深度不可信，还需记录已访问节点、设置深度限制，或改用显式栈。

递归记忆口诀：先写出口，再写缩小问题；每次不靠近出口，就会一直调用到报错。

lambda

`lambda 参数: 表达式` 创建匿名函数，只能包含一个表达式：

```python
add = lambda left, right: left + right
print(add(2, 3))  # 5
```

它可使用默认参数、`*args` 和 `**kwargs`，但复杂逻辑应改为具名 `def`：

```python
always_ten = lambda: 10
power = lambda value, exponent=2: value**exponent
total = lambda *values: sum(values)
pick = lambda **options: options.get("name", "anonymous")
larger = lambda left, right: left if left > right else right

print(larger(10, 20))  # 20
```

lambda 最常见的合理用途是短小的排序键：

```python
orders = [
    {"id": 1, "amount": 100, "created_at": 3},
    {"id": 2, "amount": 200, "created_at": 2},
    {"id": 3, "amount": 200, "created_at": 1},
]

orders.sort(key=lambda order: (-order["amount"], order["created_at"]))
print([order["id"] for order in orders])  # [3, 2, 1]
```

元组键按元素依次比较；数值前加负号可局部实现降序。字符串不能简单加负号，需要分两次稳定排序、使用自定义键，或调整业务模型。

高阶函数

接收函数或返回函数的函数称为高阶函数。

`map()` 对每个元素转换：

```python
numbers = [1, 2, 3]
squares = list(map(lambda number: number * number, numbers))
print(squares)  # [1, 4, 9]
```

`filter()` 保留谓词为真的元素：

```python
even = list(filter(lambda number: number % 2 == 0, range(6)))
print(even)  # [0, 2, 4]
```

`functools.reduce()` 将序列累计为一个值，传入函数必须接收两个参数：

```python
from functools import reduce

product = reduce(lambda left, right: left * right, [1, 2, 3, 4], 1)
print(product)  # 24
```

`map()` 和 `filter()` 在 Python 3 中返回惰性迭代器，查看全部结果时需 `list()`。简单转换和筛选通常用推导式更直观：

```python
squares = [number * number for number in numbers]
even = [number for number in range(6) if number % 2 == 0]
```

求和、最大值、最小值、连接字符串等已有专用函数时，优先使用 `sum()`、`max()`、`min()`、`join()`，不必为了使用函数式风格而强行 `reduce()`。

lambda 记忆口诀：只放一个短表达式，最适合做排序键；一旦需要多步、异常处理或解释业务，就改成普通 `def`。

闭包

当内层函数引用外层函数变量，并在外层返回后继续存活，就形成闭包。可以把它理解为“函数携带一只记忆背包”。

```python
def make_multiplier(factor: int):
    def multiply(value: int) -> int:
        return value * factor

    return multiply


double = make_multiplier(2)
triple = make_multiplier(3)
print(double(10))  # 20
print(triple(10))  # 30
```

每次调用外层函数都会形成独立环境。闭包适合小型状态、函数配置和装饰器。如果状态复杂、方法很多或需要清晰生命周期，类通常更易维护。

晚期绑定，也称幽灵闭包

闭包捕获的是变量绑定，不是创建函数那一刻的值：

```python
bad_functions = [lambda value: value + index for index in range(3)]
print([func(10) for func in bad_functions])  # [12, 12, 12]
```

调用 lambda 时循环已经结束，`index` 的最终值是 2。可用默认参数在函数创建时锁定当前值：

```python
good_functions = [
    lambda value, index=index: value + index
    for index in range(3)
]
print([func(10) for func in good_functions])  # [10, 11, 12]
```

默认参数“只求值一次”在可变默认参数场景是坑，在这里却恰好用于快照。也可以定义工厂函数，表达意图更清楚。

闭包记忆口诀：内层用外层，外层把内层返回；循环里要记住当时的值，就用默认参数锁住。

小练习：生成三个乘法函数，分别乘 `1、2、3`。输入 `10` 时预期输出 `[10, 20, 30]`，并故意去掉 `factor=factor` 看看会变成什么。

装饰器基础

装饰器接收一个可调用对象，并返回一个新的可调用对象。语法：

```python
@decorator
def target():
    ...
```

本质等价于：

```python
def target():
    ...


target = decorator(target)
```

最小可用装饰器：

```python
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar


R = TypeVar("R")


def log_call(func: Callable[..., R]) -> Callable[..., R]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        print(f"start {func.__name__}")
        result = func(*args, **kwargs)
        print(f"end {func.__name__}")
        return result

    return wrapper
```

使用：

```python
@log_call
def add(left: int, right: int) -> int:
    """Add two integers."""
    return left + right


print(add(2, 3))
```

三个细节不能丢：

- `*args, **kwargs` 透明接收并转发不同签名。
- 必须返回原函数的结果，否则业务返回值变成 `None`。
- `@functools.wraps(func)` 保留原函数的 `__name__`、`__doc__` 等元数据，框架路由、日志和调试都可能依赖它们。

装饰器与 Java AOP 都可处理日志、计时、鉴权、重试等横切逻辑，但 Python 装饰器是显式改写函数绑定，不等同于 Spring 动态代理。自调用、代理边界、生命周期等规则不能直接照搬。

带参数装饰器

装饰器自身需要配置时形成三层函数：

- 最外层接收配置。
- 中间层接收被装饰函数。
- 最内层接收实际调用参数并执行。

```python
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar


R = TypeVar("R")


def repeat(times: int):
    if times < 1:
        raise ValueError("times must be positive")

    def decorate(func: Callable[..., R]) -> Callable[..., list[R]]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> list[R]:
            return [func(*args, **kwargs) for _ in range(times)]

        return wrapper

    return decorate
```

这个版本收集每次调用的结果并返回列表，因此装饰前后返回类型发生了变化。若业务只需要最后一次结果，也可以另写版本，但名称、类型提示和说明必须把契约说清楚。

```python
@repeat(times=2)
def announce(message: str) -> str:
    print(message)
    return message.upper()


print(announce("ready"))  # ['READY', 'READY']
```

执行装饰器的时机

装饰器表达式在模块加载、函数定义执行时应用，不是等第一次调用才应用：

```python
def register(func):
    print("registering", func.__name__)
    return func


@register
def handler():
    return "ok"
```

导入模块时就会输出注册信息。Web 框架路由装饰器正是利用这一点建立路由表。

多个装饰器的顺序

```python
@outer
@inner
def target():
    ...
```

等价于 `target = outer(inner(target))`。装饰发生时由下到上，调用进入时通常先经过最外层。鉴权、事务、缓存的顺序可能改变语义，不能随意交换。

装饰器记忆口诀：外层收配置，中层收函数，内层收调用参数；转发参数别丢，返回值别丢，`@wraps` 也别丢。

计时与异常处理

计时装饰器应使用单调时钟 `time.perf_counter()`：

```python
import time
from functools import wraps


def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        started = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - started
            print(f"{func.__name__}: {elapsed:.6f}s")

    return wrapper
```

`finally` 保证原函数抛异常时仍记录耗时。异常装饰器若只是捕获后返回 `None`，会隐藏失败并改变接口契约。通常应记录后重新抛出，或转换成明确领域异常。

上面的同步计时 wrapper 不适合直接装饰 async def，因为调用异步函数只会先得到协程对象，真正执行发生在 await 时。异步函数需要 async wrapper，并在计时区间内写 `await func(...)`。

缓存装饰器

纯函数可用标准库缓存：

```python
from functools import cache


@cache
def fibonacci(number: int) -> int:
    if number < 0:
        raise ValueError("number must be non-negative")
    if number < 2:
        return number
    return fibonacci(number - 1) + fibonacci(number - 2)
```

参数必须可哈希。缓存会保留参数和返回值，长生命周期进程要考虑内存和失效策略；具有副作用、依赖当前时间或外部状态的函数不应随意缓存。

上下文管理器

`with` 确保资源获取与释放成对发生，对标 Java `try-with-resources`：

```python
with open("example.txt", "w", encoding="utf-8") as file:
    file.write("hello")
```

即使代码块抛异常，文件也会关闭。支持 `with` 的对象实现上下文管理协议：

```python
class ManagedResource:
    def __enter__(self):
        print("acquire")
        return self

    def use(self) -> None:
        print("using")

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        print("release")
        return False


with ManagedResource() as resource:
    resource.use()
```

`__enter__()` 的返回值绑定给 `as` 后的变量。`__exit__()` 会收到异常类型、异常对象和回溯；无异常时三者为 `None`。

异常抑制规则

`__exit__()` 返回真值会抑制 `with` 块中的异常：

```python
class IgnoreValueError:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        return exc_type is ValueError


with IgnoreValueError():
    raise ValueError("ignored")
```

返回 `False` 或 `None`，异常继续向外传播。不要无条件返回 `True`，否则包括编程错误在内的异常都会被吞掉。

contextlib.contextmanager

简单管理器可用生成器形式编写：

```python
from contextlib import contextmanager
from collections.abc import Iterator


@contextmanager
def managed_resource() -> Iterator[str]:
    print("acquire")
    try:
        yield "resource"
    finally:
        print("release")


with managed_resource() as resource:
    print(resource)
```

`yield` 前对应进入，`yield` 的值绑定给 `as` 变量，`finally` 中负责清理。`contextlib.closing()`、`suppress()`、`nullcontext()`、`ExitStack()` 也很实用。

使用场景包括：

- 文件、数据库连接、事务、锁的自动释放。
- 临时修改环境或配置后恢复。
- 代码块计时和追踪。
- 测试中创建并清理临时资源。

上下文管理器记忆口诀：进入时申请，退出时归还；`__exit__` 返回真会吞异常，默认返回假更安全。

小练习：写一个上下文管理器，把列表内容临时追加一个值，离开 `with` 后恢复原列表。即使代码块抛异常也必须恢复。

生成器表达式

把列表推导式的方括号换成圆括号，可创建生成器表达式：

```python
squares = (number * number for number in range(1_000_000))
print(next(squares))  # 0
print(next(squares))  # 1
```

它不会一次性创建百万个结果，而是按需计算。列表适合需要重复遍历、下标访问或立即获得全部结果的场景；生成器适合流式处理和大数据集。

生成器是一次性的：

```python
values = (number for number in range(3))
print(list(values))  # [0, 1, 2]
print(list(values))  # []，已经耗尽
```

yield 生成器函数

函数体包含 `yield` 时，调用函数不会立即执行函数体，而是返回生成器对象。每次 `next()` 执行到下一个 `yield`，返回值并冻结局部状态：

```python
def countdown(start: int):
    current = start
    while current > 0:
        yield current
        current -= 1


generator = countdown(3)
print(next(generator))  # 3
print(next(generator))  # 2
print(list(generator))  # [1]
```

生成器结束时抛 `StopIteration`，`for` 循环会自动处理。

流式读取示例：

```python
from collections.abc import Iterator
from pathlib import Path


def non_empty_lines(path: Path) -> Iterator[str]:
    with path.open(encoding="utf-8") as file:
        for line in file:
            cleaned = line.strip()
            if cleaned:
                yield cleaned
```

这里文件在生成器迭代期间保持打开，迭代结束或生成器关闭后才退出 `with`。调用方若创建生成器但长期不消费，要意识到资源生命周期。

yield from

`yield from iterable` 把另一个可迭代对象中的元素逐个转发：

```python
def flatten(values):
    for value in values:
        if isinstance(value, list):
            yield from flatten(value)
        else:
            yield value


print(list(flatten([1, [2, [3]], 4])))
```

与构建完整列表的递归版本相比，此版本可以逐项产出，降低峰值内存。不过“省 90% 内存”不是固定保证，真实收益取决于数据结构、消费方式和是否最终又调用了 `list()`。

生成器记忆口诀：调用先不跑，`next` 才开工；遇到 `yield` 先交一份并暂停，下次接着走；生成器通常只能完整消费一次。

迭代器与生成器的关系

可迭代对象实现 `__iter__()`，可获得迭代器；迭代器还实现 `__next__()` 并保存遍历状态。生成器是创建迭代器的便捷方式。

```python
items = [10, 20]
iterator = iter(items)
print(next(iterator))
print(next(iterator))
```

Java 对照中，`Iterable` 可多次创建 `Iterator`，而 Python 生成器对象通常就是单次迭代器。Java Stream 也不能重复消费，这一点更接近。

惰性链式处理

```python
def parse_numbers(lines):
    for line in lines:
        stripped = line.strip()
        if stripped:
            yield int(stripped)


def only_even(numbers):
    for number in numbers:
        if number % 2 == 0:
            yield number


lines = ["1", " 2 ", "", "4"]
result = sum(only_even(parse_numbers(lines)))
print(result)  # 6
```

每层只关心一个职责，并且数据逐项穿过管道。若中间一步抛异常，可在边界增加包含行号的明确错误信息。

常见错误集中复盘

可变默认参数跨调用累积：

```python
def bad(values=[]):
    values.append(1)
    return values
```

修复：默认值使用 `None`，函数体内创建新容器。

循环闭包全拿最终值：

```python
functions = [lambda: index for index in range(3)]
```

修复：`lambda index=index: index`，或使用工厂函数。

内层直接赋值外层变量：

```python
def outer():
    count = 0

    def inner():
        count += 1
        return count
```

调用 `inner()` 会触发 `UnboundLocalError`。修复：在 `inner()` 开头声明 `nonlocal count`。

遮蔽内置名字：

```python
len = 10
```

修复：改为 `length`、`size` 等具体名字。

装饰器丢失返回值：

```python
def wrapper(*args, **kwargs):
    func(*args, **kwargs)
```

修复：`return func(*args, **kwargs)`。

装饰器丢失元数据：

修复：在包装函数上使用 `@functools.wraps(func)`。

上下文管理器吞掉所有异常：

```python
def __exit__(self, exc_type, exc_value, traceback):
    return True
```

修复：默认返回 `False`；确实要抑制时只匹配预期异常类型。

生成器被消费两次：

修复：需要重复遍历时重新创建生成器，或在数据规模允许时转换为列表并复用。

把异常转成模糊布尔值：

函数用 `raise` 还是返回 `False` 取决于接口契约。验证函数可以返回布尔值；命令执行失败、参数非法等通常应抛出明确异常。反过来，限流器若用异常表达“当前不允许”，上层必须明确捕获；若调用方期望普通分支，返回结构化结果可能更合适。关键是契约一致，不能混用。

综合示例：请求频率限制闭包

以下示例使用闭包保留时间戳，用单调时钟避免系统时间回拨影响：

```python
from collections import deque
from collections.abc import Callable
import time


def make_limiter(limit: int, window_seconds: float) -> Callable[[], bool]:
    if limit <= 0 or window_seconds <= 0:
        raise ValueError("limit and window_seconds must be positive")

    timestamps: deque[float] = deque()

    def allow() -> bool:
        now = time.monotonic()
        boundary = now - window_seconds

        while timestamps and timestamps[0] <= boundary:
            timestamps.popleft()

        if len(timestamps) >= limit:
            return False

        timestamps.append(now)
        return True

    return allow
```

这是单进程、单实例的演示版本，不保证多线程或多进程安全，也不适合分布式限流。生产系统通常把一致状态放到 Redis 等外部系统，并明确时钟、并发和过期策略。

综合示例：可组合的数据管道

```python
from collections.abc import Callable, Iterable, Iterator
from typing import TypeVar


T = TypeVar("T")
U = TypeVar("U")


def transform(values: Iterable[T], mapper: Callable[[T], U]) -> Iterator[U]:
    for value in values:
        yield mapper(value)


def retain(values: Iterable[T], predicate: Callable[[T], bool]) -> Iterator[T]:
    for value in values:
        if predicate(value):
            yield value


numbers = range(10)
even = retain(numbers, lambda number: number % 2 == 0)
squares = transform(even, lambda number: number * number)
print(list(squares))  # [0, 4, 16, 36, 64]
```

这展示了高阶函数、类型提示、lambda 和生成器如何组合。简单场景直接写生成器表达式更短，通用管道抽象只有在重复使用时才值得保留。

练习

练习一：实现安全批量调用

编写 `call_all(func, *argument_groups)`。每个参数组是元组，函数应依次执行 `func(*group)` 并返回结果列表。

示例：

```python
def add(left: int, right: int) -> int:
    return left + right


print(call_all(add, (1, 2), (10, 20)))
```

预期输出：

```text
[3, 30]
```

练习二：修复可变默认参数

以下函数为什么两次调用互相影响？修复后，省略 `tags` 时每次应获得独立列表；显式传入列表时应修改该列表。

```python
def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags
```

修复后的预期输出：

```text
['python']
['java']
```

练习三：闭包计数器

实现 `make_counter(start=0)`，返回的函数每次接收步长并累加。两个计数器实例应互不影响。

预期行为：

```python
first = make_counter(10)
second = make_counter()
print(first())
print(first(5))
print(second())
```

预期输出：

```text
11
16
1
```

练习四：修复幽灵闭包

修复下面的代码，使输出为 `[10, 11, 12]`：

```python
functions = [lambda value: value + index for index in range(3)]
print([func(10) for func in functions])
```

练习五：带参数装饰器

编写 `require_role(role)` 装饰器。被装饰函数第一个参数是包含 `roles` 集合的用户字典。用户缺少角色时抛 `PermissionError`，否则保留原函数返回值和元数据。

预期行为：

```python
@require_role("admin")
def delete_user(operator, user_id):
    return f"deleted {user_id}"
```

管理员调用返回 `deleted 42`，普通用户调用抛 `PermissionError`。

练习六：上下文管理器计时

分别使用类协议和 `@contextmanager` 实现代码块计时。即使代码块抛异常，也必须执行结束逻辑，但不能吞掉异常。

检查点：`__exit__()` 返回 `False`；生成器版本在 `finally` 中清理。

练习七：生成器分页

实现 `batches(values, size)`，逐批产出列表。`size <= 0` 时抛 `ValueError`。

```python
print(list(batches(range(7), 3)))
```

预期输出：

```text
[[0, 1, 2], [3, 4, 5], [6]]
```

自检清单

- 能解释位置、关键字、默认、`*args`、`**kwargs` 的绑定规则。
- 能使用 `/` 和 `*` 设计仅限位置或仅限关键字参数。
- 能解释参数传递为什么既不是简单“传值”，也不是 Java 式笼统“传引用”。
- 能写出 `None` 哨兵修复可变默认参数。
- 能说清 LEGB，并正确选择 `global`、`nonlocal` 或不使用共享状态。
- 能解释 Python 没有普通 `if`、`for` 块级作用域。
- 能写带出口的递归，也知道深递归应改为循环或显式栈。
- 能用 lambda 编写多字段排序键，不把复杂业务塞进 lambda。
- 能比较推导式与 `map`、`filter`、`reduce` 的可读性。
- 能写独立闭包实例，并修复晚期绑定。
- 能手写透明装饰器，保留参数、返回值和元数据。
- 能画出带参数装饰器的三层结构，并判断多个装饰器顺序。
- 能实现类式和生成器式上下文管理器，理解 `__exit__` 返回真值的影响。
- 能解释生成器的惰性、一次性和资源生命周期。
- 能运行 `examples/functions_lab.py` 并通过全部断言。
