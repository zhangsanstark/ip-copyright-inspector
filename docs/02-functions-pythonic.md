函数与 Pythonic 进阶

容器解决了“数据怎么放”，函数接着解决“这段处理逻辑怎么反复用”。这一篇从调用一个普通函数开始，逐步看清三个问题：参数怎么进去，变量从哪里找，函数还能怎样组合。装饰器、闭包和生成器看着陌生，拆到一次具体调用里，就没那么绕了。

查找顺序：1–4 是函数、参数、对象引用和类型提示；5–8 是作用域、递归、lambda 与闭包；9–11 是装饰器、with 和生成器；12–15 用来排错、串联示例、动手验证和回顾。

想专门弄清高阶函数，可以从 7.1 往下看：7.3 是 map，7.4 是 filter，7.5–7.12 把 reduce 的参数、每轮调用、初始值、边界和实际用途拆开讲。不要一开始就硬读 lambda，先看同一逻辑的普通函数和 for 循环。

配套代码在 `examples/functions_lab.py`。在仓库根目录执行：

```powershell
python examples/functions_lab.py
```

想单独跟踪 map、filter、reduce 每一步的执行，再运行 `python examples/higher_order_lab.py`。脚本会先打印输入和中间结果，最后用断言检查，不需要安装第三方库。

1）函数：能调用，也能当作一个值传来传去

1.1 函数名后面有没有括号，是两回事

用 `def` 定义函数后，写 `greet("Ada")` 才是在调用；只写 `greet`，拿到的是函数本身。因此 `alias = greet` 不会执行问候逻辑，只是让另一个变量也指向这个函数。函数还可以放进容器、传给其他函数，或者作为结果返回。

```python
def greet(name: str) -> str:
    """Return a short greeting."""
    return f"hello, {name}"


alias = greet
print(alias("Ada"))
print(greet.__name__)  # greet
print(greet.__doc__)   # Return a short greeting.
```

“函数是一等公民”说的就是这件事：函数也能像其他值一样赋值和传递。写 Java 时可能会用 `Function<T, R>` 这样的函数式接口；Python 不需要先声明这层接口，就能把行为传出去。

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

1.2 文档字符串：让调用方知道怎么用

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

普通注释适合解释“这里为什么这样写”。文档字符串则写给调用方看：传什么，返回什么，哪些情况下会报错。它不是随便放在哪里的三引号注释，必须位于函数体第一条语句。

1.3 返回多个值：实际返回一个元组

逗号分隔的多个返回值会自动打包成元组：

```python
def min_max(values: list[int]) -> tuple[int, int]:
    return min(values), max(values)


result = min_max([3, 1, 8])
print(result)  # (1, 8)

smallest, largest = result
print(smallest, largest)  # 1 8
```

返回两个值时，拆包很方便；如果一下返回五六个值，调用方就容易记错顺序。那时可以改用 `dataclasses.dataclass`、`typing.NamedTuple` 或 Pydantic 模型，让字段有名字。

2）参数：按顺序传，按名字传，或收集多出来的值

这一组先看普通参数，再看 `*args` / `**kwargs`，最后看 `/` 和 `*` 如何限制调用方式。

2.1 位置参数、关键字参数与默认值

看一次调用时，只要逐个问：“这个值交给哪个参数？”按位置传，就从前往后对应；按名字传，就找到同名参数；没传的参数，看看有没有默认值。

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

`age=18` 的意思是“不传 age 时用 18”，不是不许传别的值。定义普通位置参数时，必填参数要放在带默认值的参数前面，否则会产生 `SyntaxError`。

调用时，普通位置参数必须出现在普通关键字参数之前：

```python
create_user("Ada", age=30)
```

下面先按名字传了 `name`，后面却又跟一个普通位置参数 `30`，这种写法连语法检查都过不了：

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

2.2 *args：把多出来的位置参数收成元组

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

这里的星号要按出现的位置理解：定义中的 `*numbers` 是“收起来”，调用中的 `*values` 是“拆开来”。`total(1, 2, 3)` 和 `total(*[1, 2, 3])` 都会让函数内的 numbers 得到 `(1, 2, 3)`。

如果写成 `total([1, 2, 3])`，没有星号，传进去的是一个列表参数，收起来就成了 `([1, 2, 3],)`，不是 `(1, 2, 3)`。这时 sum 想把数字起点和列表相加，就会报 TypeError。出错的原因不是“函数不接受列表”，而是传入的数据层次与它的计算方式不匹配。

2.3 **kwargs：把多出来的命名参数收成字典

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

这一次 `**options` 展开后，相当于 `create_user("Ada", age=30, active=False)`。它不是按字典的值顺序填位置，而是按键名找到 age 和 active。

同样，`build_profile("Ada", city="London", active=True)` 中，name 先接住 `"Ada"`，剩下两个命名参数才被收进 attributes，得到 `{"city": "London", "active": True}`。已经有参数接住的值，不会再被重复塞进 kwargs。

2.4 同时接收并转发两类参数

包装函数、适配器和装饰器常用 `*args, **kwargs` 完整转发调用：

```python
from collections.abc import Callable
from typing import Any


def traced_call(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    print(f"calling {func.__name__}")
    return func(*args, **kwargs)
```

这里 `traced_call()` 只加一条日志，不需要知道原函数有哪些参数，所以适合原样转发。但普通业务函数别为了省事都写成 `*args, **kwargs`：看调用的人会不知道该传什么，类型检查也更难帮上忙。

结合前面定义的 create_user，调用 `traced_call(create_user, "Ada", age=30)` 时，先看这一层收到了什么：

| 参数 | 收到的值 | 接下来怎么用 |
| --- | --- | --- |
| func | create_user 这个函数对象 | 稍后调用它 |
| args | `("Ada",)` | 展开成一个位置参数 |
| kwargs | `{"age": 30}` | 展开成关键字参数 age=30 |

最后 `func(*args, **kwargs)` 就变成 `create_user("Ada", age=30)`，结果是 `{"name": "Ada", "age": 30, "active": True}`。如果不写两个星号，直接 `func(args, kwargs)`，传过去的就会是“一个元组加一个字典”这两个位置参数，含义已经完全变了。

2.5 / 和 *：明确规定参数该怎么传

有些参数按位置传很自然，有些参数最好把名字写出来。比如 `timeout=5` 比一个孤零零的 `5` 清楚。下面用 `/` 和 `*` 划出这两类参数：

```python
def request(path: str, /, method: str = "GET", *, timeout: float = 3.0) -> str:
    return f"{method} {path}, timeout={timeout}"


print(request("/users", method="POST", timeout=5.0))
```

- `/` 之前的 `path` 只能按位置传入。
- `*` 之后的 `timeout` 只能按关键字传入。
- 中间的 `method` 两种方式都可用。

`/` 和 `*` 只是分隔标记，不是要你在调用时再提供两个值。把几次调用逐项填回参数位置，就能判断是否合法：

| 调用 | path | method | timeout | 结果 |
| --- | --- | --- | --- | --- |
| `request("/users")` | `/users` | 默认 GET | 默认 3.0 | 合法 |
| `request("/users", "POST", timeout=5)` | `/users` | POST | 5 | 合法 |
| `request(path="/users")` | 想按名字传 | 默认 GET | 默认 3.0 | TypeError，path 只能按位置 |
| `request("/users", "POST", 5)` | `/users` | POST | 想按位置传 | TypeError，timeout 必须写名字 |

