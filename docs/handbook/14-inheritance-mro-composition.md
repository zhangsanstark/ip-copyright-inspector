14 继承、MRO 与组合：super 下一站到底是谁

单继承里，`super()` 看起来像“调用父类”。到了多继承，这句话就不够用了：下一站由当前对象的 MRO 决定，不一定是你在代码旁边看到的那个父类。

阅读路线：1 单继承与覆盖 → 2 菱形路线 → 3 手算 C3 → 4 协作初始化 → 5 Mixin → 6 组合取舍 → 7 练习及答案。

每个 runnable 块独立运行并自带断言。在仓库根目录运行 `python scripts/check_handbook_examples.py --chapter 14 --show-output`。

---

1）继承先解决“它也是一种什么”

1.1 继承行为，不是自动复制一份代码

```python
# runnable: hb14_single_inheritance
class User:
    def __init__(self, name: str) -> None:
        self.name = name

    def greeting(self) -> str:
        return f"hello, {self.name}"


class Admin(User):
    def greeting(self) -> str:
        base_text = super().greeting()
        return f"{base_text} [admin]"


admin = Admin("Ada")
assert isinstance(admin, Admin)
assert isinstance(admin, User)
assert admin.name == "Ada"
assert admin.greeting() == "hello, Ada [admin]"
assert [cls.__name__ for cls in Admin.__mro__] == ["Admin", "User", "object"]
print(admin.greeting())
```

Admin 没写 `__init__`，初始化时找到继承来的 User 初始化方法。self 始终是这个 Admin 实例，不会为了运行父类方法再创建一个 User。

调用 greeting 时，先找到 Admin 的实现。里面的 super 继续查找，找到 User.greeting，得到基础字符串后，Admin 再加后缀。

覆盖是子类提供同名方法，修改查找结果；不是把父类方法删除。父类本身的实例仍可以用原来的行为。

1.2 继承也带着调用约定

如果调用方把 Admin 当作 User 使用，那么 User 支持的合理调用不应突然在 Admin 中无缘无故失败。比如父类允许 `send(message)`，子类却额外要求每次传 token，又没有默认值，旧调用方就会被破坏。

能通过语法检查，只说明类定义合法，不说明继承设计合理。方法参数、返回结果、异常和副作用都属于使用者实际依赖的约定。

---

2）菱形继承：实际对象只有一个，查找路线有一条

2.1 先看可验证的路线，再谈算法

```python
# runnable: hb14_diamond_trace
events = []


class Root:
    def run(self) -> list[str]:
        events.append("enter Root")
        return ["Root"]


class Left(Root):
    def run(self) -> list[str]:
        events.append("enter Left")
        result = super().run()
        events.append("leave Left")
        return ["Left", *result]


class Right(Root):
    def run(self) -> list[str]:
        events.append("enter Right")
        result = super().run()
        events.append("leave Right")
        return ["Right", *result]


class Child(Left, Right):
    def run(self) -> list[str]:
        events.append("enter Child")
        result = super().run()
        events.append("leave Child")
        return ["Child", *result]


child = Child()
assert [cls.__name__ for cls in Child.__mro__] == [
    "Child", "Left", "Right", "Root", "object"
]
assert child.run() == ["Child", "Left", "Right", "Root"]
assert events == [
    "enter Child", "enter Left", "enter Right", "enter Root",
    "leave Right", "leave Left", "leave Child",
]
print(events)
events.clear()
assert Left().run() == ["Left", "Root"]
assert events == ["enter Left", "enter Root", "leave Left"]
```

Child 的直接父类是 Left、Right，它们共同继承 Root，所以继承关系像一个菱形。

对 Child 实例，顺序是 Child → Left → Right → Root → object。Left 里面的 `super().run()` 没有跳到 Root，而是先到 Right。

对单独的 Left 实例，顺序则是 Left → Root → object。同一份 Left.run 代码，下一站可以不同，因为实际对象类型不同。

2.2 查找的进入顺序与返回的拼接顺序

| 执行位置 | 当前在等谁 | 返回时做什么 |
| :-- | :-- | :-- |
| Child.run | 等 Left.run | 把 Child 加在返回列表前面 |
| Left.run | 等 Right.run | 把 Left 加在返回列表前面 |
| Right.run | 等 Root.run | 把 Right 加在返回列表前面 |
| Root.run | 不再往下调用 run | 返回 `["Root"]` |

