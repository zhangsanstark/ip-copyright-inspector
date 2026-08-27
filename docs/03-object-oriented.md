Python 面向对象：Java 后端迁移笔记

这份笔记以 Java 后端开发者已经熟悉类、接口、继承和封装为前提。重点不是把 Java 语法逐字翻译成 Python，而是理解 Python 的对象模型、协议式多态和多重继承协作方式。

先说人话：类像一张产品图纸，对象是按图纸做出的每一件产品。`self` 像贴在产品上的编号，告诉同一段方法代码“这一次正在处理哪一个对象”。Java 把这个编号藏在 `this` 里，Python 把它明确写在方法参数中。

建议先运行配套文件：

```powershell
python examples/oop_lab.py
```

对象与类的第一组差异

Python 实例化对象时不写 `new`。类对象本身可调用，调用类时通常先分配实例，再执行 `__init__` 完成初始化。

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

可以把 `self` 暂时类比成 Java 的 `this`，但它是实例方法显式声明的第一个参数。调用 `user.greeting()` 时，Python 自动把 `user` 传给 `self`，等价理解为 `User.greeting(user)`。

需要记住这些边界：

- `self` 不是关键字，只是全社区都遵守的命名约定，不应换成别的名字。
- `__init__` 负责初始化，严格说不是分配对象的构造器；真正创建实例的是 `__new__`，普通业务类几乎不需要重写它。
- Python 不支持按参数列表进行 Java 式构造器重载。通常使用默认参数、关键字参数或 `@classmethod` 工厂方法。
- 方法和类也是对象，可以赋给变量、传入函数或放进容器。

记忆口诀：创建不写 `new`，实例方法先写 `self`，多种构造用“默认参数加类方法”。

马上练一下：给 `User` 增加 `from_dict` 类方法，接收 `{"user_id": 8, "name": "Bob"}` 并返回实例。再把 `User` 换成子类调用这个工厂，确认返回的仍是子类。

用类方法表达有名字的构造方式：

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

`cls` 指向当前类。工厂方法使用 `cls(...)`，子类继承后仍能创建子类实例；硬编码 `Coordinate(...)` 会丢掉这种多态性。

类变量与实例变量

类变量写在类体中，由类和实例共同查找，可类比 Java 的 `static` 字段；实例变量通常在 `__init__` 中通过 `self.x` 创建，每个对象各有一份。

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

实例取属性时，Python 先查实例自己的属性，再沿类的 MRO 查类属性。给 `instance.attr` 赋值通常会在实例上创建同名属性，从而遮住类属性：

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

类变量最危险的用法是放可变容器。所有实例会共享同一个列表：

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

生活类比：类变量像办公室白板，所有人看到同一块；实例变量像每个人自己的笔记本。要是把购物车商品写在白板上，甲加一本书，乙的购物车也会多一本书。

记忆口诀：固定配置可放类上，每个对象自己的状态放 `self` 上，可变容器尤其要小心共享。

类型检查器可以用 `ClassVar` 明确类变量意图：

```python
from typing import ClassVar


class Job:
    category: ClassVar[str] = "batch"

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
```

访问控制与名称修饰

Python 主要依靠约定，不依靠 Java 那样严格的 `public`、`protected`、`private` 编译期限制。

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

`property`：保留属性语法并加入规则

Java 常用 getter/setter，Python 更常先暴露简单属性；只有出现校验、派生计算或兼容旧接口等需求时，再引入 `property`。

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

无限递归是 `property` 最常见、也最值得牢记的坑：

```python
class BrokenProduct:
    @property
    def price(self) -> float:
        return self.price

    @price.setter
    def price(self, value: float) -> None:
        self.price = value
```

getter 中读取 `self.price` 会再次调用 getter，setter 中写 `self.price` 会再次调用 setter，最终得到 `RecursionError`。正确原则是“对外名称触发规则，对内名称保存状态”：

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

只读派生属性只写 getter：

```python
class Rectangle:
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    @property
    def area(self) -> float:
        return self.width * self.height
```

没有校验或计算需求时直接使用公开属性即可，机械地给每个字段套 property 只是把 Java 样板代码搬到了 Python。

记忆口诀：门牌名用 `price`，仓库名用 `_price`；门口负责检查，仓库只管保存。setter 里再次写 `self.price`，就像从门口出来又立刻走回同一扇门，会一直转圈。

