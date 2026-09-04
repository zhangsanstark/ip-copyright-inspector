Python 面向对象：Java 后端迁移笔记

写过 Java 类之后，Python 面向对象并不难上手。真正需要换个思路的地方有三个：属性不必都包一层 getter/setter，对象不必先声明实现接口，多继承中的 `super()` 也不一定直奔父类。

阅读顺序：1 创建对象 → 2 变量归谁 → 3 下划线 → 4 property → 5 魔术方法 → 6 鸭子类型 → 7 继承与 MRO → 8 组合。9—12 是排错、Java 对照和练习，可以回头查。

建议先运行配套文件：

```powershell
python examples/oop_lab.py
```

1）创建对象：少了 new，多了 self

1.1 self 表示“这一次操作的是谁”

Java 写 `new User(...)`，Python 直接写 `User(...)`。调用这个类时，通常先创建实例，再执行 `__init__` 填好它的初始数据。

```python
class User:
    def __init__(self, user_id: int, name: str = "anonymous") -> None:
        self.user_id = user_id
        self.name = name

    def greeting(self) -> str:
        return f"hello, {self.name}"


user = User(7, "Alice")
print(user.greeting())
```

预期输出：

```text
hello, Alice
```

同一个类可以创建 Alice、Bob 等多个对象，`self` 就告诉方法“这次处理的是哪一个”。它相当于 Java 中的 `this`，只是 Python 要把它写进参数列表。调用 `user.greeting()` 时，Python 会自动把 `user` 传进去，可以理解成 `User.greeting(user)`；调用时不用再手动传一次。

需要记住这些边界：

- `self` 不是关键字，只是全社区都遵守的命名约定，不应换成别的名字。
- `__init__` 负责初始化，严格说不是分配对象的构造器；真正创建实例的是 `__new__`，普通业务类几乎不需要重写它。
- Python 不支持按参数列表进行 Java 式构造器重载。通常使用默认参数、关键字参数或 `@classmethod` 工厂方法。
- 方法和类也是对象，可以赋给变量、传入函数或放进容器。

先记住最常用的写法：创建对象不写 `new`，定义实例方法时第一个参数写 `self`。

马上练一下：给 `User` 增加 `from_dict` 类方法，接收 `{"user_id": 8, "name": "Bob"}` 并返回实例。再把 `User` 换成子类调用这个工厂，确认返回的仍是子类。

1.2 多种创建方式，用默认参数或类方法

Java 可以重载构造器，Python 通常给不同入口起清楚的名字。比如“创建原点”叫 `origin()`，“从逗号分隔的文本创建”叫 `from_csv()`，调用处一眼就能看出来源：

```python
from __future__ import annotations


class Coordinate:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    @classmethod
    def origin(cls) -> Coordinate:
        return cls(0.0, 0.0)

    @classmethod
    def from_csv(cls, text: str) -> Coordinate:
        x_text, y_text = text.split(",")
        return cls(float(x_text), float(y_text))
```

`self` 指当前对象，`cls` 指当前类。这里写 `cls(...)` 很重要：以后子类继承了这个方法，调用时仍会创建子类对象。如果写死 `Coordinate(...)`，无论谁来调用，得到的都只是 `Coordinate`。

2）类变量和实例变量：这份数据到底归谁

2.1 类上放共同信息，self 上放各自状态

写在类体里的变量是类变量，可以先类比 Java 的 `static` 字段。写成 `self.token` 的是实例变量：Alice 的 token 和 Bob 的 token 应各存一份，不应该互相影响。

```python
class Session:
    created_count = 0

    def __init__(self, token: str) -> None:
        self.token = token
        type(self).created_count += 1


a = Session("a-token")
b = Session("b-token")
print(a.token, b.token)
print(Session.created_count)
```

预期输出：

```text
a-token b-token
2
```

2.2 给实例赋值，通常不会改掉类上的默认值

对下面这种普通属性，实例先找自己的值，没有才到类以及父类中查找。给 `first.enabled` 赋值，相当于让 `first` 有了自己的设置；`second` 仍用类上的默认值。后面介绍的 `property` 有自己的读写规则，不要把这个查找顺序当成所有属性的完整规则。

