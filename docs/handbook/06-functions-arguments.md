06 函数、参数与递归

这一章解决一个经常被一带而过的问题：调用函数时，括号里的值到底交给了谁？看懂这个过程，再看装饰器、FastAPI 的函数签名就不会只剩下背写法。

阅读导航：1–2 是定义和返回；3–6 是参数绑定与拆包；7 是对象共享和默认值；8 是递归；9 是练习答案。

独立运行本章所有完整示例：

```powershell
python scripts/check_handbook_examples.py --chapter 06 --show-output
```

也可以把任意一个带 `runnable` 标记的完整代码块复制到 `.py` 文件运行。`assert` 是结果核对：条件成立时安静通过，不成立会报错。不要加 `-O`，那会关闭断言。

---

1）先分清定义、调用、函数本身

1.1 def 执行时创建函数，函数体等调用时执行

你可以把函数当作有名字的一段操作。定义它是把操作准备好；加括号调用才是现在去做。

```python
# runnable: hb06_definition
events = []

def total(price, quantity):
    events.append("进入函数")
    return price * quantity

assert events == []
calculate = total
assert calculate is total
answer = calculate(12, 3)
assert answer == 36
assert events == ["进入函数"]
print(answer)
```

`calculate = total` 没有算钱，只是让两个名字指向同一个函数对象。`calculate(12, 3)` 才把 12 绑定给 `price`、3 绑定给 `quantity`，然后执行函数体。

所以“把函数作为参数传进去”通常写 `handler=total`。写 `handler=total(12, 3)` 传入的已经是 36，不再是处理规则。这是后面高阶函数最值得先弄清的区别。

1.2 docstring 不是随便放在哪里的三引号注释

函数体第一条语句如果是字符串字面量，它会成为函数的说明。三引号方便换行；真正的注释仍然是 `#`。

```python
# runnable: hb06_docstring
def subtotal(price: int, quantity: int = 1) -> int:
    """计算金额，单位为分。

    price 是单价，quantity 是数量；这里只计算，不负责收款。
    """
    return price * quantity

assert "单位为分" in subtotal.__doc__
assert subtotal(150, 2) == 300
print(subtotal.__name__)
print(subtotal.__doc__)
```

`price: int` 与 `-> int` 告诉人和检查工具预期类型。它们不会自动把传入的字符串变成整数，也不会自动拦住字符串。类型提示与入口校验的分工在第 17 章展开。

---

2）return 把值交出去，print 只负责显示

2.1 为什么屏幕有输出，变量却是 None

```python
# runnable: hb06_print_return
def show_total(a, b):
    print(a + b)

def get_total(a, b):
    return a + b

shown = show_total(2, 3)
saved = get_total(2, 3)
assert shown is None
assert saved == 5
assert saved * 2 == 10
```

第一种函数把 5 打到屏幕，但没有把 5 作为返回值交给调用方。执行到函数末尾没有遇到 `return`，返回值就是 `None`。第二种交回数字，调用方还能继续运算。

做后端时通常把计算放在返回值里；打印、日志、HTTP 响应是外层决定的事情。否则函数只能“展示”，不容易测试，也不容易复用。

2.2 提前返回与返回多个值

```python
# runnable: hb06_multiple_return
def page_bounds(page, size):
    if page < 1 or size < 1:
        return None
    start = (page - 1) * size
    return start, start + size

result = page_bounds(3, 10)
assert result == (20, 30)
start, stop = result
assert start == 20 and stop == 30
assert page_bounds(0, 10) is None
print(start, stop)
```

`return start, stop` 的本质是返回一个元组，不是绕过规则返回了两个独立对象。调用方可以先保存整个元组，也可以立刻拆包。

错误路径返回 `None`，调用方就要先判断，再拆包。否则 `start, stop = page_bounds(0, 10)` 会因为 `None` 不能被拆成两项而报 `TypeError`。如果错误代表“不允许继续”，也可以抛 `ValueError`；不要让同一个函数有时抛异常、有时悄悄用错误数据继续。

---

3）位置、关键字与默认值：同一套参数的不同交法

3.1 形参是接收名字，实参是本次交进去的值

```python
# runnable: hb06_binding
def greet(name, prefix="你好", punctuation="！"):
    return f"{prefix}，{name}{punctuation}"

assert greet("小周") == "你好，小周！"
assert greet("小周", "早上好") == "早上好，小周！"
assert greet(punctuation="。", name="小周") == "你好，小周。"
assert greet("小周", punctuation="。") == "你好，小周。"
```

第一行调用只给 `name` 一个值，另两项用默认值。第二行按顺序给前两项。第三行按名字给值，因此关键字的书写顺序可以和定义顺序不同。

“位置参数”和“关键字参数”常用来描述调用方式，不代表函数里一定有两批不同的参数。这里的 `name` 两种方式都能接收。默认值则说明“本次没给它时用什么”，也是另一件事。

