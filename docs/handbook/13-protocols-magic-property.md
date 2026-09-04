13 协议、魔术方法与 property：让对象接上熟悉的语法

你已经会写类，下一步不是记更多方法名，而是知道：写 `len(obj)`、`obj[1:3]`、`obj.price = 20` 时，Python 会替你调用哪段代码，以及那段代码必须交回什么。

阅读路线：1 协议与鸭子类型 → 2 字符串展示 → 3 相等与哈希 → 4 可调用对象 → 5 长度和切片 → 6 property 读写全过程 → 7 练习及答案。

本章使用标准库，每个 runnable 代码块独立运行。仓库根目录命令：`python scripts/check_handbook_examples.py --chapter 13 --show-output`。

---

1）协议就是双方对“怎么用”达成约定

1.1 不必先继承同一个父类

一个函数只需要发送消息，就可以接收任何提供合适 `send(message)` 方法的对象。它不必先问“你是不是某个指定类的孩子”。

```python
# runnable: hb13_duck_sender
from typing import Protocol


class Sender(Protocol):
    def send(self, message: str) -> str: ...


class ConsoleSender:
    def send(self, message: str) -> str:
        return f"console:{message}"


class MemorySender:
    def __init__(self) -> None:
        self.messages = []

    def send(self, message: str) -> str:
        self.messages.append(message)
        return f"stored:{message}"


def notify(sender: Sender, message: str) -> str:
    return sender.send(message)


memory = MemorySender()
assert notify(ConsoleSender(), "ready") == "console:ready"
assert notify(memory, "ready") == "stored:ready"
assert memory.messages == ["ready"]
print(memory.messages)
```

两个实现都没有写 `class ... (Sender)`，但方法形状符合约定。类型检查器可以根据 Protocol 检查它们；运行时仍是普通方法调用。

把它和 Java interface 对照：两者都能表达“调用方需要哪些能力”，但这里强调结构符合，不要求在类声明上显式登记 implements。

也不能只凭“存在 send 这个名字”就认为一切正确。参数个数不对会报 TypeError，返回错误类型可能让下一步逻辑失败，发错消息更是业务错误。鸭子类型不是不要契约，而是不强制用继承关系表达契约。

`@runtime_checkable` 可以让某些 Protocol 参与运行时 isinstance 检查，但它不负责完整验证参数签名和返回类型。不要把它当数据校验器。

1.2 特殊方法是 Python 预先规定的协议入口

| 外面写什么 | 主要对应方法 | 方法收到什么 | 应交回什么 |
| :-- | :-- | :-- | :-- |
| `str(obj)` | `__str__` | self | str |
| `repr(obj)` | `__repr__` | self | str |
| `left == right` | 相等比较协议，包含 `__eq__` | self、other | 本章返回 bool 或 NotImplemented |
| `hash(obj)` | `__hash__` | self | int，且符合相等约定 |
| `obj("text")` | `__call__` | self、调用参数 | 由接口定义 |
| `len(obj)` | `__len__` | self | 非负整数 |
| `obj[key]` | `__getitem__` | self、key | 元素或约定的切片结果 |

一般在类上定义这些方法，使用时仍写正常语法。不要依赖把同名函数临时塞到某一个实例上来改变所有特殊操作；隐式特殊方法查找有自己的规则，通常从类型上查找。

---

2）str 和 repr：给人看，还是帮你排错

2.1 两个出口解决不同的显示需求

```python
# runnable: hb13_str_repr
class User:
    def __init__(self, user_id: int, name: str) -> None:
        self.user_id = user_id
        self.name = name

    def __str__(self) -> str:
        return f"{self.name}({self.user_id})"

    def __repr__(self) -> str:
        return f"User(user_id={self.user_id!r}, name={self.name!r})"


user = User(7, "Ada")
assert str(user) == "Ada(7)"
assert repr(user) == "User(user_id=7, name='Ada')"
assert repr([user]) == "[User(user_id=7, name='Ada')]"
print(user)
print([user])
```

第一行显示 `Ada(7)`。第二行显示列表，列表使用元素的 repr，所以能看见 User 类名和字段名。

`!r` 表示把字段按 repr 嵌进去。名字是字符串时，引号、换行转义更容易看清，排查“到底多了一个空格还是没有值”时很有用。

`__repr__` 尽量明确、无歧义，能写成类似构造表达式更好，但不是所有 repr 都必须能被 eval 重新执行。不要对外部输入使用 eval 来“还原对象”。

2.2 方法要返回字符串，不是自己 print

如果 `__str__` 里面只写 print，函数默认返回 None，外面的 `str(obj)` 会因为没拿到字符串而报 TypeError。打印职责与生成字符串职责要分开。

