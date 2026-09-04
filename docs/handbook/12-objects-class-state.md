12 对象、类与状态：这一次操作的是谁

读这一章时，先别急着把 Python 类翻译成 Java 类。抓住两个问题就够了：这份数据放在哪个对象上，这个方法这次拿到了谁？`self`、类变量、工厂方法，都是围绕这两个问题展开的。

阅读路线：1 创建实例 → 2 self 与方法绑定 → 3 类和实例各自存什么 → 4 三种方法 → 5 下划线约定 → 6 对象模型 → 7 练习及答案。

本章代码只用标准库。每个标为 runnable 的代码块都能独立运行，包含自己的类定义与断言。在仓库根目录运行 `python scripts/check_handbook_examples.py --chapter 12 --show-output`，也可以把某个完整代码块存成 `.py` 后运行。

---

1）一个对象怎样来到你手里

1.1 从最常见的创建方式看起

Java 写 `new User(7, "Ada")`，Python 写 `User(7, "Ada")`。少掉的是 `new` 这个关键字，不是少掉了对象创建过程。

```python
# runnable: hb12_create_user
class User:
    def __init__(self, user_id: int, name: str = "anonymous") -> None:
        self.user_id = user_id
        self.name = name

    def greeting(self) -> str:
        return f"hello, {self.name}"


first = User(7, "Ada")
second = User(8)
assert first.user_id == 7
assert first.greeting() == "hello, Ada"
assert second.greeting() == "hello, anonymous"
assert first is not second
second.name = "Bob"
assert first.name == "Ada"
print(first.greeting(), second.greeting())
```

跟着 `first = User(7, "Ada")` 走一遍：

第一步，类调用流程创建一个 User 实例。此时还没有完成业务字段的初始化。

第二步，把这个实例交给 `__init__` 的 `self`，把 7 交给 `user_id`，把 Ada 交给 `name`。

第三步，`self.user_id = user_id` 在实例上保存属性。左边是对象的字段，右边是当前方法收到的参数，虽然同名，却不是同一个位置。

第四步，初始化正常结束，整个 `User(...)` 表达式得到这个实例，`first` 成为指向它的变量。

所以 `__init__` 里面不要 `return self`。它负责填数据，返回值必须是 None；把实例交给外面的变量是类调用流程的工作。

1.2 `__new__` 创建，`__init__` 初始化

普通业务类只需要写 `__init__`。下面特意把 `__new__` 也写出来，是为了看清它们的顺序，不是建议每个类照抄。

```python
# runnable: hb12_new_init_trace
events = []


class Ticket:
    def __new__(cls, number: int):
        events.append(("new", cls.__name__, number))
        instance = super().__new__(cls)
        return instance

    def __init__(self, number: int) -> None:
        events.append(("init", type(self).__name__, number))
        self.number = number


ticket = Ticket(42)
assert events == [("new", "Ticket", 42), ("init", "Ticket", 42)]
assert ticket.number == 42
assert isinstance(ticket, Ticket)
print(events)
```

`__new__` 先收到类 `cls`，因为这时还没有可以拿来初始化的实例。`super().__new__(cls)` 创建实例，随后返回它。

在这种正常路径下，`__init__` 收到刚才的实例。它没有再创建一个 Ticket，而是给同一个 Ticket 添加 number。

更精确的边界是：如果自定义 `__new__` 返回的不是这个类的实例，后面的初始化流程会不同，不会照常调用这个类的 `__init__`。这属于定制对象创建的特殊场景，不能把“调用任何类都必然执行其 `__init__`”当成绝对规则。

重写 `__new__` 常见于不可变类型的定制或底层框架。对普通订单、人员、配置对象，先用默认创建过程就好。

1.3 初始化报错，不是返回一个“半合格结果”

如果 `__init__` 校验时抛异常，`User(...)` 表达式也会抛异常，外面的赋值不会正常完成。类内部可能已经执行了一部分语句，因此有副作用的操作应尽量放在校验通过之后。

例如“创建成功计数加一”，适合放在所有必要校验之后。不要先计数，再发现名字为空抛错，最后让计数和实际成功数量对不上。

---

2）self 不神秘，它就是这次方法操作的对象

2.1 为什么定义有 self，调用却不写

`first.greeting()` 会把 first 自动交给实例方法。对这个普通方法，可以把效果理解成 `User.greeting(first)`。