仅限关键字参数很适合布尔开关、超时、重试次数等，避免 `connect(url, True, False, 3)` 这种难读调用。

2.6 参数顺序放在一起看

定义函数时，常见顺序为：

```python
def sample(pos_only, /, normal, default=1, *args, keyword_only, **kwargs):
    ...
```

这行是为了看全顺序，不是鼓励每个函数都写这么复杂。只用需要的那几种；调用的人一眼知道每个值的含义，比语法用得全更重要。

参数记忆口诀：普通参数按位置，关键字参数按名字；`*args` 收位置变元组，`**kwargs` 收关键字变字典；星号后的参数只按名字传。

小练习：写一个 `connect(host, port=5432, *, timeout=3.0)`。让 `timeout` 只能按关键字传入，并预测 `connect("db", 5432, 5)` 会发生什么。

3）函数改了参数，外面的变量为什么有时变、有时不变

3.1 改同一个对象，调用方也能看见

把 `values` 传进去后，函数里的 `items` 和外面的 `values` 指向同一份列表。`items.append()` 改的是这份列表，所以函数结束后，外面能看到新增的元素。这个规则常被叫作“按对象共享传递”或“按赋值传递”。先记住发生了什么，再记术语就够了。

```python
def add_item(items: list[str]) -> None:
    items.append("new")


values = ["old"]
add_item(values)
print(values)  # ['old', 'new']
```

3.2 给参数重新赋值，只改变函数里的名字

`items = ["replacement"]` 则是另一回事：它让函数里的 `items` 指向新列表，没有改变外面的 `values`。对照下面的输出看这一区别：

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

所以不要分成“列表传引用、整数传值”两套规则。它们都先让参数指向传入的对象；区别只是列表能直接改内容，而整数不能，`value += 1` 会让局部变量指向另一个值。

3.3 默认列表为什么会记住上一次调用

直觉上可能以为 `bucket=[]` 表示“每次没传就新建一个空列表”。实际上，这个列表在定义函数时只建了一次；以后省略 `bucket`，用的都是它。因此第二次调用会接着往第一次的列表里加：

```python
def append_bad(value: int, bucket: list[int] = []) -> list[int]:
    bucket.append(value)
    return bucket


print(append_bad(1))  # [1]
print(append_bad(2))  # [1, 2]，跨调用累积
```

想让每次调用独立，就用 `None` 表示“没有传列表”，进入函数后再新建。这个用于占位和判断的值，也常被叫作“哨兵值”：

```python
def append_good(value: int, bucket: list[int] | None = None) -> list[int]:
    if bucket is None:
        bucket = []
    bucket.append(value)
    return bucket
```

不要写 `bucket = bucket or []` 代替精确判断，因为调用方若明确传入空列表，它也会被替换，原列表不会收到修改。

也有人故意利用默认对象只创建一次来保存缓存，但这种写法不容易看出“状态藏在哪里”。确实需要记住数据时，用闭包、对象或 `functools.cache` 会更清楚。

配套脚本里还有个容易看懵的现象：先把两次结果存到 first_bad、second_bad，最后再一起打印，两个结果都会显示 `[1, 2]`。不是第一次调用已经加了两次，而是两个变量指向同一个列表，第二次追加以后，从第一个变量看也变了。

按时间看：第一次返回时列表是 `[1]`；第二次修改同一列表成为 `[1, 2]`；最后才打印，所以两次打印看到的都是修改后的内容。函数返回列表不会自动帮你保存一份“当时的快照”。

默认参数记忆口诀：默认值在定义时只做一次；可变容器用 `None`，进入函数再新建。

4）类型提示：告诉人和工具预期类型，不自动拦住错误输入

`text: str` 和 `-> str` 是在说明“这里预期接收字符串，也返回字符串”。IDE 补全、静态检查和一些框架会用到这些信息，但解释器默认不会替你执行入口校验：

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

写过 Java 会习惯“类型不对就编译不过”，但这里不能照搬。需要在程序运行时拦截非法数据，就自己写判断，或使用 Pydantic 等校验库。

5）作用域：代码里出现一个名字，Python 去哪里找

5.1 LEGB：先近后远地找

函数里写了 `label`，不一定用模块最上面的那个 `label`。Python 会先找当前函数，再往外找。下面这四步的首字母合起来，就是 LEGB：

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

接下来这个错误更容易困惑：外面明明有 `count = 10`，为什么函数里还说没赋值？因为函数体内出现了 `count = 11`，Python 就把这个名字认作局部变量；前面的 `print(count)` 读到的不是全局变量，而是一个还没赋值的局部变量。

```python
count = 10


def broken() -> None:
    try:
        print(count)
        count = 11
    except UnboundLocalError as exc:
        print(type(exc).__name__)
```

要点是：它不会因为赋值语句写在后面，就先借用全局的 `count`。这个名字在整个函数里都按局部变量处理。

5.2 global：重新赋值的是模块里的变量

确实需要在函数内重新绑定模块全局变量时使用 `global`：

```python
request_count = 0


def record_request() -> None:
    global request_count
    request_count += 1
```

`global` 能用，但一个函数悄悄改变全局变量，其他函数和测试就可能跟着受影响。需要长期保存的状态，通常更适合放进对象、依赖容器或数据库，让谁在修改它更明确。

如果只修改全局可变对象内部，而不重新绑定名字，不需要 `global`：

```python
events: list[str] = []


def record_event(event: str) -> None:
    events.append(event)
```

这里不写 `global` 也能改列表，并不代表共享全局列表就没有风险：多个调用共用它，仍然可能互相影响。

5.3 nonlocal：重新赋值的是外层函数里的变量

计数器要记住上一次的值，内层函数就得更新外层的 `count`。写上 `nonlocal count`，是在说明“用外层已有的那个，不要新建局部变量”：

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

`nonlocal` 不能指向模块全局变量。它从内向外找，使用最近一层外部函数中已经存在的同名变量。如果几层外部函数都有 count，就找离当前函数最近的那一层。

5.4 if / for / while 不会单独隔开变量

`if`、`for`、`while` 不创建新的局部作用域：

```python
if True:
    message = "visible"

print(message)  # visible

for index in range(3):
    pass

print(index)  # 2
```

不过不能由此推出“所有缩进块都一样”。函数、类体、模块和推导式各有自己的作用域规则。比如下面的推导式，内部的循环变量不会覆盖外面的同名变量：

```python
value = "outside"
numbers = [value for value in range(3)]
print(value)  # outside
```

5.5 别把 len、list 这些内置名字拿来当变量名

```python
len = 10
```

此时调用 `len([1, 2])` 会报 `TypeError`，因为名字 `len` 已经指向整数。

常见危险名字包括 `list`、`dict`、`str`、`id`、`type`、`input`、`sum`、`max`。若在交互环境误遮蔽，可删除变量或重启解释器；源文件中应直接改名。

作用域记忆口诀：L 是自己，E 是外层，G 是模块，B 是内置；改全局用 `global`，改外层函数用 `nonlocal`，能不改共享状态就不改。