```python
class Feature:
    enabled = True


first = Feature()
second = Feature()
first.enabled = False
print(first.enabled, second.enabled, Feature.enabled)
```

预期输出：

```text
False True True
```

2.3 可变类变量最容易让两个对象“串数据”

把购物车列表放在类上，只会创建一个列表。两个购物车没有各自的 `items`，就会找到并修改同一份：

```python
class BadCart:
    items: list[str] = []

    def add(self, item: str) -> None:
        self.items.append(item)


cart_a = BadCart()
cart_b = BadCart()
cart_a.add("book")
print(cart_b.items)
```

预期输出是 `['book']`，这通常不是业务想要的结果。应把容器放进 `__init__`：

```python
class Cart:
    def __init__(self) -> None:
        self.items: list[str] = []
```

区别就在创建位置：写在类里，大家共用一份；写在 `__init__` 里，每创建一个购物车就新建一个列表。固定配置可以放类上，各自的订单、商品和状态通常应该放在 `self` 上。

类型检查器可以用 `ClassVar` 明确类变量意图：

```python
from typing import ClassVar


class Job:
    category: ClassVar[str] = "batch"

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
```

3）下划线：表达使用约定，不是给数据上锁

Java 用 `public`、`protected`、`private` 限制访问；Python 更多是在名字上告诉使用者“这个能公开用”“这个是内部细节”。看见下划线，不要自动理解成外部绝对访问不到。

- `name` 是公开属性。
- `_name` 表示内部实现或受保护成员，外部技术上仍可访问。
- `__name` 会触发名称修饰，在类 `Account` 中通常变成 `_Account__name`，主要用于避免子类意外覆盖，不是安全边界。
- `__name__` 这种两侧都有双下划线的名称由 Python 数据模型保留，不应随意发明。

```python
class Account:
    def __init__(self, account_id: str) -> None:
        self.account_id = account_id
        self._status = "active"
        self.__secret = "internal-value"


account = Account("A-100")
print(account.account_id)
print(account._status)
print(account.__dict__)
```

看到 `_Account__secret` 不代表应该从外部使用它。真正的敏感信息保护依赖权限控制、密钥管理、日志脱敏和数据加密，不能依赖双下划线。

4）property：看起来在赋值，实际先经过检查

4.1 调用方仍写属性，类内部决定怎么读写

假设商品价格不能为负数。Java 往往在 `setPrice()` 里检查，Python 可以让调用方继续写 `product.price = 25`，再由 `property` 把这次赋值转交给 setter 检查。

```python
class Product:
    def __init__(self, price: float) -> None:
        self.price = price

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if value < 0:
            raise ValueError("price must be non-negative")
        self._price = float(value)


product = Product(19.9)
product.price = 25
print(product.price)
```

对外始终访问 `product.price`，初始化和后续赋值都会经过校验；内部用 `_price` 保存数据。

4.2 为什么 setter 里不能再写 self.price

下面看起来只是保存价格，实际上是在反复调用自己：

```python
class BrokenProduct:
    @property
    def price(self) -> float:
        return self.price

    @price.setter
    def price(self, value: float) -> None:
        self.price = value
```

`self.price = value` 本来就表示“请 setter 处理”。如果 setter 里面还是这句话，就会再次进入 setter，永远走不到结束。getter 里 `return self.price` 也一样：为了读价格，又调用一次读价格，最后得到 `RecursionError`。

解决方法是把两个名字分开：`price` 负责对外读写，`_price` 真正存数据。下面只演示如何避免递归；非负校验仍参考前面的 `Product`：

```python
class SafeProduct:
    def __init__(self, price: float) -> None:
        self.price = price

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        self._price = float(value)
```

4.3 算出来的属性，可以只读不写

面积由宽和高算出来，不必再保存一份容易过期的值。只写 getter，就能用 `rectangle.area` 读取；不提供 setter，就不让调用方直接给面积赋值：

```python
class Rectangle:
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    @property
    def area(self) -> float:
        return self.width * self.height
```

没有校验、计算或兼容旧接口的需要，直接使用公开属性就好，不必给每个字段都配 property。真正要记住的是：外面用 `price` 触发规则，里面用 `_price` 保存结果。