Root 返回后，Right 得到 `["Root"]`，拼成 `["Right", "Root"]`。Left 接到这个列表，再加 Left。最后 Child 再加 Child。

所以“进入日志顺序”和“返回值怎么排列”是两件事。如果把 `["Left", *result]` 改成 `[*result, "Left"]`，MRO 不变，结果列表顺序却会改变。

2.3 super 记住两个信息

可以把这里的无参数 super 理解为：保留当前 self，同时从“当前方法所在类”之后继续沿 MRO 查找。

在 Left.run 中，它知道要跳过 Left，且知道 self 实际上是 Child。所以继续查 Child 的 MRO，下一站就是 Right。

显式的 `super(Left, child)` 可以帮助理解这个定位，但普通方法里优先用 `super()`，避免重命名或调整类结构时留下写死的类名。

---

3）C3 怎么把多条父类路线合成一条

3.1 先说算法要守住什么

Python 不能简单把各父类路线接在一起，那样 Root 可能重复出现，也可能把父类原本承诺的顺序倒过来。

C3 的目标可以先记为三件事：子类在父类前面；直接父类声明的相对顺序要保留；已经成立的父类先后关系，在更深子类里不能随意翻转。

这里的“顺序”指类在方法查找表中的先后，不是对象创建几个线程的运行顺序。

3.2 手算 Child(Left, Right)

已知两条父类路线：

`Left → Root → object`

`Right → Root → object`

再加直接父类列表：`Left → Right`。

Child 自己先放最前面，然后合并下面三行：

| 当前待合并列表 | 第一轮内容 |
| :-- | :-- |
| Left 的 MRO | Left, Root, object |
| Right 的 MRO | Right, Root, object |
| 直接父类顺序 | Left, Right |

合并规则：从某一行的第一个类中挑候选。只有当这个候选没有出现在任何一行的“非首位部分”里，才可以选它。选中以后，从所有以它开头的行中删掉它。

第一轮候选 Left。它没有出现在任何行的尾部，因此选 Left。剩下 `[Root, object]`、`[Right, Root, object]`、`[Right]`。

第二轮先试 Root，但 Root 位于第二行的尾部。那条路线明确要求 Right 在 Root 前面，所以现在不能提前拿 Root。

接着试 Right，它没有出现在任何尾部，因此选 Right。剩下 `[Root, object]`、`[Root, object]`。

第三轮选 Root，把两行开头的 Root 一起删掉。最后选 object。

加上最前面的 Child，得到 Child → Left → Right → Root → object。Root 只出现一次，但左右两边要求的先后关系都保留了。

3.3 用一个短程序验证这个合并过程

下面用字符串模拟候选顺序，只解释合并步骤，不打算替代 Python 的类创建实现。

```python
# runnable: hb14_c3_merge
def merge(sequences: list[list[str]]) -> list[str]:
    pending = [list(sequence) for sequence in sequences if sequence]
    result = []
    while pending:
        candidate = None
        for sequence in pending:
            head = sequence[0]
            if not any(head in other[1:] for other in pending):
                candidate = head
                break
        if candidate is None:
            raise ValueError("inconsistent ordering")
        result.append(candidate)
        for sequence in pending:
            if sequence[0] == candidate:
                sequence.pop(0)
        pending = [sequence for sequence in pending if sequence]
    return result


route = ["Child", *merge([
    ["Left", "Root", "object"],
    ["Right", "Root", "object"],
    ["Left", "Right"],
])]
assert route == ["Child", "Left", "Right", "Root", "object"]
assert merge([["A", "B"], ["A", "B"]]) == ["A", "B"]
try:
    merge([["X", "Y"], ["Y", "X"]])
except ValueError:
    pass
else:
    raise AssertionError("contradictory order was accepted")
print(route)
```

注意复制输入的那一步。函数为了合并会 pop 元素，先复制各行，才能避免把调用方提供的原列表顺便删空。这又回到了前面对象共享的知识点。

3.4 不是所有继承图都能排出合理路线

```python
# runnable: hb14_inconsistent_mro
class X:
    pass


class Y:
    pass


class A(X, Y):
    pass


class B(Y, X):
    pass


failed = False
try:
    class Broken(A, B):
        pass
except TypeError:
    failed = True
assert failed
assert A.__mro__.index(X) < A.__mro__.index(Y)
assert B.__mro__.index(Y) < B.__mro__.index(X)
print("inconsistent MRO rejected")
```

A 要求 X 在 Y 前，B 要求 Y 在 X 前。Broken 同时继承两者时，不存在同时满足两条要求的单一路线。