没有自定义 `__str__` 时，默认展示会借用 repr。两者都没写时，通常会看到包含类型名和身份信息的默认对象表示，不能把其中的地址样式作为稳定输出做断言。

不要把密码、令牌等敏感字段放进 repr。日志、异常提示和容器展示都可能间接调用它，你未必每次都能注意到。

---

3）相等和哈希：像 Java 的 equals 与 hashCode 一样成套考虑

3.1 is 问“是不是同一个”，等号问“内容算不算相等”

```python
# runnable: hb13_value_equality
class OrderId:
    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object):
        if not isinstance(other, OrderId):
            return NotImplemented
        return self.value == other.value


first = OrderId("A-1")
second = OrderId("A-1")
assert first is not second
assert first == second
assert first != OrderId("A-2")
assert first != "A-1"
assert first.__eq__("A-1") is NotImplemented
try:
    hash(first)
except TypeError:
    pass
else:
    raise AssertionError("mutable value object should be unhashable here")
print(first == second, first is second)
```

比较两个 OrderId 时，self 是一个对象，other 是另一个；先判断对方是不是能理解的类型，再比较各自的 value。

`NotImplemented` 表示“这个组合我处理不了，请 Python 按比较协议继续尝试”。它不是 `NotImplementedError`，也不是 False。上面直接调用特殊方法，只是为了观察这个返回值；业务比较仍写 `first == other`。

相等比较可能尝试另一方的方法，子类也有优先级规则，不能认为任何 `a == b` 都只是机械调用一次 `a.__eq__(b)`。双方都不能处理相等比较时，会回退到身份方面的规则。

3.2 为什么定义相等后，反而不能放集合了

上面的对象可以改 value。假设先按 A-1 的哈希位置放进集合，再把 value 改成 A-2，集合就难以继续按原约定找到它。

Python 对“定义 `__eq__`、没有相应定义 `__hash__`”的类通常会设置为不可哈希，阻止这种误用。不要看到 TypeError 就随手加 `__hash__ = object.__hash__`：这样内容相等的两个对象可能有不同哈希，破坏约定。

最重要的一条是：如果 a 和 b 相等，`hash(a)` 必须等于 `hash(b)`。反过来不成立，哈希相同仍可能不相等，这叫碰撞。

3.3 不可变值对象可以让 dataclass 配套生成

```python
# runnable: hb13_frozen_hash
from dataclasses import dataclass, FrozenInstanceError


@dataclass(frozen=True)
class Money:
    cents: int
    currency: str


first = Money(100, "CNY")
second = Money(100, "CNY")
assert first == second
assert hash(first) == hash(second)
assert len({first, second}) == 1
prices = {first: "one yuan"}
assert prices[second] == "one yuan"
try:
    first.cents = 200
except FrozenInstanceError:
    pass
else:
    raise AssertionError("frozen field was changed")
print(prices[second])
```

这里字段都是可哈希的整数和字符串，因此生成的哈希可以工作。`frozen=True` 不是“把里面的一切递归冻住”；如果字段改成列表，列表仍不可哈希，不能照搬这个结论。

不要断言某个对象的哈希必须等于某个固定数字，尤其字符串相关哈希可能跨进程变化。需要验证的是相等对象哈希一致，以及作为字典键时行为正确。

---

4）call：对象也能像函数那样接收参数

```python
# runnable: hb13_callable_prefix
class Prefixer:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self.calls = 0

    def __call__(self, message: str, *, upper: bool = False) -> str:
        self.calls += 1
        text = f"{self.prefix}{message}"
        return text.upper() if upper else text


warn = Prefixer("warn: ")
assert warn.calls == 0
assert warn("disk low") == "warn: disk low"
assert warn("retry", upper=True) == "WARN: RETRY"
assert warn.calls == 2
assert callable(warn)
print(warn.calls)
```

`Prefixer("warn: ")` 是创建实例，调用 `__init__` 保存 prefix。之后的 `warn("disk low")` 才是调用这个实例，进入 `__call__`。

两次调用使用同一个 prefix，calls 从 0 变成 1，再变成 2。它相当于把“函数需要的配置和状态”一起装进对象，适合回调、规则对象、计数器和限流器。

`callable(obj)` 只能告诉你对象能不能被调用，不保证某组参数一定被接受。对 warn 传三个位置参数，仍会因为签名不匹配而失败。

---

5）长度、索引与切片：先明确容器的接口承诺

5.1 getitem 收到的 key 不一定是整数