```python
# runnable: hb12_bound_method
class Counter:
    def __init__(self, value: int = 0) -> None:
        self.value = value

    def add(self, amount: int) -> int:
        self.value += amount
        return self.value


left = Counter(10)
right = Counter(100)
saved_method = left.add
assert saved_method.__self__ is left
assert saved_method.__func__ is Counter.add
assert saved_method(2) == 12
assert Counter.add(right, 3) == 103
assert left.value == 12
assert right.value == 103
print(left.value, right.value)
```

`saved_method` 不只是拿到一份函数代码，还记住了“这份代码要操作 left”。所以稍后调用 `saved_method(2)`，Python 仍把 left 传给 self。

`Counter.add(right, 3)` 是通过类取出函数再显式传对象。业务代码通常写 `right.add(3)`，前一种写法主要用于理解方法绑定。

`self` 不是关键字，改成别的名字也能运行，但会让所有读代码的人困惑。像 Java 的 this 一样理解它，但按 Python 的约定把它显式写出来。

2.2 参数本身不会自动变成属性

在 `__init__(self, name)` 里，仅仅收到 name，不会自动让对象拥有 `.name`。必须有 `self.name = name` 这样的保存步骤。

同样，方法里的 `count = 0` 是局部变量；`self.count = 0` 是实例状态。方法结束以后，局部变量名不再供外部使用，实例状态则可以供下次方法调用读取。

判断一个值是否需要放到 self 上，可以问：“下次调用另一个方法时，我还需不需要这份值？”需要长期跟着对象走的状态才适合成为属性，不必把每个临时计算都塞进 self。

---

3）类变量和实例变量：看起来同名，保存位置不同

3.1 实例找不到普通属性，才会继续找类

以下规则先限定为普通属性；下一章的 property 等描述符有更具体的优先级。

```python
# runnable: hb12_class_shadow
class Feature:
    enabled = True


first = Feature()
second = Feature()
assert first.__dict__ == {}
assert first.enabled is True
first.enabled = False
assert first.__dict__ == {"enabled": False}
assert (first.enabled, second.enabled, Feature.enabled) == (False, True, True)
Feature.enabled = False
assert second.enabled is False
del first.enabled
assert first.__dict__ == {}
assert first.enabled is False
print(first.enabled, second.enabled, Feature.enabled)
```

起初 first 没有自己的 enabled，读取时找到 `Feature.enabled`。执行 `first.enabled = False` 后，first 自己保存了一份，盖住了类上的默认值。

second 没有自己的 enabled，因此修改 `Feature.enabled` 后，second 下次读取能看到新的类值。不是 Python 把改动逐个复制到了所有实例，而是 second 每次仍沿查找路径读类上的值。

`del first.enabled` 删除的是 first 自己的属性。类属性没有被删，所以下次读取又能找到类上的默认值。

3.2 共享列表为什么会把两个对象串到一起

```python
# runnable: hb12_mutable_class_state
class BadCart:
    items = []


bad_a = BadCart()
bad_b = BadCart()
bad_a.items.append("book")
assert bad_b.items == ["book"]
assert bad_a.items is bad_b.items
assert "items" not in bad_a.__dict__


class Cart:
    def __init__(self) -> None:
        self.items = []


good_a = Cart()
good_b = Cart()
good_a.items.append("book")
assert good_a.items == ["book"]
assert good_b.items == []
assert good_a.items is not good_b.items
print(bad_b.items, good_b.items)
```

`bad_a.items.append(...)` 先查找到类上的列表，再修改这个列表本身。它没有给 bad_a 创建一个新列表，也没有执行属性重新赋值。

这和 `first.enabled = False` 不矛盾：一个是修改已有对象，一个是把属性绑定到另一个值。判断共享问题时，先看有没有创建新容器，再看谁持有它。

正确版本每次进入 `__init__` 都执行一次 `[]`，所以两辆购物车各有一个列表。

3.3 计数器究竟统计哪一类对象

```python
# runnable: hb12_class_counter
class Session:
    created = 0

    def __init__(self) -> None:
        type(self).created += 1


class SpecialSession(Session):
    pass


Session()
assert Session.created == 1
SpecialSession()
assert SpecialSession.created == 2
assert Session.created == 1
SpecialSession()
assert SpecialSession.created == 3
assert "created" in SpecialSession.__dict__
print(Session.created, SpecialSession.created)
```

这个结果容易出乎意料：子类第一次加一时，先读到继承来的 1，再把 2 保存到子类自己的 created 中。从此子类有自己的值。