错误发生在执行类定义时，还没有开始创建 Broken 实例。解决办法是调整设计，不是等到某个方法调用时再手动挑一个父类绕过去。

---

4）协作初始化：每一层拿走自己负责的参数

4.1 参数要像接力一样继续传下去

```python
# runnable: hb14_cooperative_init
class Named:
    def __init__(self, *, name: str, **kwargs) -> None:
        if not name.strip():
            raise ValueError("name must not be blank")
        self.name = name.strip()
        super().__init__(**kwargs)


class RetryMixin:
    def __init__(self, *, retries: int = 0, **kwargs) -> None:
        if type(retries) is not int or retries < 0:
            raise ValueError("retries must be a non-negative integer")
        self.retries = retries
        super().__init__(**kwargs)


class Service(RetryMixin, Named):
    pass


service = Service(name=" orders ", retries=2)
assert service.name == "orders"
assert service.retries == 2
assert [cls.__name__ for cls in Service.__mro__] == [
    "Service", "RetryMixin", "Named", "object"
]
try:
    Service(name="orders", retryes=2)
except TypeError:
    pass
else:
    raise AssertionError("unknown argument was silently ignored")
print(service.name, service.retries)
```

Service 没有自己的初始化实现，所以首先找到 RetryMixin。retries 被它接住，name 留在 kwargs 中。

RetryMixin 通过 super 把 name 交给 Named。Named 接住 name，剩余 kwargs 应为空，再交给 object 的初始化。

故意拼错 `retryes` 后，没有一层认识这个参数，它会继续往下传，最终报 TypeError。不要为了“兼容”把剩余 kwargs 悄悄丢掉，那会把拼写错误伪装成创建成功。

4.2 只在大家遵守同一套规则时合作

协作式多继承通常要求：参与链条的方法签名兼容；每层处理自己的参数；通过 super 继续传递；同一次操作不要重复调用下一层。

写死 `Root.__init__(self)` 会绕过 MRO 中间的其他类。在菱形里分别手动调用两个父类，还可能重复执行共同祖先的初始化。

不是所有第三方类都按协作式多继承设计。遇到不兼容的父类，优先考虑组合或适配，而不是强行把它们塞进一条初始化链。

---

5）Mixin：补一种能力，不抢业务主体

5.1 一个小能力可以改变一层处理

```python
# runnable: hb14_mixin_chain
class BaseFormatter:
    def format(self, text: str) -> str:
        return text


class StripMixin:
    def format(self, text: str) -> str:
        return super().format(text.strip())


class BracketMixin:
    def format(self, text: str) -> str:
        return f"[{super().format(text)}]"


class CleanFormatter(StripMixin, BracketMixin, BaseFormatter):
    pass


formatter = CleanFormatter()
assert formatter.format(" hello ") == "[hello]"
assert [cls.__name__ for cls in CleanFormatter.__mro__] == [
    "CleanFormatter", "StripMixin", "BracketMixin", "BaseFormatter", "object"
]
print(formatter.format(" hello "))
```

StripMixin 先处理输入，把空白去掉再传下去。BracketMixin 则等下一层返回后，再处理输出，加上方括号。

阅读这种链条时，要分别标出“调用 super 之前做什么”和“之后做什么”。只是记住父类从左到右，还不够预测最后字符串。

Mixin 是约定，不是 Python 关键字。它应提供小而明确的能力，说明依赖哪些方法或属性。一个 Mixin 如果偷偷需要十几个字段、控制整个业务流程，就很难安全复用。

5.2 父类顺序是接口的一部分

调整 Mixin 顺序可能改变结果、校验先后和异常位置。不能把父类列表当成一组无序标签。变更时应同时查看 `Class.__mro__` 和代表性行为测试。

---

6）组合：把需要的对象交进来

6.1 “拥有一个”通常比“是一种”更适合组合

OrderService 需要一个 Repository，但它不是一种 Repository。让服务继承数据库实现，会把存储细节和业务身份绑在一起。

```python
# runnable: hb14_composition
class MemoryRepository:
    def __init__(self) -> None:
        self.rows = {}

    def save(self, order_id: str, amount: int) -> None:
        self.rows[order_id] = amount


class OrderService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def create(self, order_id: str, amount: int) -> str:
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.repository.save(order_id, amount)
        return order_id


repository = MemoryRepository()
service = OrderService(repository)
assert service.create("A-1", 100) == "A-1"
assert repository.rows == {"A-1": 100}
try:
    service.create("A-2", 0)
except ValueError:
    pass
else:
    raise AssertionError("invalid amount was accepted")
assert repository.rows == {"A-1": 100}
print(repository.rows)
```