```python
# runnable: hb13_index_slice
class NameBook:
    def __init__(self, names) -> None:
        self._names = list(names)

    def __len__(self) -> int:
        return len(self._names)

    def __getitem__(self, key):
        return self._names[key]

    def __iter__(self):
        return iter(self._names)


book = NameBook(["Ada", "Bob", "Cora", "Dan"])
assert len(book) == 4
assert bool(book) is True
assert bool(NameBook([])) is False
assert book[0] == "Ada"
assert book[-1] == "Dan"
assert book[1:4:2] == ["Bob", "Dan"]
assert book[::-1] == ["Dan", "Cora", "Bob", "Ada"]
assert book[99:] == []
assert list(book) == ["Ada", "Bob", "Cora", "Dan"]
try:
    book[99]
except IndexError:
    pass
else:
    raise AssertionError("out-of-range index was accepted")
print(book[1:4:2])
```

执行 `book[1]` 时，key 是整数 1。执行 `book[1:4:2]` 时，key 是 `slice(1, 4, 2)` 对象，里面分别有 start、stop、step。

这里不自己重写切片算法，直接交给内部列表处理，因此自然继承列表的负索引、步长、越界切片规则。返回一个名字还是一个列表，取决于 key 是整数还是切片。

这一接口选择也要说清：本章切片返回 list，不返回 NameBook。自定义容器可以选择其他返回类型，但要前后一致，别让使用者猜。

5.2 长度影响 bool，但不负责产生迭代器

没有自定义 `__bool__` 时，Python 可以使用 `__len__` 判断真假：0 为假，非 0 为真。`__len__` 必须给非负整数，不能用 -1 表示未知长度。

`__iter__` 返回迭代器，for 不断从它拿下一个元素。长度、索引、迭代是相关但不同的能力，写了 len 并不意味着可以任意索引。

如果自己展开切片，可以使用 `slice.indices(length)` 得到适用于该长度的 start、stop、step，再交给 range。它处理了默认值和边界，不必猜 `None` 在反向切片里表示什么。

```python
# runnable: hb13_slice_indices
values = [10, 20, 30, 40, 50]
key = slice(None, None, -2)
start, stop, step = key.indices(len(values))
indices = list(range(start, stop, step))
assert (start, stop, step) == (4, -1, -2)
assert indices == [4, 2, 0]
assert [values[index] for index in indices] == values[key] == [50, 30, 10]
print(indices)
```

这里归一化后的 -1 是 range 的停止边界，不要再把它拼回 `values[4:-1:-2]` 并期待相同结果；重新写成切片时，-1 又会被解释为原列表的负索引。

---

6）property：属性读写如何进入函数

6.1 初始化、修改、读取，走的是不同入口

```python
# runnable: hb13_property_chain
import math


class Product:
    def __init__(self, price: float) -> None:
        self.events = []
        self.price = price

    @property
    def price(self) -> float:
        self.events.append("get")
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        self.events.append(("set", value))
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("price must be a number")
        normalized = float(value)
        if not math.isfinite(normalized) or normalized < 0:
            raise ValueError("price must be finite and non-negative")
        self._price = normalized


product = Product(19.9)
product.price = 25
assert product.price == 25.0
assert product.events == [("set", 19.9), ("set", 25), "get"]
try:
    product.price = -1
except ValueError:
    pass
else:
    raise AssertionError("negative price was accepted")
assert product.price == 25.0
assert product.__dict__["_price"] == 25.0
assert "price" not in product.__dict__
print(product.price)
```

创建时，`self.price = price` 进入 setter；修改时，`product.price = 25` 也进入同一个 setter；读取时，`product.price` 进入 getter，拿到返回值后再参与比较或打印。

| 操作 | 输入 | 真正保存的数据 | 返回到调用处的内容 |
| :-- | :-- | :-- | :-- |
| 初始化 19.9 | setter 的 value=19.9 | `_price=19.9` | 创建流程得到实例 |
| 修改为 25 | setter 的 value=25 | `_price=25.0` | 赋值语句本身不领取 setter 返回值 |
| 读取价格 | getter 只有 self | 不改价格 | 25.0 |
| 修改为 -1 | setter 的 value=-1 | 仍为 25.0 | 抛 ValueError |

这里先完成类型检查、转换和范围检查，再写 `_price`。因此失败不会把原值改坏。`math.isfinite` 补上 NaN 和无穷大的边界；单靠 `value < 0` 拦不住这些值。

这仍然只是数值属性演示，不是完整金额模型。金额精度、币种、舍入规则需要单独设计，不能因为叫 price 就认为 float 已解决财务计算。

6.2 property 放在类上，数据通常放在实例上

类创建时，`@property` 把读取函数包装成 property 对象，`@price.setter` 补上写入函数。后来访问实例属性时，这个对象负责转交读写请求。

因此“实例有同名字段就一定优先”不是完整属性查找规则。property 属于数据描述符，按正常属性访问流程有其优先级。日常使用只需记住：对外的 price 是规则入口，内部的 `_price` 是本例选择的数据位置。