3.2 一项不能拿两份值，也不能把名字拼错

```python
# runnable: hb06_binding_errors
def create(name, age=18):
    return name, age

bad_calls = [
    lambda: create(),
    lambda: create("周", name="吴"),
    lambda: create("周", agge=20),
    lambda: create("周", 20, 30),
]
for call in bad_calls:
    try:
        call()
    except TypeError as error:
        print(type(error).__name__, str(error))
    else:
        raise AssertionError("本次调用应该失败")
assert create("周", age=20) == ("周", 20)
```

四个错误依次是：必填项没给、`name` 收到两次、出现不认识的名字、多出一个位置值。它们发生在函数参数绑定阶段，不是执行完函数体后才发现。

3.3 哪些顺序真的不能写

普通调用中，直接写出的非关键字实参不能放在关键字实参后面。例如 `create(name="周", 20)` 在解析代码时就会报 `SyntaxError`。

普通形参列表也不能把无默认值的位置参数放到有默认值的位置参数后面，例如 `def f(a=1, b): ...`。否则 `f(2)` 的含义会让读者很难判断。

```python
# runnable: hb06_syntax_order
invalid_sources = [
    'create(name="周", 20)',
    'def f(a=1, b):\n    return a + b',
]
for source in invalid_sources:
    try:
        compile(source, "order_demo", "exec")
    except SyntaxError:
        print("写法顺序不合法")
    else:
        raise AssertionError("预期 SyntaxError")
assert len(invalid_sources) == 2
```

这里用 `compile` 是为了把错误写法作为字符串检查，让整个示例还能运行。不要把错误那一行直接放进正常脚本，否则脚本在运行任何逻辑之前就停止了。

有一个别过度背口诀的地方：调用中的 `*iterable` 展开有更灵活的语法，可以出现在关键字实参之后。它展开的仍是位置值，还可能造成重复绑定。日常代码保持“普通位置值、展开位置值、关键字值”这个易读顺序即可。

---

4）不定长参数：星号在定义处收集，在调用处展开

4.1 `*args` 收集多出来的位置值

```python
# runnable: hb06_args
def add_to(start, *amounts):
    print("start =", start, "amounts =", amounts)
    answer = start
    for amount in amounts:
        answer += amount
    return answer

assert add_to(10, 2, 3) == 15
assert add_to(10) == 10
numbers = [2, 3]
assert add_to(10, *numbers) == 15
```

`start` 先接走第一个位置值，剩下的才进入 `amounts`，它是元组。没有剩余值就是空元组，不是 `None`。

`args` 只是常见名字，写 `*amounts` 一样有效。调用处的 `*numbers` 则反过来：把 `[2, 3]` 拆成两个位置实参，而不是传入一个列表。

4.2 `**kwargs` 收集没有被命名形参接走的关键字值

```python
# runnable: hb06_kwargs
def record(event, **fields):
    return {"event": event, "fields": fields}

result = record("login", user_id=7, success=True)
assert result == {"event": "login", "fields": {"user_id": 7, "success": True}}
assert record(event="logout")["fields"] == {}
payload = {"user_id": 8, "success": False}
assert record("login", **payload)["fields"] == payload
```

`event` 是明确声明的形参，即使用关键字传它，也会被 `event` 接走，不会再放进 `fields`。`fields` 的类型是字典。

调用处 `**payload` 的键必须是字符串。即便两个字典里的同名键对应同一个值，`f(**a, **b)` 重复提供参数也会报错；它和 `{**a, **b}` 的“后值覆盖前值”不是同一条规则。

4.3 转发要同时保留位置值、关键字值和返回值

```python
# runnable: hb06_forwarding
def invoke(func, *args, **kwargs):
    return func(*args, **kwargs)

def format_price(amount, *, currency="CNY"):
    return f"{currency} {amount:.2f}"

assert invoke(format_price, 12, currency="USD") == "USD 12.00"
assert invoke(pow, 2, 3) == 8
```

这里接收时把多余参数装起来，调用时原样展开。`return` 也不能漏，否则业务函数算出了字符串，外层 `invoke` 却返回 `None`。装饰器本质上也要面对这三件事。

---

5）斜杠和裸星号：把接口约定写在签名里

5.1 `/` 左边仅限位置，`*` 右边仅限关键字

```python
# runnable: hb06_parameter_kinds
def export(source, /, limit=100, *, encoding="utf-8", overwrite=False):
    return source, limit, encoding, overwrite

assert export("items", 20) == ("items", 20, "utf-8", False)
assert export("items", limit=20, overwrite=True)[3] is True
for call in (
    lambda: export(source="items"),
    lambda: export("items", 20, "utf-8"),
):
    try:
        call()
    except TypeError:
        print("违反参数传法约定")
    else:
        raise AssertionError("预期 TypeError")
```