如果要统计所有 Session 及其子类的统一总量，应明确修改 `Session.created`。如果每个子类都要从 0 开始各算各的，也应明确初始化每个子类的计数。`type(self)` 只表示实际类型，不会自动替你选择业务统计口径。

而 `self.created += 1` 对这个整数属性会写到实例上，通常不是“全体实例累计”的意思。多线程共享计数还需要同步，类变量本身不附带线程安全。

---

4）实例方法、类方法、静态方法怎么选

4.1 不看名字，先看方法需要谁

| 形式 | 自动收到的第一个对象 | 适合处理什么 |
| :-- | :-- | :-- |
| 普通实例方法 | self，当前实例 | 修改某人的名字、读取某张订单 |
| `@classmethod` | cls，调用入口的类 | 创建实例、按当前类选择配置 |
| `@staticmethod` | 不自动接收 self 或 cls | 与类主题相关、但不需要对象状态的计算 |

```python
# runnable: hb12_method_kinds
class Coordinate:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def moved(self, dx: float, dy: float):
        return type(self)(self.x + dx, self.y + dy)

    @classmethod
    def from_text(cls, text: str):
        x_text, y_text = text.split(",")
        return cls(float(x_text), float(y_text))

    @staticmethod
    def is_origin(x: float, y: float) -> bool:
        return x == 0 and y == 0


class ScreenCoordinate(Coordinate):
    pass


point = ScreenCoordinate.from_text("3,4")
assert type(point) is ScreenCoordinate
assert (point.x, point.y) == (3.0, 4.0)
next_point = point.moved(1, 2)
assert type(next_point) is ScreenCoordinate
assert (next_point.x, next_point.y) == (4.0, 6.0)
assert (point.x, point.y) == (3.0, 4.0)
assert Coordinate.is_origin(0, 0)
print(type(point).__name__, next_point.x, next_point.y)
```

`from_text` 不需要一个现成的坐标，它就是负责创建坐标的入口。调用 `ScreenCoordinate.from_text` 时，cls 是 ScreenCoordinate，所以 `cls(...)` 创建的是子类。

如果里面写死 `Coordinate(...)`，继承来的工厂每次都会创建父类。这里用 cls 不是为了缩短名字，而是为了保留调用者选择的类型。

`moved` 需要读取当前坐标，因此是实例方法。示例返回新对象，不修改原对象；这是接口选择，不是所有叫 moved 的方法都天然如此。

`is_origin` 只看两个输入数字，完全不依赖对象状态。它可以是静态方法，也可以放在模块里作为普通函数。Python 没有“所有函数都必须属于某个工具类”的要求。

4.2 没有 Java 式的同名重载

在同一个类体里写两次同名 `__init__`，后面的定义会覆盖前面的，不会按参数个数自动选择。常见替代是默认参数、仅限关键字参数，以及 `from_text`、`from_dict` 这样的具名工厂。

返回 `cls(...)` 也有契约：子类构造参数要能兼容这个工厂传入的值。如果子类额外要求一个无默认值参数，就应重写工厂或重新设计接口，不是 cls 会自动猜出参数。

---

5）下划线表达使用约定，不是访问权限开关

公开的 `name` 是调用方可以依赖的接口。`_name` 表示内部细节，外部技术上能读写，但不应把它当稳定契约。

类体中的 `__name` 会进行名称修饰，主要是防止子类无意间撞名。它不等于 Java 的 private，更不等于保密存储。

```python
# runnable: hb12_name_mangling
class Base:
    def __init__(self) -> None:
        self.__value = "base"

    def base_value(self) -> str:
        return self.__value


class Child(Base):
    def __init__(self) -> None:
        super().__init__()
        self.__value = "child"

    def child_value(self) -> str:
        return self.__value


obj = Child()
assert obj.base_value() == "base"
assert obj.child_value() == "child"
assert obj.__dict__ == {"_Base__value": "base", "_Child__value": "child"}
print(obj.__dict__)
```

两个方法虽然都写 `self.__value`，但所在类不同，最终名字不同，因此没有互相覆盖。

`__len__` 这种两边都有双下划线的名字另有用途，是 Python 的特殊方法协议。不要为了“显得私有”自行发明 `__password__`，那不是名称修饰的正确使用方式。

---

6）把对象模型和 Java 经验接起来

6.1 类本身也是对象

类可以赋给变量、传给函数、放进字典。`factory = User` 保存的是类对象，随后 `factory(...)` 仍可以创建实例。