小练习：用 `make_balance(initial)` 返回 `deposit(amount)`。每次存钱后返回余额；要求两个余额实例互不影响。

6）递归：把同一个问题缩小一点，再交给自己

6.1 先找停止条件

算 `5!`，可以写成 `5 × 4!`；算 `4!`，又可以写成 `4 × 3!`。每次都让数字小一点，直到 `1! = 1` 就不用再拆。这就是递归：函数调用自己，但必须有停止条件，还得保证每次都在靠近它。

```python
def factorial(number: int) -> int:
    if number < 0:
        raise ValueError("number must be non-negative")
    if number <= 1:
        return 1
    return number * factorial(number - 1)


print(factorial(5))  # 120
```

先拿更小的 `factorial(3)` 跟一遍。每一次调用都有自己的 number，不是所有层一起修改同一个 number：

| 阶段 | 当前调用 | 它现在能做什么 |
| --- | --- | --- |
| 往下调用 | `factorial(3)` | 想算 `3 × factorial(2)`，先等下一层结果 |
| 往下调用 | `factorial(2)` | 想算 `2 × factorial(1)`，继续等 |
| 到达出口 | `factorial(1)` | 命中 `number <= 1`，直接返回 1 |
| 往回返回 | 回到 `factorial(2)` | 得到了刚才等待的 1，算出 `2 × 1 = 2` |
| 往回返回 | 回到 `factorial(3)` | 得到了刚才等待的 2，算出 `3 × 2 = 6` |

所以递归要同时看“怎么往下拆”和“结果怎么往回交”。最内层 return 只结束最内层这一次调用，不会让外面的调用全部跳过剩余计算。出口解决停止问题，`number - 1` 解决“下一次离出口更近”的问题。

目录里面还有目录，部门下面还有子部门，这种一层套一层的数据很适合递归。只是从 1 数到很大的数，用循环通常更稳妥：CPython 不会做尾递归优化，调用层数太深会报 `RecursionError`，即使最后一步只是继续调用自己也一样。

6.2 遍历嵌套列表

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

真实数据还可能“绕回来”，比如一个节点间接指回自己。遇到这种情况，要记录已经访问过的节点；数据可能特别深时，可以限制深度，或用自己维护的栈配合循环处理。

递归记忆口诀：先写出口，再写缩小问题；每次不靠近出口，就会一直调用到报错。

7）lambda 与高阶函数：把一小段处理规则传进去

7.1 lambda：只有一个表达式的小函数

只是要临时传一个“两个数相加”的规则，不一定非要单独起一个函数名。`lambda 参数: 表达式` 就能写出这个小函数；表达式的结果就是返回值，不写 `return`。

```python
add = lambda left, right: left + right
print(add(2, 3))  # 5
```

拆开看 `lambda left, right: left + right`：冒号前声明两个参数，冒号后计算要返回的值。调用时传入 2 和 3，于是表达式变成 `2 + 3`，返回 5。它不是“直接保存 5”，而是保存了一段下次还能执行的逻辑。

这和下面的普通函数做的是同一件事。先能读懂 def，再把它缩成 lambda：

```python
def add(left, right):
    return left + right


print(add(2, 3))  # 5
print(add(10, 20))  # 30
```

给高阶函数传参数时，`add` 是函数，`add(2, 3)` 是这次调用得到的数字 5。别人需要“以后怎么处理”的规则，就传 add；别人需要“这次处理完的结果”，才传调用表达式。这是理解 map 和 reduce 的第一步。

它可使用默认参数、`*args` 和 `**kwargs`，但复杂逻辑应改为具名 `def`：

```python
always_ten = lambda: 10
power = lambda value, exponent=2: value**exponent
total = lambda *values: sum(values)
pick = lambda **options: options.get("name", "anonymous")
larger = lambda left, right: left if left > right else right

print(larger(10, 20))  # 20
```

7.2 排序时，用 key 说清比较规则

下面要“金额高的在前；金额一样时，创建时间小的在前”。把这个规则写成一个元组键，就能放进 `sort(key=...)`：

```python
orders = [
    {"id": 1, "amount": 100, "created_at": 3},
    {"id": 2, "amount": 200, "created_at": 2},
    {"id": 3, "amount": 200, "created_at": 1},
]

orders.sort(key=lambda order: (-order["amount"], order["created_at"]))
print([order["id"] for order in orders])  # [3, 2, 1]
```

元组先比第一项，第一项相等才比第二项。金额前加负号后，金额越大，负值越小，就会排在前面；只有金额降序，时间仍是升序。字符串不能这样加负号，要改用分两次的稳定排序、自定义键，或调整数据表示方式。

`key` 收到的是每次一个订单，不是两个订单；它返回“拿来排序的值”，也不是返回 True/False。可以先把上面的 lambda 写开：

```python
def order_key(order):
    return (-order["amount"], order["created_at"])
```

三个订单对应的排序键如下。注意这里没有修改订单金额，只是计算临时用来比较的键：

| 订单 id | 金额 | 创建时间 | 排序键 |
| --- | ---: | ---: | --- |
| 1 | 100 | 3 | `(-100, 3)` |
| 2 | 200 | 2 | `(-200, 2)` |
| 3 | 200 | 1 | `(-200, 1)` |

升序比较时，`-200` 在 `-100` 前面，所以 2、3 先于 1；2 和 3 的第一项一样，再比较时间，1 在 2 前面，所以最终顺序是 3、2、1。若整个元组都相同，稳定排序会保留它们原来的先后次序。

再区分返回值：`orders.sort(key=order_key)` 改原列表，返回 None；`sorted(orders, key=order_key)` 创建排好序的新列表，不改原列表。`key` 每个元素只计算一次，再拿这些键比较，不是在每次两两比较时重新执行一遍。

7.3 map：每次取一个元素，把它换成处理后的值

把“怎么处理”作为参数传给另一个函数，这个接收函数的函数就叫高阶函数；能返回函数的函数也属于这一类。map 负责反复取数据，传进去的函数只负责处理取到的那一项。

先看不用 map 的写法。把 `[1, 2, 3]` 里的每个数平方，保留三项结果：

```python
numbers = [1, 2, 3]
result = []
for number in numbers:
    result.append(number * number)
print(result)  # [1, 4, 9]
```

把“平方”单独写成函数，再把取数据和反复调用的部分交给 map：

```python
def square(number):
    return number * number


numbers = [1, 2, 3]
mapped = map(square, numbers)
print(list(mapped))  # [1, 4, 9]
```

这里有两个参数：`square` 是处理规则，`numbers` 是数据来源。第一次调用 `square(1)` 得到 1，第二次调用 `square(2)` 得到 4，第三次调用 `square(3)` 得到 9。输出元素是函数的返回值，不要求与输入类型相同，比如 `map(str, [1, 2])` 会产生字符串 `"1"`、`"2"`。

现在再看原来的 lambda 写法，就只是把 square 这个小函数写在调用的位置：

```python
numbers = [1, 2, 3]
squares = list(map(lambda number: number * number, numbers))
print(squares)  # [1, 4, 9]
```

map 返回的是迭代器，不是已经算好的列表。创建 map 时先不执行 square；`next()`、`list()` 或 for 真正取结果时才调用。这个“需要时才做”的行为就是惰性计算：