马上练一下：给 `Product` 增加 `stock` property，只接受非负整数。分别赋值 `3`、`-1` 和 `2.5`，为后两种情况设计清楚的异常信息。

魔术方法与对象协议

形如 `__xxx__` 的魔术方法由语言或内置函数在特定语法下调用。业务代码通常使用公开语法，例如写 `len(queue)`，而不是直接写 `queue.__len__()`。

`__str__` 与 `__repr__`

`__str__` 面向普通用户展示，`str(obj)` 和 `print(obj)` 会使用它；`__repr__` 面向开发和调试，交互式环境、容器展示及 `repr(obj)` 会使用它。理想的 `repr` 应明确、无歧义，有条件时可写成近似构造表达式。

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

`__eq__` 与 `NotImplemented`

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

参数标成 `object`，遇到不支持的类型返回 `NotImplemented`，让 Python 尝试对方的反向比较或得出 `False`；不要把 `NotImplemented` 写成字符串或异常。定义值相等性以后，Python 通常会让对象不可哈希，避免“相等对象哈希不同”破坏字典和集合。不可变值对象可考虑 `@dataclass(frozen=True)`，由标准库生成一致的 `__eq__` 和 `__hash__`。

`__call__`

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

`__len__`

`len(obj)` 转发到 `obj.__len__()`。返回值必须是非负整数，否则会抛出 `TypeError` 或 `ValueError`。如果未定义 `__bool__`，Python 还会用长度是否为零判断对象真假。

`__getitem__` 与切片

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

完整的队列协议示例

配套文件中的 `CustomQueue` 同时实现了 `__len__`、`__bool__`、`__getitem__`、`__iter__`、`__repr__` 和 `__eq__`。这样的类能自然接入 Python 语法：

```python
queue = CustomQueue(["a", "b", "c"])
print(len(queue))
print(bool(queue))
print(queue[-1])
print(queue[0:2])
print(list(queue))
```

不要为了“显得 Pythonic”实现所有魔术方法。只实现对象真正承诺的协议。例如业务对象没有自然顺序，就不该随意实现大小比较。

记忆口诀：魔术方法不是魔法，只是“语法按约定来敲门”。`print` 找展示，`repr` 找调试，`len` 找长度，方括号找索引。

马上练一下：让 `CustomQueue` 支持 `reversed(queue)`。可以实现 `__reversed__`，也可以思考已有的长度和索引协议是否足够。验证反转不会修改原队列。

鸭子类型：关注能力而不是继承关系

Java 常通过接口声明能力；Python 运行时通常只要求对象提供所需方法。“如果它像鸭子一样走路、叫起来也像鸭子，就把它当鸭子使用。”

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

运行时不要求两个类继承同一个接口。若要让类型检查器也理解，可以用 `Protocol` 表达结构化接口：

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

生活类比：充电器不关心手机来自哪家工厂，只关心插头和协议能否匹配。鸭子类型看能力，Java 接口更常看是否正式声明了关系。

记忆口诀：运行时“会做就行”，静态检查再用 `Protocol` 写清能力。

马上练一下：写一个完全不继承 `Sender` 的 `FileLikeSender`，只实现 `send` 并把消息放进列表。把它传给 `notify`，验证鸭子类型正常工作。

继承、覆盖与 `super()`

```python
class Repository:
    def save(self, value: str) -> None:
        print(f"save {value}")


class AuditedRepository(Repository):
    def save(self, value: str) -> None:
        print(f"audit {value}")
        super().save(value)
```

单继承里可以先把 `super()` 理解成调用父类实现，但多继承时更准确的定义是：从当前类之后，沿当前实例所属类的 MRO 找下一个实现。它不是“固定调用某个爸爸”。

多重继承与 MRO

Python 支持多重继承。方法解析顺序 MRO 决定属性和方法查找路径，可用 `ClassName.mro()` 或 `ClassName.__mro__` 查看。

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

C3 线性化解决什么问题

Python 使用 C3 线性化计算 MRO。日常开发不必手算完整算法，但要掌握三个结果约束：