`type(instance)` 得到实例所属的类。普通类通常由 type 创建，因此 `type(User)` 通常是 type。知道这一层关系就足够理解 cls；暂时不需要为了业务类去定制元类。

6.2 `__dict__` 是观察窗口，不是所有对象的统一存储保证

本章普通实例有 `__dict__`，方便查看自己保存的属性。但使用 slots 的类和不少内置对象没有实例字典。不能写一个通用函数就假定每个对象都有 `obj.__dict__`。

6.3 相似写法背后不同的习惯

Java 的 this 对应 self 的主要用途，但 Python 把它放进方法签名。Java 的 static 字段可以帮助理解类变量，但 Python 实例还能遮蔽普通类属性，子类也可能建立自己的同名属性。

Java 的访问修饰符是语言机制，Python 下划线更多是约定及名称处理。Java 常用构造重载，Python 倾向用默认参数和具名工厂。

对象的生命周期也不要拿来安排关键资源的释放。文件、锁、数据库连接应通过上下文管理器或显式关闭管理，不要寄希望于对象“差不多该被回收了”。

---

7）练习与完整参考答案

7.1 练习一：名字只属于当前人

实现 Person，保存名字和 tags。创建两个人，给第一人添加标签，第二人的 tags 仍为空。额外验证传入的标签列表随后被调用方修改时，不影响对象内部列表。

参考答案：初始化时复制传入容器，解决的是列表结构共享；如果标签本身换成可变对象，这仍然只是浅拷贝。

```python
# runnable: hb12_exercise_person
class Person:
    def __init__(self, name: str, tags=None) -> None:
        self.name = name
        self.tags = list(tags) if tags is not None else []


source = ["reader"]
first = Person("Ada", source)
second = Person("Bob")
first.tags.append("writer")
source.append("outside")
assert first.tags == ["reader", "writer"]
assert second.tags == []
assert source == ["reader", "outside"]
print(first.tags, second.tags)
```

7.2 练习二：成功创建才增加总数

实现 Job，空白名字创建失败；父类和子类统一累计成功次数。创建一次 Job、一次子类，再尝试一次非法名字，最终总数为 2。

参考答案：明确更新 Job，而不是依靠 `type(self)` 猜统计范围；校验放在计数之前。这里只讨论单线程调用。

```python
# runnable: hb12_exercise_creation_count
class Job:
    created = 0

    def __init__(self, name: str) -> None:
        normalized = name.strip()
        if not normalized:
            raise ValueError("name must not be blank")
        self.name = normalized
        Job.created += 1


class BatchJob(Job):
    pass


first = Job(" one ")
second = BatchJob("two")
try:
    Job("   ")
except ValueError:
    pass
else:
    raise AssertionError("blank name was accepted")
assert Job.created == 2
assert first.name == "one"
assert second.name == "two"
print(Job.created)
```

7.3 练习三：从字典创建实际子类

实现 `User.from_dict`，把 user_id 和 name 交给构造方法。Admin 继承它，调用后对象应是 Admin，而不是 User。

参考答案：工厂不复制初始化逻辑，只负责拆输入，必要校验仍留在统一入口。下面特意用 `type(...) is int` 排除 True，因为 bool 是 int 的子类。

```python
# runnable: hb12_exercise_factory
class User:
    def __init__(self, user_id: int, name: str) -> None:
        if type(user_id) is not int or user_id <= 0:
            raise ValueError("user_id must be a positive integer")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be non-blank text")
        self.user_id = user_id
        self.name = name.strip()

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["user_id"], data["name"])


class Admin(User):
    pass


user = Admin.from_dict({"user_id": 8, "name": " Bob "})
assert type(user) is Admin
assert (user.user_id, user.name) == (8, "Bob")
print(type(user).__name__, user.name)
```

字典缺少字段会抛 KeyError，字段值非法会抛 ValueError。这里没有把所有问题都变成“返回 None”，调用方才能分清缺字段与值不合规则。

---

8）回看与资料

合上代码，试着解释：`__new__` 和 `__init__` 分别接到什么；`self.x = value` 和 `self.x.append(value)` 为什么可能产生不同的共享效果；类方法为什么写 cls 而不是写死类名。

如果能把这三个问题说清楚，后面的 property、魔术方法和继承就有了稳定的基础。

官方参考：[类教程](https://docs.python.org/3.11/tutorial/classes.html)、[对象创建与数据模型](https://docs.python.org/3.11/reference/datamodel.html)、[classmethod 与 staticmethod](https://docs.python.org/3.11/library/functions.html)。