```python
def show_square(number):
    print("正在处理", number)
    return number * number


mapped = map(show_square, [2, 3])
print("刚创建好")
print(next(mapped))
print(list(mapped))
print(list(mapped))
```

预期顺序：

```text
刚创建好
正在处理 2
4
正在处理 3
[9]
[]
```

第一次 list 只收集剩下的 9，不会重新从 2 开始；第二次已经读完，所以得到空列表。要再来一遍，需要重新创建 map，而不是重复读取已经耗尽的对象。

map 也可以同时接收多组数据，这时处理函数会收到每组各取来的一个值：

```python
def add(left, right):
    return left + right


print(list(map(add, [1, 2, 3], [10, 20])))  # [11, 22]
```

实际调用是 `add(1, 10)`、`add(2, 20)`。第二组用完就停止，第一组多出的 3 不参与。本文目标版本是 Python 3.11，先按默认“遇到最短输入结束”来理解。

7.4 filter：判断留不留，留下的仍是原元素

map 问“这一项要变成什么”，filter 问“这一项要不要保留”。例如从 0 到 5 里筛出偶数，可以先写普通循环：

```python
result = []
for number in range(6):
    if number % 2 == 0:
        result.append(number)
print(result)  # [0, 2, 4]
```

交给 filter 时，判断函数每次接收一个元素。返回真值就保留这个原元素，返回假值就丢弃。不是把 True/False 收集进结果：

```python
def is_even(number):
    return number % 2 == 0


print(list(filter(is_even, range(6))))  # [0, 2, 4]
```

从前几次看：`is_even(0)` 是 True，于是留下数字 0；`is_even(1)` 是 False，跳过数字 1；`is_even(2)` 是 True，留下数字 2。完整判断结果是六个布尔值，最终留下的却是三个原数字。

再缩成 lambda，就是原来的写法：

```python
even = list(filter(lambda number: number % 2 == 0, range(6)))
print(even)  # [0, 2, 4]
```

和 map 一样，filter 也是按取用进度执行、用完就耗尽的迭代器。一次 `next(filtered)` 可能判断多个输入，直到找到第一项该保留的元素；因此“取一个输出”不等于“只检查一个输入”。

还有一个常见写法 `filter(None, values)`，意思是直接按元素自身的真假筛选：

```python
values = [0, 1, "", "ok", None, False, [], [2]]
print(list(filter(None, values)))  # [1, 'ok', [2]]
```

它不只是删 None，也会删 0、空字符串等。要保留 0 和 False、只排除 None，应明确写 `filter(lambda value: value is not None, values)`，或用列表推导式。

7.5 reduce：拿上一次的结果，接着处理下一项

假设把 `[1, 2, 3, 4]` 加起来。不是把这四项分别变成四个结果，而是先算 `1 + 2 = 3`，再拿这个 3 加上下一项 3，得到 6，最后拿 6 加 4，得到 10。这种“上次的结果继续参与下次处理”就是 reduce 的核心。

不用 reduce，也可以写得很清楚：

```python
numbers = [1, 2, 3, 4]
accumulator = 0
for current in numbers:
    accumulator = accumulator + current
print(accumulator)  # 10
```

`accumulator` 就是到目前为止的累计结果，常简称 acc；`current` 是这轮新取到的元素。这两个角色不要混：第二轮时，accumulator 已经不是最开始的 0，而是第一轮算完的结果。

reduce 帮你完成“取下一项、调用函数、保存返回值、继续下一轮”这几步，你提供的只是中间那条处理规则：

```python
from functools import reduce


def add(accumulator, current):
    return accumulator + current


print(reduce(add, [1, 2, 3, 4], 0))  # 10
```

reduce 不是内置函数，所以要从 functools 导入。普通写法是 `reduce(处理函数, 数据来源, 可选初始值)`。这三个位置分别在说：

- 处理函数：每轮怎样把“累计结果”和“当前项”合成下一轮的累计结果。这里传 add，不是 `add()`。
- 数据来源：从哪里依次取元素，可以是列表、元组、生成器等可迭代对象。
- 初始值：第一轮开始前，累计结果是什么。写了 0，就从 0 开始处理列表第一项；不写时的规则在 7.7 单独展开。

传入的函数每次会被用两个位置参数调用，所以要能接收两个参数。不是让你给它传整个列表，也不是要求两个参数都来自列表。初始值写在第三个位置，这种写法可用于本仓库的 Python 3.11+ 环境。

7.6 一轮一轮看：return 的值去了哪里

前面的加法例子从 0 开始，实际相当于执行下面四轮：

| 第几轮 | 本轮累计结果 | 本轮当前元素 | 调用 | 返回值，留给下一轮 |
| --- | ---: | ---: | --- | ---: |
| 1 | 0 | 1 | `add(0, 1)` | 1 |
| 2 | 1 | 2 | `add(1, 2)` | 3 |
| 3 | 3 | 3 | `add(3, 3)` | 6 |
| 4 | 6 | 4 | `add(6, 4)` | 10 |

最后已经没有新元素，reduce 就把最后的累计结果 10 返回。它不会默认把 `[1, 3, 6, 10]` 这一串过程返回给你，也不会自动打印中间值。

可以主动加打印，把真正发生的调用看出来：

```python
from functools import reduce


def add_and_show(accumulator, current):
    result = accumulator + current
    print(f"原累计={accumulator}, 当前项={current}, 新累计={result}")
    return result


result = reduce(add_and_show, [1, 2, 3, 4], 0)
print("最终结果:", result)
```

输出如下，正好对应上面四轮：

```text
原累计=0, 当前项=1, 新累计=1
原累计=1, 当前项=2, 新累计=3
原累计=3, 当前项=3, 新累计=6
原累计=6, 当前项=4, 新累计=10
最终结果: 10
```

这时再把 add 缩成 `lambda acc, current: acc + current`，执行过程一点没变，只是写法短了。原来的乘法例子也遵循同一规则：

```python
from functools import reduce

product = reduce(lambda left, right: left * right, [1, 2, 3, 4], 1)
print(product)  # 24
```

这里从 1 开始：`1 × 1 → 1`、`1 × 2 → 2`、`2 × 3 → 6`、`6 × 4 → 24`。若把初始值改成 0，第一轮就是 `0 × 1`，以后一直都是 0；所以初始值不能随便填。

7.7 不写初始值时，为什么少调用一轮

不写初始值，reduce 把数据的第一项直接当作起点，然后从第二项开始调用处理函数：

```python
from functools import reduce


def add(accumulator, current):
    print(accumulator, current)
    return accumulator + current


print(reduce(add, [1, 2, 3, 4]))
```

输出是：

```text
1 2
3 3
6 4
10
```

第一项 1 已经被拿来作为起点，不会再额外执行一次 `add(0, 1)`。对有 n 项的输入：给了初始值就调用 n 次；没给初始值且 n 至少为 1，就调用 n−1 次。

加法从 0 开始与省略初值，在这组数字上刚好都得到 10，但不是“第三个参数写不写都一样”：

```python
from functools import reduce


def add(accumulator, current):
    return accumulator + current


print(reduce(add, [1, 2, 3], 100))  # 106
print(reduce(add, [1, 2, 3]))  # 6
```