OrderService 只调用 repository.save，不关心内部是字典还是别的实现。测试时传入内存对象，不需要启动数据库。

这和 Java 构造器注入很接近，只是示例不需要容器框架。对象创建者负责把依赖交进来，业务类负责使用依赖。

6.2 选择时问三个具体问题

第一，调用方能否自然地把子类当父类使用？如果不能，继承关系可能只是为了省几行代码。

第二，变化的是一个可替换部件，还是对象本身的类型身份？输出格式、存储方式、重试策略这类部件，组合往往更清楚。

第三，为理解一次方法调用，要不要横跨很多父类？如果 MRO 已成为日常排错负担，把其中部分能力改成显式调用的协作对象，通常更容易维护。

组合不是绝对优于继承。稳定的类型层次、框架规定的扩展点、小型协作 Mixin 都可以合理使用继承。关键是不要为了复用就跳过“这关系是否成立”的判断。

---

7）练习与完整参考答案

7.1 练习一：同一份方法，换一个对象路线就变了

预测 Left().run 与 Child().run 的结果，再运行验证。要求实现里不写死 Root.run。

```python
# runnable: hb14_exercise_route
class Root:
    def run(self):
        return ["Root"]


class Left(Root):
    def run(self):
        return ["Left", *super().run()]


class Right(Root):
    def run(self):
        return ["Right", *super().run()]


class Child(Left, Right):
    pass


assert Left().run() == ["Left", "Root"]
assert Child().run() == ["Left", "Right", "Root"]
assert Child.__mro__.index(Left) < Child.__mro__.index(Right)
print(Left().run(), Child().run())
```

Child 没实现 run，所以结果中没有 Child 标签，但查找表里仍然有 Child。方法返回什么，不等于查找表完整列了什么。

7.2 练习二：初始化链增加超时配置

创建 TimeoutMixin 和 Named，最终 Client 能接收 name 与 timeout。timeout 必须是正数；默认 timeout 为 3。

```python
# runnable: hb14_exercise_init
import math


class Named:
    def __init__(self, *, name, **kwargs):
        self.name = name
        super().__init__(**kwargs)


class TimeoutMixin:
    def __init__(self, *, timeout=3.0, **kwargs):
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise TypeError("timeout must be numeric")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        self.timeout = float(timeout)
        super().__init__(**kwargs)


class Client(TimeoutMixin, Named):
    pass


client = Client(name="search", timeout=2)
assert (client.name, client.timeout) == ("search", 2.0)
assert Client(name="default").timeout == 3.0
try:
    Client(name="bad", timeout=0)
except ValueError:
    pass
else:
    raise AssertionError("zero timeout was accepted")
print(client.name, client.timeout)
```

每层只消费自己负责的关键字参数。这里没有真的发送网络请求，timeout 只是经过校验的配置字段。

7.3 练习三：用组合替换继承式输出

Report 接收 formatter，render 接收字符串并返回 formatter 的结果。提供纯文本和大写两个格式器，不让 Report 继承它们。

```python
# runnable: hb14_exercise_composition
class PlainFormatter:
    def format(self, text):
        return text


class UpperFormatter:
    def format(self, text):
        return text.upper()


class Report:
    def __init__(self, formatter):
        self.formatter = formatter

    def render(self, text):
        return self.formatter.format(text)


plain = Report(PlainFormatter())
upper = Report(UpperFormatter())
assert plain.render("ready") == "ready"
assert upper.render("ready") == "READY"
plain.formatter = UpperFormatter()
assert plain.render("changed") == "CHANGED"
print(plain.render("changed"))
```

最后替换的是 Report 持有的部件，不是动态更改 Report 的父类。这个区别能帮你判断什么时候组合更直接。

---

8）回看与资料

看见 super，先找实际对象类型，再看该类型的 MRO，最后从当前方法所在类之后继续查。看见多继承初始化，先画参数由谁消费，再检查是否完整传到了链条末端。

官方参考：[类与继承](https://docs.python.org/3.11/tutorial/classes.html)、[super](https://docs.python.org/3.11/library/functions.html#super)、[MRO 说明](https://docs.python.org/3/howto/mro.html)、[对象模型](https://docs.python.org/3.11/reference/datamodel.html)。