下划线不是魔法。把内部存储改名为 `_stored_price` 也能工作，只要 getter 和 setter 指向同一个不冲突的名字。

6.3 无限递归发生在什么位置

```python
# runnable: hb13_property_recursion
class Broken:
    @property
    def price(self):
        return self.price

    @price.setter
    def price(self, value):
        self.price = value


obj = Broken()
errors = []
try:
    obj.price = 10
except RecursionError:
    errors.append("setter")
try:
    value = obj.price
except RecursionError:
    errors.append("getter")
assert errors == ["setter", "getter"]
print(errors)
```

写入链是：`obj.price = 10` → setter → 又执行 `self.price = 10` → 又进入 setter。读取链同理：为了返回 price，先读 price；为了读 price，又调用 getter。

两条链都没有到达一个普通存储位置，所以最终触发 RecursionError。不要通过提高递归深度来“修复”，应改为 getter 读 `_price`、setter 写 `_price`。

6.4 只读计算属性不是缓存

```python
# runnable: hb13_computed_property
class Rectangle:
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    @property
    def area(self) -> float:
        return self.width * self.height


rectangle = Rectangle(3, 4)
assert rectangle.area == 12
rectangle.width = 5
assert rectangle.area == 20
try:
    rectangle.area = 99
except AttributeError:
    pass
else:
    raise AssertionError("read-only property was assigned")
print(rectangle.area)
```

每次读 area 都重新计算，所以宽改变后结果跟着改变。没有 setter，只是禁止给 area 这个入口直接赋值，不表示整个 Rectangle 不可变。

没有校验、计算或接口兼容需求时，直接公开属性即可，不必把每个字段都绕成 getter/setter。

---

7）练习与完整参考答案

7.1 练习一：库存只接收非负整数

实现 StockBox.stock。赋 0 和 3 成功，-1、2.5、True 失败，失败后旧值保持。为什么要特别测 True？因为 `isinstance(True, int)` 为真。

```python
# runnable: hb13_exercise_stock
class StockBox:
    def __init__(self, stock: int) -> None:
        self.stock = stock

    @property
    def stock(self) -> int:
        return self._stock

    @stock.setter
    def stock(self, value: int) -> None:
        if type(value) is not int:
            raise TypeError("stock must be an integer, not bool or float")
        if value < 0:
            raise ValueError("stock must be non-negative")
        self._stock = value


box = StockBox(0)
box.stock = 3
for value in (-1, 2.5, True):
    try:
        box.stock = value
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError(f"accepted invalid stock: {value!r}")
    assert box.stock == 3
print(box.stock)
```

检查完再保存，保证失败时状态不变。使用 exact int 是这道题的接口选择，不是所有接受整数的函数都必须排除 int 子类。

7.2 练习二：能显示、能比较，但不能当字典键

实现可改名字的 Label，两个名字相等则对象相等，repr 看得出字段内容。不要添加 hash。

```python
# runnable: hb13_exercise_label
class Label:
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"Label(name={self.name!r})"

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return self.name == other.name


first = Label("draft")
second = Label("draft")
assert first == second
assert repr(first) == "Label(name='draft')"
second.name = "ready"
assert first != second
assert Label.__hash__ is None
print(first, second)
```

这里使用 exact type，把“父子类是否也能按名字相等”排除在契约外。前面的 OrderId 用 isinstance，允许子类参与；两种写法要根据相等规则选择，不能只凭喜好混用。

7.3 练习三：带状态的可调用累加器

创建 `Accumulator(10)`，连续调用无参、传 4、传 -2，分别得到 11、15、13。读取 total 不应再增加它。

```python
# runnable: hb13_exercise_accumulator
class Accumulator:
    def __init__(self, start: int = 0) -> None:
        self._total = start

    def __call__(self, step: int = 1) -> int:
        self._total += step
        return self._total

    @property
    def total(self) -> int:
        return self._total


counter = Accumulator(10)
assert [counter(), counter(4), counter(-2)] == [11, 15, 13]
assert counter.total == 13
assert counter.total == 13
other = Accumulator()
assert other() == 1
assert counter.total == 13
print(counter.total, other.total)
```

`__call__` 是操作入口，property 是读取入口，两者虽然都能访问内部状态，但没有必要做同样的事。

---

8）回看与资料

读到陌生特殊方法时，不要先背名字，先补齐一句话：“用户写什么，Python 传进什么，我必须返回什么。”很多错误会在这句话里直接暴露出来。

官方参考：[特殊方法与属性访问](https://docs.python.org/3.11/reference/datamodel.html)、[property](https://docs.python.org/3.11/library/functions.html#property)、[Protocol](https://docs.python.org/3.11/library/typing.html#typing.Protocol)、[dataclasses](https://docs.python.org/3.11/library/dataclasses.html)。