- 子类一定排在父类之前，保留局部优先级。
- 类声明中的父类顺序尽量得到保留，例如 `Child(Left, Right)` 中 `Left` 在 `Right` 前。
- 继承层次扩展后，已有类之间的相对次序保持单调，避免同一继承关系在不同位置突然反转。

概念上，某类的 MRO 等于“该类本身”加上各父类 MRO 与父类列表的 C3 合并。合并时反复选取一个候选头元素：它不能出现在其他待合并序列的尾部。若找不到候选，说明继承顺序自相矛盾，定义类时直接抛 `TypeError`。

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

先说人话：多继承像几条排队队伍要合成一队。每条原队伍里谁在谁前不能被颠倒，子类也必须站在父类前。C3 就是在这些规则下合成一条不打架的队伍；规则互相矛盾时，Python 当场拒绝建类。

记忆口诀：查方法先看 MRO，`super()` 找队伍中的下一位；人人接力调用，链条才不会断。

马上练一下：交换为 `OrderProcessor(AuditMixin, ValidationMixin)`，先不要运行，写下你预测的 MRO 和调用日志，再用 `mro()` 验证。

协作式 `super()` 的设计规则

多继承链上的类都应合作，才能保证每一层恰好执行一次：

- 每一层都调用 `super()`，除非它明确是链条终点。
- 方法签名要兼容。初始化 Mixin 常消费自己的关键字参数，再把剩余 `**kwargs` 传下去。
- 不要在同一条链里混用 `Parent.method(self)` 和 `super().method()`，否则可能重复调用或跳过节点。
- Mixin 应小而专注，通常不独立实例化，名称常以 `Mixin` 结尾。
- 能用组合清晰表达时，优先组合；多继承更适合正交、可叠加的行为。

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

组合通常比继承更直接

Java 后端常说“组合优于继承”，Python 同样适用。若订单服务只是需要一个仓库，直接保存仓库对象比继承仓库更符合 is-a 与 has-a 的语义：

```python
class OrderService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def create(self, order_id: str) -> None:
        self.repository.save(order_id)
```

配合鸭子类型，测试时传入内存仓库即可，不必搭建复杂继承树。

常见错误与排查

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

与 Java 的快速映射

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
| 单继承接口、多接口 | 可多重继承 | 查找顺序由 C3 MRO 决定 |
| `super.method()` | `super().method()` | 指向 MRO 下一个实现，不一定是直接父类 |

动手练习

练习一：给 `CustomQueue` 增加 `peek()`，空队列时抛 `IndexError("peek from empty queue")`，并写断言验证入队、出队、切片和迭代不互相破坏。

练习二：实现 `Temperature`。公开属性 `celsius` 必须不低于绝对零度，内部保存 `_celsius`；再提供只读属性 `fahrenheit`。验证非法输入会抛 `ValueError`，并刻意写一次递归 setter 观察堆栈后修复。

练习三：增加一个具有 `send(message)` 的 `WebhookSender`，不要继承现有发送器，让它直接通过 `notify` 的 `Sender` 类型检查。再写一个缺少 `send` 的类，观察静态检查与运行时分别怎样失败。

练习四：给菱形继承示例每层加入进入和退出日志，例如先追加 `"Left before"`，调用 `super()` 后再追加 `"Left after"`。预测并验证完整顺序。

练习五：把一个同时继承“数据库、缓存、日志”三个重量级父类的服务改为组合，通过构造器注入三个小协议。比较测试替身的代码量和 MRO 复杂度。

练习六：实现不可变值对象 `Money(amount, currency)`，要求可比较相等、可放入集合，并拒绝不同币种直接相加。先手写魔术方法，再用 `@dataclass(frozen=True)` 简化。

自检清单

- 能解释 `self` 为什么显式出现在方法定义中。
- 能区分类变量、实例变量以及可变类变量共享问题。
- 能写出不会递归的 property setter，并说出何时不该用 property。
- 能区分 `__str__` 与 `__repr__`，并避免敏感字段泄漏。
- 能让自定义容器支持长度、索引、切片和迭代。
- 能用鸭子类型或 `Protocol` 降低对继承关系的依赖。
- 能读懂 `Class.mro()`，知道多继承中的 `super()` 指向 MRO 下一项。
- 能说出 C3 保证的局部优先级、父类顺序和单调性。
- 能判断一个需求更适合 Mixin、普通继承还是组合。