前者是 `100 + 1 + 2 + 3`，后者是 `1 + 2 + 3`。初值是参加计算的真实数据，不只是某种配置开关。

7.8 空输入和单元素：还会不会调用处理函数

先看四种情况，再运行验证：

| 调用 | 结果 | 为什么 |
| --- | --- | --- |
| `reduce(add, [], 10)` | 10 | 有起点但没新元素，直接返回起点，不调用 add |
| `reduce(add, [])` | TypeError | 没有起点，输入也拿不出第一项 |
| `reduce(add, [7])` | 7 | 唯一元素直接作起点，后面没有元素，不调用 add |
| `reduce(add, [7], 10)` | 17 | 用 10 作起点，实际调用一次 `add(10, 7)` |

下面是一段完整的验证代码，故意出现的 TypeError 已经接住，不会让脚本中断：

```python
from functools import reduce


def add(accumulator, current):
    print("调用 add:", accumulator, current)
    return accumulator + current


print("空输入有初值:", reduce(add, [], 10))
print("单元素无初值:", reduce(add, [7]))
print("单元素有初值:", reduce(add, [7], 10))
try:
    reduce(add, [])
except TypeError:
    print("空输入无初值: TypeError")
```

输出中的“调用 add”只出现一次：

```text
空输入有初值: 10
单元素无初值: 7
调用 add: 10 7
单元素有初值: 17
空输入无初值: TypeError
```

还有个细节：显式传 None 仍然算“给了初始值”。例如 `reduce(add, [], None)` 返回 None；但对非空数字列表，第一轮可能变成 `None + 1` 并报错。不要把“没传第三个参数”和“第三个参数传 None”混为一谈。

7.9 顺序不能乱：它从左往右接着算

加法容易掩盖顺序，换减法就清楚了：

```python
from functools import reduce


def subtract(accumulator, current):
    return accumulator - current


print(reduce(subtract, [20, 5, 3]))  # 12
print(reduce(subtract, [20, 5, 3], 0))  # -28
```

第一行是 `(20 - 5) - 3 = 12`，不是 `20 - (5 - 3) = 18`。第二行多了初始值 0，变成 `((0 - 20) - 5) - 3 = -28`。它不会自动把输入两两分组后并行计算。

Java Stream 的 reduce 还需要考虑流是否并行、合并规则是否满足要求。这里先按 Python reduce 的顺序累计来理解，别把 Java 并行流的行为直接套过来。

7.10 业务例子：累计金额和当前订单可以是不同类型

前面两个参数都是数字，容易误以为它们必须同类型。实际上，累计结果可以是金额，当前元素可以是一条订单字典：

```python
from functools import reduce


def add_order(total, order):
    subtotal = order["price"] * order["quantity"]
    result = total + subtotal
    print(f"原合计={total}, 本条={subtotal}, 新合计={result}")
    return result


orders = [
    {"price": 10, "quantity": 2},
    {"price": 3, "quantity": 4},
]
print("订单合计:", reduce(add_order, orders, 0))
```

输出：

```text
原合计=0, 本条=20, 新合计=20
原合计=20, 本条=12, 新合计=32
订单合计: 32
```

第一轮 total 是初始值 0，order 是第一条字典，算出 20；第二轮 total 是上轮返回的 20，order 换成第二条字典，算出 32。reduce 最终返回的是一个对象，不一定是数字，也可以是字符串、列表或字典；关键是返回值能继续作为下一轮的第一个参数使用。

这个例子不能随手省略初始值。省略后，第一条订单字典会被当作 total，函数里的“字典加金额”就不成立了。生产金额还要按业务使用最小货币单位整数或 Decimal；这里用小整数只为看清流程。

7.11 reduce 的错误通常出在哪里

第一种：把函数调用结果传进去。`reduce(add(1, 2), [3, 4])` 会先算出 3，再把 3 放在“处理函数”的位置；真正要调用处理函数时，数字 3 不能调用，于是报 TypeError。应传 add，让 reduce 决定每轮的参数。

第二种：函数只接收一个参数。reduce 每轮会传入两个，普通 `def square(number)` 接不住。map 的单项转换规则和 reduce 的累计规则不能直接互换。

第三种：只打印，忘了 return。下面这段第一次打印看似正确，但函数返回的是 None；第二轮就变成 `None + 3`：

```python
from functools import reduce


def wrong_add(accumulator, current):
    print(accumulator + current)
    # 故意漏掉 return，Python 默认返回 None


try:
    reduce(wrong_add, [1, 2, 3])
except TypeError:
    print("第二轮收到 None，无法继续相加")
```

先输出 3，再输出错误提示。修复是在函数末尾写 `return accumulator + current`，不是再加一个 print。

第四种：把它当成惰性迭代器。map、filter 创建后等你取结果；reduce 调用后就会消费输入并进行累计，正常结束才返回最终结果。把没有结束的无限迭代器交给 reduce，就不会正常得到“最终结果”，除非中途发生异常或被外部中止。

如果过程函数抛异常，reduce 不会自动跳过坏元素，也不会替你撤回前面发生的文件写入、列表修改等副作用。先把过程函数写得简单、尽量只计算和返回，排错会轻松很多。

7.12 三者放在一起看，什么时候不用 reduce

| 工具 | 每次交给处理函数什么 | 函数返回什么 | 最后拿到什么 |
| --- | --- | --- | --- |
| `map(func, values)` | 当前元素 | 转换后的值 | 按需产出新值的迭代器 |
| `filter(func, values)` | 当前元素 | 用于判断的真值或假值 | 按需产出被保留原元素的迭代器 |
| `reduce(func, values, start)` | 当前累计结果、当前元素 | 下一轮累计结果 | 完成累计后的最终对象 |

记住关系，比记中文译名更有用：map 每项各做各的，filter 决定谁留下，reduce 则把上轮结果带入下一轮。

简单转换和筛选通常用推导式更直观：

```python
squares = [number * number for number in numbers]
even = [number for number in range(6) if number % 2 == 0]
```

求和直接写 `sum(numbers)`，相乘可以写 `math.prod(numbers)`，最大最小值用 `max()`、`min()`，连接字符串用 `join()`。这些函数已经把意图写进名字，不必全部改成 reduce。上面的订单合计也可以直接写 `sum(order["price"] * order["quantity"] for order in orders)`。

如果想看到每一步累计结果，可以考虑 `itertools.accumulate()`：

```python
from itertools import accumulate


print(list(accumulate([1, 2, 3, 4])))  # [1, 3, 6, 10]
```

accumulate 返回逐步产出累计结果的迭代器，reduce 返回最后结果。需要复杂分支或同时维护几个变量时，普通 for 循环通常更容易读、也更容易打断点。会用 reduce，不等于每次累计都应该用它。