`source` 必须按位置传；`limit` 两种方式都行；`encoding` 和 `overwrite` 必须把名字写出来。

后两个值很适合关键字限定：`export("items", 20, "utf-8", True)` 让读者猜 `True` 是什么意思，而 `overwrite=True` 直接表达了意图。

如果前面已经有 `*args`，它也起到这个分隔作用，例如 `def f(*values, scale=1): ...`。关键字限定参数可以有默认值，也可以是必填项，不受普通位置参数默认值顺序那条限制。

5.2 全部放在一起读，不要一次背住符号串

下面只展示签名结构，不是业务实现。

```python
# fragment: 参数位置示意，需要自行提供函数体
def submit(source, /, count=1, *items, strict, timeout=3, **extra):
    ...
```

按从左到右读：`source` 只能按位置；`count` 可按位置或名字；多出来的位置值进入 `items`；`strict` 必须按名字给；`timeout` 没给就用 3；剩余关键字进 `extra`。

不需要每个函数都写全套。简单函数写简单签名，只有当“必须怎么传”能减少误用时，再加这些约束。

---

6）拆包：右边先准备好，左边再分配名字

```python
# runnable: hb06_unpacking
left, right = 3, 8
left, right = right, left
assert (left, right) == (8, 3)

first, *middle, last = [10, 20, 30, 40]
assert first == 10 and middle == [20, 30] and last == 40

key1, key2 = {"name": "周", "age": 20}
assert (key1, key2) == ("name", "age")
for key, value in {"name": "周", "age": 20}.items():
    print(key, value)
```

交换时右侧先取到旧的 `right` 和旧的 `left`，所以不需要额外的临时变量。字典直接参与迭代时产出键，想要键和值才用 `.items()`。

没有星号时，左右项数必须相等。有星号时，星号目标接收剩余部分，得到列表；即使右侧是元组也如此。同一层拆包里只能有一个星号目标，否则不知道中间部分怎么分。

---

7）参数传的是对象引用，但不是“调用方变量本身”

7.1 修改对象与重新绑定，区别在哪里

```python
# runnable: hb06_object_sharing
def change(values):
    values.append("内层添加")
    values = ["只给局部名字的新列表"]
    return values

original = ["原值"]
local_result = change(original)
assert original == ["原值", "内层添加"]
assert local_result == ["只给局部名字的新列表"]
assert local_result is not original
```

进函数时，`original` 和 `values` 指向同一个列表。`append` 改了那个列表，因此两边都能看见。随后 `values = ...` 只把局部名字改为指向另一对象，不会替调用方执行 `original = ...`。

这与 Java 的“引用值按值传递”很接近。不要把它背成“Python 能直接修改调用方变量”。真正变的是共享对象的内容，还是某个名字的绑定，需要分开看。

`id` 可以帮助观察同一时刻两个引用是否指向同一对象，更直接的写法是 `is`。对象释放后编号可能复用，所以不要把 `id` 当永久业务编号。

7.2 默认值只在定义函数时求值

```python
# runnable: hb06_mutable_default
def bad_add(value, bucket=[]):
    bucket.append(value)
    return bucket

first = bad_add("A")
second = bad_add("B")
assert first is second
assert first == ["A", "B"]

def good_add(value, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(value)
    return bucket

assert good_add("A") == ["A"]
assert good_add("B") == ["B"]
provided = []
assert good_add("C", provided) is provided
assert provided == ["C"]
```

错误版本不是“上次函数还在运行”，而是两个调用都使用了定义时创建的同一个默认列表。正确版本把新建列表放进函数体，每次缺省调用才各建一个。

不能机械写成 `bucket = bucket or []`。调用方明确传入的空列表也是假值，这样会被换掉，破坏“修改用户交进来的列表”这个约定。

如果 `None` 本身也是合法业务值、而你还要区分“没给”，可以用专门对象当哨兵。

```python
# runnable: hb06_sentinel
MISSING = object()

def describe(value=MISSING):
    if value is MISSING:
        return "没有提供"
    if value is None:
        return "明确提供空值"
    return f"提供了 {value}"

assert describe() == "没有提供"
assert describe(None) == "明确提供空值"
assert describe(0) == "提供了 0"
```

---

8）递归：每次把问题缩小，最后再一层层返回

8.1 不仅要有出口，还必须逐步接近出口

```python
# runnable: hb06_recursion_trace
events = []

def factorial(n):
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("n 必须是非负整数")
    events.append(f"进入 {n}")
    if n <= 1:
        result = 1
    else:
        result = n * factorial(n - 1)
    events.append(f"返回 {n}: {result}")
    return result

assert factorial(3) == 6
assert events == ["进入 3", "进入 2", "进入 1", "返回 1: 1", "返回 2: 2", "返回 3: 6"]
print("\n".join(events))
```