马上练一下：给 `Product` 增加 `stock` property，只接受非负整数。分别赋值 `3`、`-1` 和 `2.5`，为后两种情况设计清楚的异常信息。

5）魔术方法：让自己的对象也能用 len、方括号和 print

魔术方法不是另一套神秘语法，而是 Python 留给类的一组接口。比如写好 `__len__`，别人就能用 `len(queue)`；写好 `__getitem__`，别人就能用 `queue[0]`。使用对象时仍写这些正常语法，不需要手动调用 `queue.__len__()`。

5.1 `__str__` 给人看，`__repr__` 帮你排错

`print(user)` 通常希望简洁好读，会用 `__str__`，很像 Java 的 `toString()`。排错时还想知道对象是什么类、字段是什么值，就用 `__repr__`。它也会出现在交互式环境和列表等容器的展示中，能写成类似构造调用的样子就更清楚。

```python
class User:
    def __init__(self, user_id: int, name: str) -> None:
        self.user_id = user_id
        self.name = name

    def __str__(self) -> str:
        return f"{self.name}({self.user_id})"

    def __repr__(self) -> str:
        return f"User(user_id={self.user_id!r}, name={self.name!r})"


user = User(7, "Alice")
print(user)
print([user])
```

预期输出：

```text
Alice(7)
[User(user_id=7, name='Alice')]
```

`!r` 会把字段按 `repr` 形式嵌入，字符串引号等细节更清楚。不要把密码、令牌等秘密放进 `__repr__`，因为日志和报错经常隐式调用它。

5.2 `__eq__` 决定“内容相同算不算相等”

默认对象相等性通常接近身份比较。实现 `__eq__` 后，`a == b` 可以按业务值比较：

```python
class OrderId:
    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OrderId):
            return NotImplemented
        return self.value == other.value
```

参数标成 `object`，因为比较时对方可能是什么类型。遇到不认识的类型，返回 `NotImplemented`，意思是“这次比较我处理不了，请 Python 尝试对方的比较规则”。它是一个专门的值，不是字符串，也不是要抛出的异常；双方都处理不了时，相等比较会按相应规则退回身份比较，通常得到 `False`。

这里还有个和 Java `equals` / `hashCode` 类似的配套问题：两个对象既然相等，哈希也必须一致。只定义 `__eq__` 时，Python 通常会让对象不可哈希，避免它误入字典或集合。不可变值对象可以考虑 `@dataclass(frozen=True)`，让标准库生成配套的 `__eq__` 和 `__hash__`。

5.3 `__call__` 让对象像函数一样使用

实现 `__call__` 后，实例可像函数一样调用。它适合“带配置或状态的函数对象”：

```python
class Prefixer:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def __call__(self, text: str) -> str:
        return f"{self.prefix}{text}"


warn = Prefixer("WARN: ")
print(warn("disk is nearly full"))
```

预期输出：

```text
WARN: disk is nearly full
```

5.4 `__len__` 返回长度，也可能影响真假判断

`len(obj)` 转发到 `obj.__len__()`。返回值必须是非负整数，否则会抛出 `TypeError` 或 `ValueError`。如果未定义 `__bool__`，Python 还会用长度是否为零判断对象真假。

5.5 `__getitem__` 同时接住索引和切片

`obj[key]` 会调用 `__getitem__(key)`；`obj[1:4:2]` 传入的不是三个整数，而是一个 `slice(1, 4, 2)` 对象。

```python
from collections.abc import Iterator
from typing import overload


class NameBook:
    def __init__(self, names: list[str]) -> None:
        self._names = list(names)

    def __len__(self) -> int:
        return len(self._names)

    @overload
    def __getitem__(self, key: int) -> str: ...

    @overload
    def __getitem__(self, key: slice) -> list[str]: ...

    def __getitem__(self, key: int | slice) -> str | list[str]:
        return self._names[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._names)


book = NameBook(["A", "B", "C", "D"])
print(book[1])
print(book[1:4:2])
```

预期输出：

```text
B
['B', 'D']
```

将切片直接委托给内部列表，可以自然保留负索引、步长以及越界处理。如果自己实现整数索引，越界时应抛 `IndexError`，否则 Python 某些旧式迭代回退机制可能无法停止。现代容器最好显式实现 `__iter__`。