这些 API 的边界按 [Python 3.11 functools.reduce](https://docs.python.org/3.11/library/functools.html#functools.reduce)、[内置 map / filter](https://docs.python.org/3.11/library/functions.html#map) 和 [排序指南](https://docs.python.org/3.11/howto/sorting.html) 核对；上面的输入、过程表和输出可用仓库的 higher_order_lab.py 对照验证。

7.13 先自己算，再看答案

下面假设 add 是两数相加，multiply 是两数相乘，subtract 是前一个数减后一个数。每题先写出每轮的两个参数，不要只猜最后答案：

- `reduce(add, [2, 4, 6], 10)` 的结果和调用次数？
- `reduce(multiply, [2, 3, 4], 1)` 的结果？把初值改成 0 呢？
- `reduce(subtract, [10, 3, 2])` 相当于怎样加括号？
- `reduce(add, [9])` 会不会调用 add？
- 要保留 `[0, None, 2]` 中的 0，能不能直接用 `filter(None, ...)`？

核对答案：第一题 22，共 3 次，依次是 `(10, 2)`、`(12, 4)`、`(16, 6)`；第二题分别是 24 和 0；第三题 `(10 - 3) - 2 = 5`；第四题直接返回 9，不调用 add；第五题不能，应该明确判断 `value is not None`，结果为 `[0, 2]`。

动手验证：运行 `python examples/higher_order_lab.py`，再把脚本中的一组输入改掉。先改初值，再改输入顺序，最后改为空列表；每次都先预测结果或异常，再运行核对。

lambda 记忆口诀：只放一个短表达式，最适合做排序键；一旦需要多步、异常处理或解释业务，就改成普通 `def`。

8）闭包：外层函数结束了，返回的函数还能用它的变量

8.1 先固定倍数，再处理不同的数字

想做两个函数，一个永远乘 2，一个永远乘 3，不用把相同逻辑写两遍。下面先调用 `make_multiplier(2)` 固定倍数，它返回的 `multiply` 之后还能用到这个 `factor`。这种内层函数保留外层变量的方式，就是闭包。

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

`double` 和 `triple` 分别来自两次调用，各自保留自己的 `factor`，不会串在一起。闭包适合保存少量状态、固定函数配置，也常用于装饰器；如果要保存很多字段、提供很多方法，用类通常更容易看清楚。

这里有两次不同的调用，不要揉成一步：

1. `make_multiplier(2)` 执行外层函数，建立 factor=2，并返回内层 multiply 函数。此时没有计算任何 value。
2. `double = ...` 接住这个返回的函数，因此 double 现在是可调用对象，不是数字 2。
3. `double(10)` 才执行内层 multiply：value 来自本次调用，是 10；factor 来自创建它的那次外层调用，是 2。
4. 内层算出 `10 × 2 = 20` 并返回。随后 `double(7)` 仍可使用同一个 factor，得到 14。

“函数能记住变量”只是便于理解的说法，它保留的是对外层变量的访问，不一定是创建时复制的一份值。这正是下一小点的循环问题会发生的原因。

8.2 循环里建函数：为什么最后都用了同一个数

下面看起来造了三个函数，应该分别加 `0、1、2`，结果却全都加了 `2`。原因是函数创建时没有把当时的 `index` 拍下来保存；等真正调用时，才去取这个变量的值。这叫晚期绑定，也常被称作“幽灵闭包”。

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

`index=index` 左边是参数名，右边是当前循环值。右边在每个函数创建时就会求值，所以这次分别记住了 `0、1、2`。同样的“默认值只算一次”，前面可能导致列表累积，这里却正好拿来保存当时的值。也可以用工厂函数显式创建这三个函数。

如果两个 index 看着难分，可以把左边换个参数名，写成 `lambda value, saved=index: value + saved`：saved 是这个小函数自己的参数，右边的 index 才是当前循环变量。三次创建分别相当于 saved 默认是 0、1、2；之后调用只传 value，便使用各自默认的 saved。

这也不是深拷贝。若默认值存的是列表，后来修改了同一个列表，函数仍能看到变化；当前例子存的是整数，所以容易直观看成“固定当时的数字”。

闭包记忆要点：返回的函数还能用外层变量；它通常不是保存一份当时的值。循环里确实要记住当时的值，可以用默认参数固定下来。

小练习：生成三个乘法函数，分别乘 `1、2、3`。输入 `10` 时预期输出 `[10, 20, 30]`，并故意去掉 `factor=factor` 看看会变成什么。

9）装饰器：不改业务函数，也能在调用前后加步骤

这一组先看无参数装饰器，再加配置，接着看执行时机和嵌套顺序，最后写计时与缓存。

9.1 把函数交给另一层包装

假设每个接口调用前后都要打日志，总不能把同样的日志代码复制到所有函数里。可以把原函数交给一个包装函数，让它负责“先打印、再调用原函数、最后返回结果”。这种用法就是装饰器：接收函数，再返回包装后的函数。写法如下：

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

下面的 `log_call` 先接住 `func`，返回 `wrapper`。以后调用被装饰的函数，其实会先进入 `wrapper`：

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

- `*args, **kwargs` 把位置参数和关键字参数都接住，再原样交给原函数。
- 必须返回原函数的结果，否则业务返回值变成 `None`。
- `@functools.wraps(func)` 保留原函数的 `__name__`、`__doc__` 等元数据，框架路由、日志和调试都可能依赖它们。

这些用途很像 Java AOP：把日志、计时、鉴权、重试等重复步骤集中处理。但实现机制不同：这里是把函数名重新指向装饰器的返回值，不是直接套用 Spring 动态代理。因此自调用、代理边界和生命周期等规则，不能照搬 Spring 的结论。

9.2 带参数装饰器：多一层来接收配置

如果还想指定“重复执行几次”，就要在外面再加一层接收 `times`。按调用顺序看三层，各有一件事：

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

这个版本执行几次，就收集几个结果，所以原函数返回字符串，装饰后返回的是字符串列表。也可以设计成只返回最后一次结果，但要把这个行为写清楚，让调用方知道拿到的是什么。

```python
@repeat(times=2)
def announce(message: str) -> str:
    print(message)
    return message.upper()


print(announce("ready"))  # ['READY', 'READY']
```

把三层拆成“定义时”和“调用时”，就不用死记有几个 return：

| 时机 | 发生的调用 | 收到什么 | 返回什么 |
| --- | --- | --- | --- |
| 定义时第 1 步 | `repeat(times=2)` | 重复次数 2 | decorate 函数 |
| 定义时第 2 步 | `decorate(原 announce)` | 原函数对象 | wrapper 函数 |
| 定义时第 3 步 | 重新绑定 announce | wrapper | 以后 announce 这个名字指向 wrapper |
| 真正调用时 | `announce("ready")`，实际进入 wrapper | `args=("ready",)`、`kwargs={}` | 两次原函数的返回值组成列表 |

wrapper 用得到 times 和 func，是因为它们由外层保留着，这里正好用到了闭包。两次调用原 announce，每次先打印 ready，再返回 READY；因此整个例子的完整输出是：

```text
ready
ready
['READY', 'READY']
```

“返回 decorate”表示把下一层函数交出去，不是现在就调用它；“返回 wrapper”也一样。真正的业务参数要等调用 announce 时才到达最里层。

9.3 装饰器什么时候执行

要区分“给函数加包装”和“执行包装后的函数”。下面的 `register` 在 Python 执行到函数定义时就运行了，不会等到第一次调用 `handler()`：

```python
def register(func):
    print("registering", func.__name__)
    return func


@register
def handler():
    return "ok"
```

导入模块时就会输出注册信息。Web 框架路由装饰器正是利用这一点建立路由表。

9.4 多个装饰器：先包里面，再包外面

```python
@outer
@inner
def target():
    ...
```

等价于 `target = outer(inner(target))`。先把 `target` 交给 `inner`，再把结果交给 `outer`；真正调用时，通常先进入最外层的 `outer`。顺序会影响结果，例如先鉴权再查缓存，和先返回缓存结果再鉴权，不是一回事。

配套 functions_lab.py 的 `demo_decorator_order()` 记录了完整来回顺序：`enter outer → enter inner → target → exit inner → exit outer`。建立包装是从里面开始，调用进入是从外面开始，返回收尾再从里面退出来。这三个时机分清了，就不会只凭 @ 的上下位置猜运行顺序。

装饰器记忆口诀：外层收配置，中层收函数，内层收调用参数；转发参数别丢，返回值别丢，`@wraps` 也别丢。

9.5 计时：报错时也要记下耗时

计时需要的是“过去了多久”，不是当前几点几分。`time.perf_counter()` 适合量这段耗时，也不会因为系统时间被调回去就得到负时长：

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

耗时输出放在 `finally` 中，因此原函数成功或报错都会记录。别顺手把所有异常都捕获后返回 `None`，那会让调用方分不清“正常没结果”和“执行失败”。通常应记录后继续抛出，或转换成调用方认识的业务异常。

上面的同步计时 wrapper 不适合直接装饰 async def，因为调用异步函数只会先得到协程对象，真正执行发生在 await 时。异步函数需要 async wrapper，并在计时区间内写 `await func(...)`。

9.6 缓存：相同输入的重复计算可以省下来

如果一个函数的结果只取决于输入，并且没有额外副作用，相同输入反复计算就有些浪费。这类函数常叫纯函数，可以用标准库缓存结果：

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

缓存需要用参数查找旧结果，所以参数必须可哈希。它也会保留参数和返回值，服务一直运行时，要考虑占多少内存、旧结果什么时候失效。像“查询当前时间”或“发一封邮件”，不能因为参数一样就随意跳过执行。

10）with：进入一段操作，离开时把资源收好

10.1 `__enter__` 和 `__exit__` 各负责什么

打开文件后要关闭，拿到锁后要释放。每次手写 `try/finally` 容易漏，`with` 可以把这类收尾规则交给对象处理，用途接近 Java 的 `try-with-resources`：

```python
with open("example.txt", "w", encoding="utf-8") as file:
    file.write("hello")
```

正常进入代码块后，即使写文件时抛异常，也会执行关闭操作。自己写支持 `with` 的对象时，需要提供 `__enter__()` 和 `__exit__()` 两个方法，这组约定就叫上下文管理协议：

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

`as resource` 接到的是 `__enter__()` 的返回值，不一定是原对象。离开时，`__exit__()` 会收到异常类型、异常对象和回溯；没有异常时，这三个值都是 `None`。注意：如果 `__enter__()` 自己就失败，还没有成功进入代码块，Python 不会再调用这个对象的 `__exit__()`。

上面的例子依次输出 acquire、using、release，对应三个时刻：

1. 创建 ManagedResource 对象，调用它的 `__enter__()`，输出 acquire。
2. 把 enter 返回的 self 交给 resource，进入代码块，`resource.use()` 输出 using。
3. 代码块正常结束，调用 `__exit__(None, None, None)`，输出 release。

如果第二步抛了 ValueError，第三步仍执行，但收到的就不再是三个 None，而是异常类型、异常对象和回溯信息。当前实现返回 False，所以清理后异常继续向外抛，with 后面的正常语句不会直接接着运行；需要外层 except 接住后才能继续。

10.2 `__exit__` 返回 True，异常就不再向外抛

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

可把 `__exit__` 的返回值理解成回答“这次异常是否已经由我处理”：真值表示不用再抛，假值表示仍要交给外层。没有异常时，这个返回值不会凭空制造异常。成功进入后才谈退出规则；如果进程被强制终止，也不能指望清理代码还有机会执行。

10.3 用 contextmanager 写一个简短版本

只是做一点进入准备和退出清理，不想专门写一个类，可以用 `@contextmanager`。下面的 `yield` 把“进入”和“离开”分开，生成器的执行过程会在下一组细讲：

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

先执行 `yield` 前的准备，把 `yield` 后面的值交给 `as` 变量；等 `with` 代码块结束，再回来执行清理。这个例子把清理写进 `finally`，所以代码块报错时也会收尾。`contextlib` 里还有 `closing()`、`suppress()`、`nullcontext()`、`ExitStack()`，遇到更具体的资源管理需求时可以查它们。

使用场景包括：

- 文件、数据库连接、事务、锁的自动释放。
- 临时修改环境或配置后恢复。
- 代码块计时和追踪。
- 测试中创建并清理临时资源。

上下文管理器记忆口诀：进入时申请，退出时归还；`__exit__` 返回真会吞异常，默认返回假更安全。

小练习：写一个上下文管理器，把列表内容临时追加一个值，离开 `with` 后恢复原列表。即使代码块抛异常也必须恢复。

11）生成器：需要一个算一个，不急着把结果全放进内存

11.1 生成器表达式：把方括号换成圆括号

把列表推导式的方括号换成圆括号，可创建生成器表达式：

```python
squares = (number * number for number in range(1_000_000))
print(next(squares))  # 0
print(next(squares))  # 1
```

这里没有提前算出一百万个平方数；第一次 `next()` 才取第一个，第二次再取第二个。这就是按需计算。需要反复遍历、按下标访问或立即拿到全部结果时，用列表方便；只想边读边处理时，生成器更合适。

生成器是一次性的：

```python
values = (number for number in range(3))
print(list(values))  # [0, 1, 2]
print(list(values))  # []，已经耗尽
```

11.2 yield：交出一个结果，暂停在这里

普通函数遇到 `return` 就结束；生成器遇到 `yield` 则先交出一个值，记住当前走到哪、局部变量是什么，然后暂停。下一次 `next()` 再从暂停处往后继续。函数体里有 `yield`，调用它时先得到生成器对象，不会立即执行函数体：

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

把每次取值时的位置写出来：

| 外面的操作 | 函数里面执行到哪里 | 交出的结果 |
| --- | --- | --- |
| `countdown(3)` | 只创建生成器，函数体还没开始 | 一个生成器对象 |
| 第一次 `next(generator)` | 设置 current=3，条件成立，停在 yield | 3 |
| 第二次 `next(generator)` | 从上次 yield 后继续，先减成 2，再进入下一轮 yield | 2 |
| `list(generator)` | 继续减成 1 并产出；再减成 0，循环结束 | 收到剩余的 `[1]` |

第二次不会重新执行 `current = start`，否则每次就都返回 3 了。暂停时保存了当前执行位置和局部变量，恢复时才接着做 `current -= 1`。`for`、list 和 sum 都会替你反复取下一项，并处理正常结束，不需要你手动写一串 next。

生成器结束时抛 `StopIteration`，`for` 循环会自动处理。

11.3 逐行读取时，文件什么时候关闭

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

调用 `non_empty_lines()` 只得到生成器，开始迭代后才会打开文件。文件在迭代期间一直开着，直到迭代结束或生成器关闭才退出 `with`。如果读了几行就把生成器长期搁着，文件也可能一直没关；使用时要把“何时不再需要它”想清楚。

11.4 yield from：把另一段结果逐个交出去

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

前面的递归版本先攒好一个完整列表，这个版本可以找到一项就交出一项，因而有机会减少同时留在内存里的数据。但不是固定“省 90%”：如果最后仍然 `list(...)` 把全部结果收齐，结果列表该占的内存还是要占。

生成器记忆口诀：调用先不跑，`next` 才开工；遇到 `yield` 先交一份并暂停，下次接着走；生成器通常只能完整消费一次。

11.5 可迭代对象、迭代器、生成器，怎么区分

列表能被 `for` 遍历，是可迭代对象。调用 `iter(items)`，会得到一个负责记住“读到哪里了”的迭代器；调用 `next()`，就读下一项。对应的方法是：可迭代对象提供 `__iter__()`，迭代器还提供 `__next__()`。生成器也是迭代器，只是用 `yield` 写它更省事。

```python
items = [10, 20]
iterator = iter(items)
print(next(iterator))
print(next(iterator))
```

Java 对照中，`Iterable` 可多次创建 `Iterator`，而 Python 生成器对象通常就是单次迭代器。Java Stream 也不能重复消费，这一点更接近。

11.6 把几步处理接起来，仍然逐项执行

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

这里先逐行解析数字，再只保留偶数，最后求和。每一步只负责一件事，不需要中途存下完整列表。如果某行转整数失败，可以在解析入口补上行号，让报错说明“哪一行有问题”。

它不是“先把所有字符串转完，再把所有偶数挑完”。真正推动流程的是最外层 sum 想要下一个数字：

1. sum 向 only_even 要一项；only_even 又向 parse_numbers 要一项。
2. parse_numbers 读到 `"1"`，产出整数 1；only_even 判断为奇数，不交给 sum，继续要下一项。
3. 读到 `" 2 "`，去空格变成 `"2"`，转成整数 2；only_even 这次交出 2，sum 累计为 2。
4. 空字符串在 parse_numbers 里被跳过；随后读到 `"4"`，同样得到偶数 4，sum 累计为 6。
5. 输入读完，整条链正常结束，sum 返回 6。

把“谁在索要下一项”看清楚，就能理解这种一边读取、一边处理的方式为什么不用提前保存所有中间列表。

12）常见错误：对着现象找原因

这组适合写代码卡住时回来查。先看现象，定位原因后再看修复，不必把所有错误名一次背下来。

12.1 第二次调用，怎么带上了第一次的数据

```python
def bad(values=[]):
    values.append(1)
    return values
```

修复：默认值使用 `None`，函数体内创建新容器。

12.2 循环建了多个函数，结果却全一样

```python
functions = [lambda: index for index in range(3)]
```

修复：`lambda index=index: index`，或使用工厂函数。

12.3 外层明明有 count，内层却报没有赋值

```python
def outer():
    count = 0

    def inner():
        count += 1
        return count
```

这是用于观察错误的片段，还没有调用 inner。在 `outer()` 内调用这里的 `inner()`，才会触发 `UnboundLocalError`；直接在外部写 `inner()` 找不到这个局部函数，会是 `NameError`。修复前一种错误：在 `inner()` 开头声明 `nonlocal count`。

12.4 len 突然不能调用了

```python
len = 10
```

修复：改为 `length`、`size` 等具体名字。

12.5 加完装饰器，返回值变成 None

```python
def wrapper(*args, **kwargs):
    func(*args, **kwargs)
```

修复：`return func(*args, **kwargs)`。

12.6 加完装饰器，函数名字和说明丢了

修复：在包装函数上使用 `@functools.wraps(func)`。

12.7 with 里面报错，外面却像没发生过

```python
def __exit__(self, exc_type, exc_value, traceback):
    return True
```

修复：默认返回 `False`；确实要抑制时只匹配预期异常类型。

12.8 同一个生成器第二次读，变成空结果

修复：需要重复遍历时重新创建生成器，或在数据规模允许时转换为列表并复用。

12.9 返回 False 和抛异常，到底选哪个

先看调用方准备怎么处理。“现在允许请求吗？”可以返回布尔值，再由上层写 `if` 分支；“执行这条命令”失败了，或参数本身非法，通常应抛出明确异常。如果限流器选择用异常表示“当前不允许”，调用方就必须捕获它；如果需要原因和重试时间，也可以返回结构化结果。关键是双方约定一致：不能调用方等着 `False`，函数却突然抛异常中断流程。

13）把几个知识点用在一起

13.1 用闭包记住最近的请求时间

下面要回答“这一段时间内，还能再放行一次吗？”每次先移走过期时间戳，再数剩下多少次；没满就记录本次时间并返回 `True`，满了就返回 `False`。时间戳由闭包保留，计时用单调时钟，避免系统时间被调回去影响判断。

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

这个例子只在单进程、单实例内演示思路，不保证多线程或多进程安全。部署多个服务实例时，它们也不会自动共享这份时间戳，因此不能直接当分布式限流器。那类场景通常要把共享状态放到 Redis 等外部系统，并处理好并发更新、计时和过期。

13.2 把筛选规则和转换规则分别传进去

`retain` 只管“留不留”，`transform` 只管“变成什么”，具体规则由调用方传入。这个例子把高阶函数、lambda、类型提示和生成器放在了一起：

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

这里为了看清组合过程，特意拆成两个函数。如果项目里只有这一处，直接写生成器表达式反而更短；真有多处重复使用，再保留这样的通用函数。

14）动手验证：从传参到生成器

14.1 实现批量调用

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

14.2 修复可变默认参数

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

14.3 闭包计数器

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

14.4 修复循环函数的晚期绑定

修复下面的代码，使输出为 `[10, 11, 12]`：

```python
functions = [lambda value: value + index for index in range(3)]
print([func(10) for func in functions])
```

14.5 带参数装饰器

编写 `require_role(role)` 装饰器。被装饰函数第一个参数是包含 `roles` 集合的用户字典。用户缺少角色时抛 `PermissionError`，否则保留原函数返回值和元数据。

预期行为：

```python
@require_role("admin")
def delete_user(operator, user_id):
    return f"deleted {user_id}"
```

管理员调用返回 `deleted 42`，普通用户调用抛 `PermissionError`。

14.6 上下文管理器计时

分别使用类协议和 `@contextmanager` 实现代码块计时。即使代码块抛异常，也必须执行结束逻辑，但不能吞掉异常。

检查点：`__exit__()` 返回 `False`；生成器版本在 `finally` 中清理。

14.7 生成器分页

实现 `batches(values, size)`，逐批产出列表。`size <= 0` 时抛 `ValueError`。

```python
print(list(batches(range(7), 3)))
```

预期输出：

```text
[[0, 1, 2], [3, 4, 5], [6]]
```

15）合上笔记后，能不能自己解释出来

不用背长定义。尽量用一小段代码回答，比如“改列表”和“重新赋值”各写一次，再预测外面的变量会不会变。

- 能解释位置、关键字、默认、`*args`、`**kwargs` 的绑定规则。
- 能使用 `/` 和 `*` 设计仅限位置或仅限关键字参数。
- 能用例子说明：改参数指向的列表，会影响调用方；给参数重新赋值，则不会换掉调用方的变量。
- 能用 `None` 表示“没有传入容器”，修复默认列表跨调用累积的问题。
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