执行过程不是看到 `factorial(3)` 就一次乘完。它分成往下调用与往上返回两个阶段。

| 当前层 | 还在等什么 | 等到后的动作 |
| --- | --- | --- |
| n = 3 | factorial(2) 的结果 | 3 × 2，返回 6 |
| n = 2 | factorial(1) 的结果 | 2 × 1，返回 2 |
| n = 1 | 不再等待 | 直接返回 1 |

每层都有自己的局部 `n`，不是一个 `n` 在所有层里来回变化。`n - 1` 让输入接近出口；只写一个永远到不了的 `if n == 0` 没有用。

8.2 深度很大时换循环，不要一味调大递归限制

```python
# runnable: hb06_recursion_alternative
def factorial_loop(n):
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("n 必须是非负整数")
    result = 1
    for current in range(2, n + 1):
        result *= current
    return result

assert factorial_loop(0) == 1
assert factorial_loop(5) == 120
```

普通 Python 递归不会自动把末尾的递归调用变成循环。调用过深可能触发 `RecursionError`，并且每层都需要保存执行状态。阶乘、简单累计通常用循环更直接；树形数据、目录结构这类“子问题形状相同”的场景更容易用递归表达。

---

9）练习：先写调用过程，再运行答案

9.1 题目一：有折扣的金额函数

写 `bill(price, quantity=1, *, discount=1.0)`。单价按分计算；负单价、数量小于 1、折扣不在 0 到 1 之间应报错。结果仍按分，用 `round` 取整。本题只处理已给定的数值输入，不承担字符串转换。

预期：`bill(1000, 2, discount=0.8)` 为 1600；`bill(1000)` 为 1000。为什么不让折扣作为第三个位置参数？因为 `bill(1000, 2, 0.8)` 比按名字写难读。

参考答案：

```python
# runnable: hb06_exercise_bill
def bill(price, quantity=1, *, discount=1.0):
    if price < 0 or quantity < 1 or not 0 <= discount <= 1:
        raise ValueError("金额、数量或折扣不合法")
    return round(price * quantity * discount)

assert bill(1000, 2, discount=0.8) == 1600
assert bill(1000) == 1000
try:
    bill(1000, discount=1.2)
except ValueError:
    print("非法折扣被拦截")
else:
    raise AssertionError("应该拦截")
```

实际涉及金额精度与舍入规则时，通常使用整数最小单位或明确配置的 `Decimal`。不要把这个入门浮点折扣例子直接当成支付系统的完整金额策略。

9.2 题目二：不改调用方数据的追加函数

要求 `with_tag(tags, new_tag)` 返回新列表，原列表不变。与第 7 节不同，这次接口约定明确要求不修改调用方对象。

```python
# runnable: hb06_exercise_copy
def with_tag(tags, new_tag):
    result = list(tags)
    result.append(new_tag)
    return result

old = ["python"]
new = with_tag(old, "api")
assert old == ["python"]
assert new == ["python", "api"]
assert new is not old
```

这里浅拷贝就够了，因为元素是字符串，而且我们只增添顶层元素。如果之后要修改嵌套字典，浅拷贝并不会隔开内层对象；第 3 章有完整对照。

9.3 题目三：把嵌套列表里的数字求和

例如 `[1, [2, [3]], 4]` 得到 10。本题约定只包含整数与列表，不含循环引用；每遇到子列表就把同样的工作交给下一层。

```python
# runnable: hb06_exercise_nested_sum
def nested_sum(items):
    total = 0
    for item in items:
        if isinstance(item, list):
            total += nested_sum(item)
        else:
            total += item
    return total

assert nested_sum([1, [2, [3]], 4]) == 10
assert nested_sum([]) == 0
assert nested_sum([[], [5]]) == 5
```

空列表没有进入循环，直接返回 0，就是这个问题的自然出口。递归不一定都需要单独写 `if n == 0`；真正需要的是输入越来越小，并且最小情况能结束。

---

10）回想本章时抓住这几个问题

不看代码，解释 `func` 与 `func()` 有什么差别；解释 `*` 在定义和调用位置分别做什么；解释为什么列表在函数里 `append` 后外面会变，而给参数重新赋值却不会替换外面的变量。

最后手算 `factorial(3)`：不能只回答 6，要说清三次进入与三次返回。能讲出过程，才不容易在更复杂的代码里迷路。

本章例子采用 Python 3.11 起即可使用的语法。参数约定可对照 [Python 函数教程](https://docs.python.org/3.11/tutorial/controlflow.html#more-on-defining-functions)，调用展开的细节可查 [调用表达式](https://docs.python.org/3.11/reference/expressions.html#calls)。正文示例为本仓库独立编写。