5.6 把这些方法放进一个队列

配套文件中的 `CustomQueue` 同时实现了 `__len__`、`__bool__`、`__getitem__`、`__iter__`、`__repr__` 和 `__eq__`。这样的类能自然接入 Python 语法：

```python
queue = CustomQueue(["a", "b", "c"])
print(len(queue))
print(bool(queue))
print(queue[-1])
print(queue[0:2])
print(list(queue))
```

不用为了“更像 Python”而凑齐所有魔术方法。队列确实有长度和元素，写 `len`、索引协议很自然；但一个业务对象没有明确大小关系，就不该随意让它支持 `>`、`<`。需要什么能力，就实现对应的方法。

马上练一下：让 `CustomQueue` 支持 `reversed(queue)`。可以实现 `__reversed__`，也可以思考已有的长度和索引协议是否足够。验证反转不会修改原队列。

6）鸭子类型：我需要你会 send，不要求你出自哪个父类

Java 常先定义接口，再让类 `implements`。Python 运行时可以更直接：`notify` 只想发一条消息，传进来的对象只要能正确执行 `send(message)` 就行，邮件发送器和短信发送器不必继承同一个父类。这就是“鸭子类型”：看它能做什么，不先问它是什么。

```python
class EmailSender:
    def send(self, message: str) -> None:
        print(f"email: {message}")


class SmsSender:
    def send(self, message: str) -> None:
        print(f"sms: {message}")


def notify(sender: object, message: str) -> None:
    sender.send(message)  # type checker 无法从 object 得知 send
```

上面的写法运行时可以工作，但标成 `object` 后，类型检查器不知道它有 `send`。如果想在运行前就检查“传来的对象有没有这个方法”，可以用 `Protocol` 把要求写清楚：

```python
from typing import Protocol


class Sender(Protocol):
    def send(self, message: str) -> None:
        ...


def notify(sender: Sender, message: str) -> None:
    sender.send(message)
```

`EmailSender` 和 `SmsSender` 不需要显式继承 `Sender`，只要方法签名匹配即可。这很像 Go 的隐式接口，也可看作比 Java 显式 `implements` 更松耦合的静态检查方式。

鸭子类型不等于吞掉所有异常。通常直接调用所需方法，让真正的 `AttributeError` 或业务异常暴露出来，比先堆叠大量 `hasattr` 更清晰。如果需要运行时检查，可给协议加 `@runtime_checkable`，但它主要检查属性是否存在，不会完整验证签名和语义。

可以把两层分开记：鸭子类型让代码运行时按能力合作，`Protocol` 让类型检查器提前检查这些能力。它们都不要求每个发送器先写一次 `implements` 式声明。

马上练一下：写一个完全不继承 `Sender` 的 `FileLikeSender`，只实现 `send` 并把消息放进列表。把它传给 `notify`，验证鸭子类型正常工作。

7）继承和 MRO：super 找的是调用顺序中的下一位

7.1 单继承时，先理解“补充功能后接着往下做”

子类可以重写父类方法，也可以先补一段逻辑，再把剩余工作交给 `super()`。例如保存前先记审计信息：

```python
class Repository:
    def save(self, value: str) -> None:
        print(f"save {value}")


class AuditedRepository(Repository):
    def save(self, value: str) -> None:
        print(f"audit {value}")
        super().save(value)
```

单继承里，下一位通常就是父类，所以看起来和 Java 的 `super` 很像。多继承时就不能靠这个直觉了：`super()` 会沿当前对象所属类的 MRO，从当前类之后继续找方法，不是固定跳到代码里写的那个父类。

7.2 多继承先看 mro()，别凭继承图猜

Python 允许一个类同时继承多个类。几个父类都有同名方法，到底先找谁？Python 会先排出一张查找顺序表，这就是 MRO。直接看 `ClassName.mro()` 或 `ClassName.__mro__`，比在脑子里猜可靠得多。

```python
class Root:
    def handle(self) -> list[str]:
        return ["Root"]


class Left(Root):
    def handle(self) -> list[str]:
        return ["Left", *super().handle()]


class Right(Root):
    def handle(self) -> list[str]:
        return ["Right", *super().handle()]


class Child(Left, Right):
    def handle(self) -> list[str]:
        return ["Child", *super().handle()]


print([cls.__name__ for cls in Child.mro()])
print(Child().handle())
```

预期输出：

```text
['Child', 'Left', 'Right', 'Root', 'object']
['Child', 'Left', 'Right', 'Root']
```

注意 `Left` 里的 `super().handle()` 最终调用 `Right.handle()`，不是直接跳到 `Root.handle()`。这是理解协作式多继承的关键。

7.3 C3：把多条继承关系排成一条不冲突的顺序

多继承像几条队伍要合成一队，但不能随意把原来的先后关系打乱。Python 用 C3 算法完成这个排序。日常不必背算法，先看它必须守住哪些要求：

- 子类排在父类之前，先找更具体的实现。
- 保留类声明要求的父类顺序，例如 `Child(Left, Right)` 中 `Left` 在 `Right` 前；无法同时满足时，不会凑出一个将就的顺序。
- 子类继续扩展继承关系时，不颠倒父类 MRO 中已有的先后关系，这叫“单调性”。

如果想知道它怎么排：先放当前类，再合并各父类的 MRO 和直接父类列表。每轮只能选某条列表的第一项，而且这项不能藏在别的列表后面，否则说明那里还有必须先排的人。一直选不出合适项，就说明要求互相冲突，定义类时直接抛 `TypeError`。

一个矛盾例子：

```python
class X:
    pass


class Y:
    pass


class A(X, Y):
    pass


class B(Y, X):
    pass


class Broken(A, B):
    pass
```

`A` 要求 `X` 在 `Y` 前，`B` 又要求 `Y` 在 `X` 前，因此 `Broken` 不可能得到一致 MRO。上面这段代码专门用于观察错误，单独运行会在定义 `Broken` 时抛出 `TypeError`。

这个例子不用手算：一边要求 X 先，一边要求 Y 先，根本没法同时满足。遇到多继承问题，先打印 MRO，再沿着顺序看每一层是否继续调用了 `super()`，通常就能找到断点。

马上练一下：交换为 `OrderProcessor(AuditMixin, ValidationMixin)`，先不要运行，写下你预测的 MRO 和调用日志，再用 `mro()` 验证。

7.4 大家都接着调用，整条链才能走完

`super()` 只能找到下一位，不能替下一位继续工作。如果中间某层处理完就返回，后面的类就没有机会执行。因此，这种协作式多继承要约好：

- 每一层都调用 `super()`，除非它明确是链条终点。
- 方法签名要兼容。初始化 Mixin 常消费自己的关键字参数，再把剩余 `**kwargs` 传下去。
- 不要在同一条链里混用 `Parent.method(self)` 和 `super().method()`，否则可能重复调用或跳过节点。
- Mixin 应小而专注，通常不独立实例化，名称常以 `Mixin` 结尾。
- 能用组合清晰表达时，优先组合；多继承更适合彼此相对独立、又能叠加使用的行为。

```python
class BaseService:
    def __init__(self, *, name: str, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.name = name


class RetryMixin:
    def __init__(self, *, retries: int = 3, **kwargs: object) -> None:
        self.retries = retries
        super().__init__(**kwargs)


class ApiService(RetryMixin, BaseService):
    pass


service = ApiService(name="orders", retries=5)
```

这里使用仅限关键字参数减少位置参数在多层之间串错的风险。链尾最终是 `object.__init__()`，它不接受额外参数，所以各层必须消费完自己负责的参数。

8）组合：服务“用一个仓库”，不等于服务“是一种仓库”

订单服务需要保存订单，但它本身不是仓库。与其让 `OrderService` 继承 `Repository`，不如在构造时传进一个仓库，保存为 `self.repository`。这就是 Java 中也常用的组合：需要哪个对象，就持有它、调用它。

```python
class OrderService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def create(self, order_id: str) -> None:
        self.repository.save(order_id)
```

配合鸭子类型，测试时传入内存仓库即可，不必搭建复杂继承树。

9）看到这些现象，先检查对应位置

- 在 property 的 getter 中读同名公开属性，或在 setter 中写同名公开属性：无限递归；内部改用 `_name`。
- 把实例列表写成类变量：多个实例串数据；在 `__init__` 中创建。
- 认为双下划线等于安全私有：名称修饰可绕过；敏感数据需要真正的安全机制。
- 把 `super()` 理解成固定父类：在菱形继承中调用顺序判断错误；直接打印 `type(obj).mro()`。
- 多继承中有一层忘记 `super()`：后续节点全部被截断。
- 多继承构造器签名互不兼容：优先使用仅限关键字参数和协作式 `**kwargs`。
- `__eq__` 对陌生类型直接访问字段：可能抛 `AttributeError`；先判断类型并返回 `NotImplemented`。
- `__repr__` 输出令牌或密码：调试日志发生泄漏；只保留标识和非敏感状态。
- `__len__` 返回浮点数或负数：协议不合法；始终返回非负 `int`。
- 用 `type(x) is Base` 判断多态对象：会排除子类；通常使用 `isinstance`，更 Pythonic 的场景直接依赖协议。

10）用 Java 经验快速对照

| Java 习惯 | Python 对应思路 | 关键差异 |
| :-- | :-- | :-- |
| `new User(...)` | `User(...)` | 不写 `new` |
| `this.name` | `self.name` | `self` 在定义中显式出现 |
| 构造器重载 | 默认参数、关键字参数、类方法工厂 | 不按签名重载 |
| `static` 字段 | 类变量 | 可被实例同名属性遮住 |
| getter/setter | 先用公开属性，必要时用 property | 调用方仍写属性语法 |
| `private` | `__name` 名称修饰 | 不是安全访问限制 |
| `interface` | 鸭子类型、`Protocol`、抽象基类 | 可不显式声明实现关系 |
| `toString()` | `__str__` / `__repr__` | 用户展示与调试展示分离 |
| `equals()` | `__eq__` | 陌生类型返回 `NotImplemented` |
| 类单继承、可实现多接口 | 类可多重继承 | 查找顺序由 C3 MRO 决定 |
| `super.method()` | `super().method()` | 指向 MRO 下一个实现，不一定是直接父类 |

11）动手练习：从一个小改动开始

11.1 给 `CustomQueue` 增加 `peek()`，空队列时抛 `IndexError("peek from empty queue")`，并写断言验证入队、出队、切片和迭代不互相破坏。

11.2 实现 `Temperature`。公开属性 `celsius` 必须不低于绝对零度，内部保存 `_celsius`；再提供只读属性 `fahrenheit`。验证非法输入会抛 `ValueError`，并刻意写一次递归 setter 观察堆栈后修复。

11.3 增加一个具有 `send(message)` 的 `WebhookSender`，不要继承现有发送器，让它直接通过 `notify` 的 `Sender` 类型检查。再写一个缺少 `send` 的类，观察静态检查与运行时分别怎样失败。

11.4 给菱形继承示例每层加入进入和退出日志，例如先追加 `"Left before"`，调用 `super()` 后再追加 `"Left after"`。预测并验证完整顺序。

11.5 把一个同时继承“数据库、缓存、日志”三个重量级父类的服务改为组合，通过构造器传入三个只提供所需方法的对象。比较测试时准备替代对象的代码量，以及还需不需要绕着 MRO 思考。

11.6 实现不可变值对象 `Money(amount, currency)`，要求可比较相等、可放入集合，并拒绝不同币种直接相加。先手写魔术方法，再用 `@dataclass(frozen=True)` 简化。

12）合上代码，检查自己能否讲清楚

- 能解释 `self` 为什么显式出现在方法定义中。
- 能区分类变量、实例变量以及可变类变量共享问题。
- 能写出不会递归的 property setter，并说出何时不该用 property。
- 能区分 `__str__` 与 `__repr__`，并避免敏感字段泄漏。
- 能让自定义容器支持长度、索引、切片和迭代。
- 能用鸭子类型或 `Protocol` 降低对继承关系的依赖。
- 能读懂 `Class.mro()`，知道多继承中的 `super()` 指向 MRO 下一项。
- 能说出 C3 保证的局部优先级、父类顺序和单调性。
- 能判断一个需求更适合 Mixin、普通继承还是组合。
