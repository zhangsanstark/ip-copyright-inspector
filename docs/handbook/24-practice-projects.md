24 四个完整项目：从需求走到实现、验证与扩展

这一章把前面分散的语法放回完整流程。每个项目都先说清楚接受什么输入、内部保存什么、什么时候修改状态，再给可以单独运行的完整实现。代码中的 assert 是可执行的要求，不是装饰。

阅读路线：1 人员记录管理 → 2 CustomQueue → 3 Account 属性规则 → 4 RequestLimiter → 5 综合检查。

所有例子只用标准库，不启动数据库或网络服务，不读取真实账号资料。每个 runnable 代码块独立运行；主实现与扩展答案互不依赖。运行 `python scripts/check_handbook_examples.py --chapter 24 --show-output`。

示例使用脚本化操作，而不是无限等待 input 的交互菜单。这样一运行就能看到完整场景和测试结果；以后要加菜单，只需在最外层读取输入，再调用现有方法，不要把业务校验复制进菜单。

---

1）项目一：人员记录管理

1.1 先把需求写到能判断对错

一条记录包含正整数编号、非空姓名、0 到 150 的整数年龄。姓名保存前去掉两侧空白，编号不能重复。

系统支持新增、按编号查询、修改姓名或年龄、删除、列出全部、按姓名片段搜索。全部列表按编号排序，搜索忽略英文字母大小写。

错误要能区分：字段值非法是 ValueError，字段类型不对是 TypeError，编号不存在是 KeyError。不要一律返回 False，否则调用方不知道该纠正哪一项。

修改失败时，原记录必须保持不变。查询返回的记录也不应被调用方随意改坏，从而绕过管理器规则。

1.2 数据和操作怎样拆

Person 负责“一条记录是否合格”。Registry 负责“多条记录怎样按编号组织”。

内部用 `dict[int, Person]`，按编号查找很直接，不用每次遍历整个列表。Person 用冻结 dataclass，外部不能通过普通赋值直接修改字段；修改时创建一条新的合格记录，再替换旧记录。

这类似 Java 里用不可变 DTO 表达数据，用一个 service 管理增删改查，只是这里没有数据库层。

dataclass 会根据字段生成初始化、展示和相等比较等常用方法。生成的初始化在填好字段后调用 `__post_init__`，因此把单条记录的补充检查放在那里。frozen 阻止普通字段赋值；初始化阶段规范化姓名时使用 `object.__setattr__`，是在类自己控制的步骤中完成最后整理，不是让调用方绕过规则的接口。

1.3 完整实现

```python
# runnable: hb24_person_registry
from dataclasses import dataclass, replace, FrozenInstanceError


def check_id(person_id: int) -> None:
    if type(person_id) is not int:
        raise TypeError("person_id must be an integer")
    if person_id <= 0:
        raise ValueError("person_id must be positive")


@dataclass(frozen=True)
class Person:
    person_id: int
    name: str
    age: int

    def __post_init__(self) -> None:
        check_id(self.person_id)
        if not isinstance(self.name, str):
            raise TypeError("name must be text")
        normalized = self.name.strip()
        if not normalized:
            raise ValueError("name must not be blank")
        if type(self.age) is not int:
            raise TypeError("age must be an integer")
        if not 0 <= self.age <= 150:
            raise ValueError("age must be between 0 and 150")
        object.__setattr__(self, "name", normalized)


class Registry:
    def __init__(self) -> None:
        self._people: dict[int, Person] = {}

    def add(self, person_id: int, name: str, age: int) -> Person:
        person = Person(person_id, name, age)
        if person.person_id in self._people:
            raise ValueError("person_id already exists")
        self._people[person.person_id] = person
        return person

    def get(self, person_id: int) -> Person:
        check_id(person_id)
        return self._people[person_id]

    def update(self, person_id: int, *, name=None, age=None) -> Person:
        old = self.get(person_id)
        new = replace(
            old,
            name=old.name if name is None else name,
            age=old.age if age is None else age,
        )
        self._people[person_id] = new
        return new

    def remove(self, person_id: int) -> Person:
        check_id(person_id)
        return self._people.pop(person_id)

    def all(self) -> list[Person]:
        return [self._people[key] for key in sorted(self._people)]

    def search(self, text: str) -> list[Person]:
        if not isinstance(text, str):
            raise TypeError("search text must be text")
        needle = text.strip().casefold()
        return [person for person in self.all() if needle in person.name.casefold()]

    def __len__(self) -> int:
        return len(self._people)


def expect_error(kind, action) -> None:
    try:
        action()
    except kind:
        return
    raise AssertionError(f"expected {kind.__name__}")


registry = Registry()
ada = registry.add(2, " Ada ", 28)
bob = registry.add(1, "Bob", 31)
assert ada.name == "Ada"
assert registry.all() == [bob, ada]
assert registry.search(" AD ") == [ada]
assert registry.search("") == [bob, ada]

updated = registry.update(2, age=29)
assert updated.age == 29
assert ada.age == 28
assert registry.get(2) is updated
assert len(registry) == 2

expect_error(ValueError, lambda: registry.add(2, "Other", 20))
expect_error(ValueError, lambda: registry.add(3, " ", 20))
expect_error(TypeError, lambda: registry.add(True, "Flag", 20))
expect_error(TypeError, lambda: registry.update(2, age=2.5))
expect_error(ValueError, lambda: registry.update(2, age=-1))
assert registry.get(2) is updated
expect_error(KeyError, lambda: registry.get(999))
expect_error(FrozenInstanceError, lambda: setattr(updated, "age", -1))

snapshot = registry.all()
snapshot.clear()
assert len(registry) == 2
assert registry.remove(1) == bob
assert registry.all() == [updated]
expect_error(KeyError, lambda: registry.remove(1))
print(registry.all())
```

1.4 跟着一次修改走到底

执行 `registry.update(2, age=29)`，先通过 get 找到编号 2 的旧 Person。name 没传，因此继续使用旧姓名；age 传了 29，因此用新年龄。

replace 不是随便改旧对象，而是根据旧字段和指定变更新建 Person，新对象仍执行 `__post_init__` 校验。校验成功后，才用它替换字典中的值。

因此上面保存的变量 ada 仍指向旧记录，年龄仍为 28；registry 现在指向新记录，年龄为 29。这是不可变记录的快照效果，不是修改没生效。

如果 age=-1，构造新记录时就失败，还没走到字典赋值，所以旧记录保持不变。把保存步骤放在校验之后，比“先改完，错了再尝试恢复”更容易保证正确。

这里约定 name=None、age=None 表示不修改，而不是把字段改成 None。如果将来业务允许 None 成为有效字段值，就应使用专门的缺省哨兵区分“没传”和“传了 None”。

1.5 为什么查询结果不会顺手改坏内部结构

all 返回新列表，所以调用方清空它，不会清空 Registry 内部字典。列表里的 Person 是冻结记录，普通字段赋值被阻止。

这不是安全沙箱。刻意使用底层方式仍可能绕过冻结规则；目的只是让正常调用者不容易误改数据。如果记录中放入可变嵌套容器，还要继续分析共享问题，frozen 并不自动递归冻结。

1.6 边界测试怎样对应需求

重复编号测试保证不能覆盖已有记录；空姓名和非法年龄保证新数据合格；失败修改后对象身份仍相同，证明没有先写坏再报错；列表副本测试保证外部容器修改不会影响内部组织。

搜索空字符串匹配全部，是因为空串属于任意字符串的子串。这是本项目明确接受的规则；如果界面不希望这样，可在 search 中单独拒绝空搜索词。

1.7 扩展练习：JSON 往返与整批校验

要求把人员列表转成 JSON 字符串，再读回。导入过程中任何一条非法或编号重复，整个导入失败，不返回半份结果。不接触磁盘，先把数据转换规则验证清楚。

下面是独立可运行的导入导出模块。它保留同样字段规则，用局部集合和列表构建候选结果，全部通过后才返回；将它接到 Registry 时，也应先构建完整候选，再替换状态。

```python
# runnable: hb24_person_json_answer
from dataclasses import dataclass, asdict
import json


@dataclass(frozen=True)
class Person:
    person_id: int
    name: str
    age: int

    def __post_init__(self) -> None:
        if type(self.person_id) is not int or self.person_id <= 0:
            raise ValueError("invalid person_id")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("invalid name")
        if type(self.age) is not int or not 0 <= self.age <= 150:
            raise ValueError("invalid age")
        object.__setattr__(self, "name", self.name.strip())


def dump_people(people: list[Person]) -> str:
    return json.dumps([asdict(person) for person in people], ensure_ascii=False)


def load_people(text: str) -> list[Person]:
    rows = json.loads(text)
    if not isinstance(rows, list):
        raise ValueError("top-level JSON must be a list")
    people = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"person_id", "name", "age"}:
            raise ValueError("each record must contain exactly the expected fields")
        person = Person(**row)
        if person.person_id in seen:
            raise ValueError("duplicate person_id")
        seen.add(person.person_id)
        people.append(person)
    return sorted(people, key=lambda person: person.person_id)


original = [Person(2, "小明", 20), Person(1, "Ada", 28)]
text = dump_people(original)
restored = load_people(text)
assert restored == [original[1], original[0]]
assert "小明" in text
bad_inputs = [
    '{}',
    '[{"person_id": 1, "name": "Ada", "age": -1}]',
    '[{"person_id": 1, "name": "Ada", "age": 20},'
    ' {"person_id": 1, "name": "Bob", "age": 30}]',
]
for bad in bad_inputs:
    try:
        load_people(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid import was accepted")
assert original == [Person(2, "小明", 20), Person(1, "Ada", 28)]
print(restored)
```

这里严格拒绝额外字段，避免调用方以为某个字段被保存了，实际上却被悄悄忽略。是否允许额外字段是接口选择，必须在需求里说明。

还可以继续扩展分页与年龄筛选。先写出“页码从 0 还是 1 开始、空页返回什么、排序怎样稳定”，再写循环，避免接口行为直到测试时才临时决定。

---

2）项目二：CustomQueue，自定义一个行为清楚的队列

2.1 先定义“先进先出”之外的规则

enqueue 从尾部加入，dequeue 从头部取走，peek 只看头部不移除。空队列取出或查看抛 IndexError。

支持 len、bool、索引、切片、迭代、repr 和内容相等比较。切片返回普通 list，迭代使用创建迭代器时的结构快照。

可选 capacity 限制容量，创建后只读，满了再加入抛 OverflowError。extend 一次加入多项时，要么全部放入，要么一项都不放，不能加入一半才发现超额。

2.2 为什么这个版本先用 list

list 能直接复用索引和切片规则，很适合把协议串起来。代价是 `pop(0)` 要移动后面元素，队列很大、出队很频繁时不合适。

这是一种有意的取舍：先把接口和状态验证清楚，后面再用 deque 比较底层结构。不要把“写成自定义类”当成高性能保证。

2.3 完整实现

```python
# runnable: hb24_custom_queue
class CustomQueue:
    def __init__(self, values=(), *, capacity=None) -> None:
        if capacity is not None and (type(capacity) is not int or capacity <= 0):
            raise ValueError("capacity must be a positive integer or None")
        items = list(values)
        if capacity is not None and len(items) > capacity:
            raise OverflowError("initial values exceed capacity")
        self._items = items
        self._capacity = capacity

    @property
    def capacity(self):
        return self._capacity

    def _check_room(self, incoming: int) -> None:
        if self.capacity is not None and len(self._items) + incoming > self.capacity:
            raise OverflowError("queue capacity exceeded")

    def enqueue(self, value) -> None:
        self._check_room(1)
        self._items.append(value)

    def extend(self, values) -> None:
        incoming = list(values)
        self._check_room(len(incoming))
        self._items.extend(incoming)

    def dequeue(self):
        if not self._items:
            raise IndexError("dequeue from empty queue")
        return self._items.pop(0)

    def peek(self):
        if not self._items:
            raise IndexError("peek from empty queue")
        return self._items[0]

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)

    def __bool__(self) -> bool:
        return bool(self._items)

    def __getitem__(self, key):
        return self._items[key]

    def __iter__(self):
        return iter(tuple(self._items))

    def __repr__(self) -> str:
        return f"CustomQueue({self._items!r}, capacity={self.capacity!r})"

    def __eq__(self, other):
        if not isinstance(other, CustomQueue):
            return NotImplemented
        return self._items == other._items


source = ["A", "B"]
queue = CustomQueue(source, capacity=4)
source.append("outside")
assert list(queue) == ["A", "B"]
assert queue.peek() == "A"
assert len(queue) == 2
queue.enqueue("C")
queue.extend(["D"])
assert queue[0] == "A"
assert queue[-1] == "D"
assert queue[1:4:2] == ["B", "D"]
assert queue == CustomQueue(["A", "B", "C", "D"])
assert queue != ["A", "B", "C", "D"]

try:
    queue.capacity = 1
except AttributeError:
    pass
else:
    raise AssertionError("read-only capacity was changed")
assert queue.capacity == 4

try:
    queue.extend(["E", "F"])
except OverflowError:
    pass
else:
    raise AssertionError("over-capacity batch was accepted")
assert list(queue) == ["A", "B", "C", "D"]

snapshot_iterator = iter(queue)
assert queue.dequeue() == "A"
assert list(snapshot_iterator) == ["A", "B", "C", "D"]
assert list(queue) == ["B", "C", "D"]
queue.clear()
assert len(queue) == 0
assert not queue
for operation in (queue.peek, queue.dequeue):
    try:
        operation()
    except IndexError:
        pass
    else:
        raise AssertionError("empty queue operation should fail")
assert CustomQueue.__hash__ is None
print(queue)
```

2.4 一次出队到底改了什么

原内容是 A、B、C、D。dequeue 检查非空，pop(0) 取走 A，并把 A 作为返回值交给调用方；内部列表变成 B、C、D。

peek 只返回 `_items[0]`，没有 pop，所以队列长度不变。不要只看方法都返回 A，就认为它们做的是同一件事。

`queue[1:4:2]` 传进来的是 slice，直接交给列表，因此返回位置 1 和 3 的 B、D。这个结果是新的列表结构，不是能把队列增删同步回去的视图。

2.5 快照只复制结构，不会递归复制元素

iter 内部先生成 tuple，再返回它的迭代器。所以创建迭代器后出队，旧迭代器仍能看到当时的四项。

如果元素是可变字典，快照仍然引用那些字典。随后修改某个字典内部字段，快照也能看到。这里承诺的是队列元素排列的快照，不是每个对象都深拷贝。

相等规则只比较内容，不比较 capacity。两个队列内容一样但容量不同，本项目仍认为它们相等。由于内容可变，类没有提供 hash，避免被当作不稳定的字典键。

2.6 批量加入为什么先 list 再检查

如果边遍历 values 边 append，可能前两项已加入，第三项才发现满了。要提供整批成功或整批失败，先把输入材料化为 incoming，检查总容量，再统一 extend。

如果输入生成器在遍历过程中自己抛错，incoming 尚未构建完，也不会修改队列。但生成器已经产生过的外部副作用不会自动撤销，队列只能保证自身状态不被部分更新。

2.7 扩展练习：换成 deque，增加 drain

实现 FastQueue，保留入队、出队、peek、len、迭代，并增加 `drain(count)` 一次取出最多 count 项。这里故意不承诺索引、切片和容量，集中比较 FIFO 所需接口。

count 必须是非负整数；超过剩余数量就全部取走；0 返回空列表且不改变状态。下面是独立完整的这个精简接口，不是前一代码块的补丁。

```python
# runnable: hb24_queue_drain_answer
from collections import deque


class FastQueue:
    def __init__(self, values=()) -> None:
        self._items = deque(values)

    def enqueue(self, value) -> None:
        self._items.append(value)

    def dequeue(self):
        if not self._items:
            raise IndexError("dequeue from empty queue")
        return self._items.popleft()

    def peek(self):
        if not self._items:
            raise IndexError("peek from empty queue")
        return self._items[0]

    def drain(self, count: int) -> list:
        if type(count) is not int or count < 0:
            raise ValueError("count must be a non-negative integer")
        return [self._items.popleft() for _ in range(min(count, len(self._items)))]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(tuple(self._items))


queue = FastQueue([1, 2, 3, 4])
assert queue.drain(0) == []
assert list(queue) == [1, 2, 3, 4]
assert queue.drain(2) == [1, 2]
assert list(queue) == [3, 4]
assert queue.drain(99) == [3, 4]
assert not queue
queue.enqueue(5)
assert queue.peek() == 5
assert queue.dequeue() == 5
for invalid in (-1, 1.5, True):
    try:
        queue.drain(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid drain count was accepted")
assert not queue
print("drain checks passed")
```

deque 从左端取出不需要像列表那样移动其余全部元素，适合频繁 FIFO 操作。但这个类仍没有完整线程同步：不能因为底层某些操作有实现层面的保障，就把“先检查再取出”等组合操作当成业务原子动作。

如果要跨线程等待任务，用标准库 queue.Queue 更合适；跨协程等待用 asyncio.Queue；跨进程通信又是 multiprocessing.Queue。它们解决的等待和同步问题不同，不只是容器名字不同。

---

3）项目三：Account，集中观察属性校验与显示规则

3.1 先划清这个项目的边界

这是属性机制的玩具实现：内部保存明文字符串，verify 直接比较。它不是密码安全存储、身份认证或账号保护方案，不能放进真实认证系统使用。

读取 password 返回星号，只改变显示内容，不会把内部字符串加密。`_password` 的下划线也不阻止外部代码读取。

下面只验证 Python 对象规则：创建和修改都走相同校验；非法修改保留旧值；repr 不主动显示内部字符串；需要核对当前值才能调用改密流程。

3.2 需求与方法拆分

username 是非空文本，创建时去掉两边空格。password 必须是长度至少 8 的字符串，不自动 strip；因为两侧空格也可能是调用者明确提供的内容。

password getter 返回固定星号，setter 校验后保存 `_password`。verify_password 返回比较结果。change_password 先核对旧值，再让 setter 校验新值。

成功创建总数统一放在 Account.created_count，初始化失败不计数。这个计数只演示单线程状态，不承诺线程安全。

3.3 完整实现

```python
# runnable: hb24_account_property
class Account:
    created_count = 0

    def __init__(self, username: str, password: str) -> None:
        if not isinstance(username, str):
            raise TypeError("username must be text")
        normalized = username.strip()
        if not normalized:
            raise ValueError("username must not be blank")
        self.username = normalized
        self.password = password
        Account.created_count += 1

    @property
    def password(self) -> str:
        return "******"

    @password.setter
    def password(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("password must be text")
        if len(value) < 8:
            raise ValueError("password must contain at least 8 characters")
        self._password = value

    def verify_password(self, candidate: str) -> bool:
        return isinstance(candidate, str) and candidate == self._password

    def change_password(self, current: str, replacement: str) -> None:
        if not self.verify_password(current):
            raise ValueError("current password does not match")
        self.password = replacement

    def __repr__(self) -> str:
        return f"Account(username={self.username!r})"

    def __str__(self) -> str:
        return f"Account<{self.username}>"


def expect_error(kind, action) -> None:
    try:
        action()
    except kind:
        return
    raise AssertionError(f"expected {kind.__name__}")


account = Account(" Ada ", "demo-pass-1")
assert account.username == "Ada"
assert account.password == "******"
assert account.verify_password("demo-pass-1")
assert not account.verify_password("wrong")
assert not account.verify_password(None)
assert "demo-pass-1" not in repr(account)
assert "demo-pass-1" not in str(account)
assert account._password == "demo-pass-1"
assert Account.created_count == 1

expect_error(ValueError, lambda: setattr(account, "password", "short"))
expect_error(TypeError, lambda: setattr(account, "password", 12345678))
assert account.verify_password("demo-pass-1")

expect_error(ValueError, lambda: account.change_password("wrong", "demo-pass-2"))
assert account.verify_password("demo-pass-1")
expect_error(ValueError, lambda: account.change_password("demo-pass-1", "short"))
assert account.verify_password("demo-pass-1")

account.change_password("demo-pass-1", "demo-pass-2")
assert not account.verify_password("demo-pass-1")
assert account.verify_password("demo-pass-2")
assert account.password == "******"
assert Account.created_count == 1
expect_error(ValueError, lambda: Account("Bob", "short"))
expect_error(ValueError, lambda: Account("   ", "demo-pass-3"))
assert Account.created_count == 1
print(account, repr(account), account.password)
```

3.4 初始化与后续改值怎么共用入口

创建时，`self.password = password` 进入 setter。setter 检查类型和长度，保存到 `_password`，返回后 `__init__` 才增加 created_count。

后续 `account.password = ...` 走同一个 setter，因此不需要再写一套修改时校验。change_password 通过它完成新值校验，也没有复制规则。

getter 不返回 `_password`，所以读取 password 永远是星号。verify_password 则直接比较内部值，不会拿星号和候选值比较，否则所有真实候选都会被判错。

3.5 两种失败为什么都保留旧值

旧值不匹配时，change_password 在进入 setter 之前就抛错。新值太短时，已经进入 setter，但在赋给 `_password` 之前抛错。

两条路径都没执行保存，因此内部仍是旧字符串。测试分别覆盖这两个位置，不能只测“随便出一个异常”，就认为所有失败路径都正确。

3.6 这里故意没有做哪些承诺

长度 8 只是本例约束，不代表完整密码政策。星号不隐藏对象内存，repr 不输出某字段也不等于所有日志都不会泄露。代码中还能直接读取 `_password`，就是为了明确这个限制。

真正系统应使用成熟认证方案与专门的密码哈希实现，并处理速率限制、凭据管理、重置流程等要求。这一章不把一个 property 例子包装成认证系统，也不让你用自创加密替代成熟方案。

3.7 扩展练习：把最小长度变成每个对象的配置

要求 Account 接收 min_length，默认 8，必须是至少 8 的整数。getter 仍只显示星号，初始化与后续赋值都使用该对象的最小长度，失败不改变旧值。

下面是独立完整的属性配置版本，重点是构造顺序：先保存校验配置，再触发依赖它的 setter。它仍然不是安全认证实现。

```python
# runnable: hb24_account_policy_answer
class Account:
    def __init__(self, password: str, *, min_length: int = 8) -> None:
        if type(min_length) is not int or min_length < 8:
            raise ValueError("min_length must be an integer of at least 8")
        self._min_length = min_length
        self.password = password

    @property
    def min_length(self) -> int:
        return self._min_length

    @property
    def password(self) -> str:
        return "******"

    @password.setter
    def password(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("password must be text")
        if len(value) < self._min_length:
            raise ValueError("password is shorter than configured minimum")
        self._password = value

    def verify_password(self, candidate: str) -> bool:
        return isinstance(candidate, str) and candidate == self._password


account = Account("demo-value-123", min_length=12)
assert account.min_length == 12
assert account.password == "******"
for invalid in ("12345678", "short"):
    try:
        account.password = invalid
    except ValueError:
        pass
    else:
        raise AssertionError("short replacement was accepted")
    assert account.verify_password("demo-value-123")
account.password = "another-demo-123"
assert account.verify_password("another-demo-123")
try:
    account.min_length = 1
except AttributeError:
    pass
else:
    raise AssertionError("read-only minimum was changed")
assert account.min_length == 12
print(account.password, account.min_length)
```

如果把 `self.password = password` 放在 `_min_length` 保存之前，setter 读取配置时就会缺少属性。这种错误不是 property 本身复杂，而是初始化依赖顺序没排好。

---

4）项目四：RequestLimiter，用时间窗口限制通过次数

4.1 先把“十秒内两次”说精确

一个限流器实例负责一个配额范围。在最近 window_seconds 秒内，最多接受 limit 次请求。接受返回 True，超额返回 False；拒绝属于正常业务结果，不抛异常中断主流程。

非法配置、非法时钟值属于调用或环境错误，会抛异常。要区分“请求正常被拒绝”和“限流器本身无法正确工作”。

窗口约定为 `(now - window_seconds, now]`：刚好位于左边界的记录过期。只有成功接受的请求计入窗口，拒绝不会把窗口延长。

这是滑动窗口日志，不是每逢整十秒清零的固定窗口。每次判断都根据当前时间向前看一段长度相同的区间。

4.2 为什么用 monotonic 和可替换时钟

计算经过多久时，用单调时钟 time.monotonic，比直接依赖日历时间更合适。它的具体起点不重要，时间差才重要。

测试不应该真的 sleep 十秒。把时钟作为参数传入，用 FakeClock 精确推进到 9 秒、10 秒，就能验证边界，同时快速重复运行。

时间戳按接受顺序放进 deque。只要时钟不倒退，最早记录就在左边，过期时从左端逐个删除即可。

4.3 状态与同步怎样安排

实例保存 limit、window_seconds、时钟、时间戳队列和锁。allow 的读取时间、清理过期、检查数量、加入新记录必须属于同一个临界区。

如果只给 append 加锁，两个线程仍可能都看见“还剩一名额”，随后各自加入一条。需要锁的是完整判断与保存，不是某个容器操作。

4.4 完整实现

```python
# runnable: hb24_request_limiter
from collections import deque
from threading import Lock
from time import monotonic
import math


class FakeClock:
    def __init__(self, now: float = 0.0) -> None:
        self.now = float(now)

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("advance must be finite and non-negative")
        self.now += seconds


class RequestLimiter:
    def __init__(self, limit: int, window_seconds: float, *, clock=monotonic) -> None:
        if type(limit) is not int or limit <= 0:
            raise ValueError("limit must be a positive integer")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)):
            raise TypeError("window_seconds must be numeric")
        if not math.isfinite(window_seconds) or window_seconds <= 0:
            raise ValueError("window_seconds must be finite and positive")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._limit = limit
        self._window = float(window_seconds)
        self._clock = clock
        self._timestamps = deque()
        self._last_seen = None
        self._lock = Lock()

    def _read_time_and_expire(self) -> float:
        raw = self._clock()
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise TypeError("clock must return a number")
        now = float(raw)
        if not math.isfinite(now):
            raise ValueError("clock must return finite time")
        if self._last_seen is not None and now < self._last_seen:
            raise ValueError("clock moved backwards")
        self._last_seen = now
        boundary = now - self._window
        while self._timestamps and self._timestamps[0] <= boundary:
            self._timestamps.popleft()
        return now

    def allow(self) -> bool:
        with self._lock:
            now = self._read_time_and_expire()
            if len(self._timestamps) >= self._limit:
                return False
            self._timestamps.append(now)
            return True

    def __call__(self) -> bool:
        return self.allow()

    @property
    def remaining(self) -> int:
        with self._lock:
            self._read_time_and_expire()
            return self._limit - len(self._timestamps)

    @property
    def retry_after(self) -> float:
        with self._lock:
            now = self._read_time_and_expire()
            if len(self._timestamps) < self._limit:
                return 0.0
            return max(0.0, self._timestamps[0] + self._window - now)


clock = FakeClock()
limiter = RequestLimiter(2, 10, clock=clock)
assert limiter.remaining == 2
assert [limiter.allow(), limiter(), limiter()] == [True, True, False]
assert limiter.remaining == 0
assert limiter.retry_after == 10.0

clock.advance(9)
assert limiter() is False
assert limiter.retry_after == 1.0
clock.advance(1)
assert limiter() is True
assert limiter.remaining == 1
assert limiter.retry_after == 0.0
assert limiter() is True
assert limiter() is False

clock.now = 5.0
try:
    limiter()
except ValueError:
    pass
else:
    raise AssertionError("backwards clock was accepted")
clock.now = 10.0
assert limiter.remaining == 0

for bad_limit in (0, -1, True):
    try:
        RequestLimiter(bad_limit, 10)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid limit was accepted")
for bad_window in (0, -1, float("nan"), float("inf")):
    try:
        RequestLimiter(2, bad_window)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid window was accepted")
print("accepted twice, rejected once; boundary and clock checks passed")
```

4.5 跟着时间戳队列走一遍

| 当前时间 | 操作 | 操作后的有效时间戳 | 结果 |
| :-- | :-- | :-- | :-- |
| 0 | 第一次申请 | `[0]` | True |
| 0 | 第二次申请 | `[0, 0]` | True |
| 0 | 第三次申请 | `[0, 0]` | False |
| 9 | 再次申请 | `[0, 0]` | False |
| 10 | 再次申请 | 先清除两个 0，再放入 10 | True |

时间到 10 时，左边界是 `10 - 10 = 0`。队列里的 0 满足 `timestamp <= boundary`，所以过期。若条件误写成 `<`，刚好十秒的请求仍会被挡住，与本项目约定不同。

拒绝时不 append，所以前三次请求后队列仍只有两项。否则被拒绝的请求也占名额，持续重试可能不断拖延恢复，变成另一种规则。

4.6 remaining 和 retry_after 不预订名额

remaining 读取当前时间、清理过期数据，再返回剩余数量；retry_after 在已满时计算最早一条记录还需多久过期。

它们都不加入新记录，所以查询状态不会消耗次数。不过它们只是查询瞬间的快照：另一个线程下一刻可能抢先申请，看到 remaining=1 不代表你已经预约了一名额。

retry_after 是根据当前记录算出的等待提示。等够时间后仍应重新调用 allow，而不是跳过判断直接执行，因为其他调用者可能已经占用了释放的名额。

4.7 为什么检查时钟倒退

队列按时间递增排列才方便从左端清理。若自定义时钟突然变小，已有顺序和窗口判断就失去前提，所以示例明确拒绝这种输入。

FakeClock 是测试工具，不是可由多线程任意修改的生产时钟。默认 monotonic 由系统提供；如果注入自己的时钟，也必须遵守返回有限数字、不倒退、不长期阻塞的契约。

4.8 这不是跨进程或分布式限流

锁只保护同一个实例在同一个进程中的共享状态。启动多个进程，每个进程各有一份 limiter，就各自拥有 limit 个名额，总量会放大。

按用户、接口、IP 或租户限流，还要明确定义 key、可信来源、状态存储、过期清理等规则。此处类名和算法不能自动解决这些问题。

4.9 扩展练习：不同 key 各有自己的窗口

实现 KeyedLimiter，A 连续两次允许，第三次拒绝，不影响 B 的名额。增加 purge_idle，清除已经没有有效记录的 key，避免永久保存闲置标识。

下面用一个统一锁保护字典与每个 deque，代码完整独立。它仍是本地单进程版本；大量 key 的容量治理、异常时钟和分布式一致性需要另行设计。

```python
# runnable: hb24_keyed_limiter_answer
from collections import deque
from threading import Lock
from time import monotonic
import math


class KeyedLimiter:
    def __init__(self, limit: int, window: float, *, clock=monotonic) -> None:
        if type(limit) is not int or limit <= 0:
            raise ValueError("limit must be a positive integer")
        if isinstance(window, bool) or not isinstance(window, (int, float)):
            raise TypeError("window must be numeric")
        if not math.isfinite(window) or window <= 0:
            raise ValueError("window must be finite and positive")
        self.limit = limit
        self.window = float(window)
        self.clock = clock
        self._records = {}
        self._lock = Lock()
        self._last_seen = None

    def _now(self) -> float:
        value = float(self.clock())
        if not math.isfinite(value):
            raise ValueError("time must be finite")
        if self._last_seen is not None and value < self._last_seen:
            raise ValueError("clock moved backwards")
        self._last_seen = value
        return value

    def _expire(self, records, now) -> None:
        while records and records[0] <= now - self.window:
            records.popleft()

    def allow(self, key: str) -> bool:
        if not isinstance(key, str) or not key:
            raise ValueError("key must be non-empty text")
        with self._lock:
            now = self._now()
            records = self._records.setdefault(key, deque())
            self._expire(records, now)
            if len(records) >= self.limit:
                return False
            records.append(now)
            return True

    def purge_idle(self) -> int:
        with self._lock:
            now = self._now()
            for records in self._records.values():
                self._expire(records, now)
            idle = [key for key, records in self._records.items() if not records]
            for key in idle:
                del self._records[key]
            return len(idle)


time_state = {"now": 0.0}
limiter = KeyedLimiter(2, 10, clock=lambda: time_state["now"])
assert [limiter.allow("A") for _ in range(3)] == [True, True, False]
assert limiter.allow("B") is True
assert limiter.purge_idle() == 0
time_state["now"] = 10.0
assert limiter.purge_idle() == 2
assert limiter.allow("A") is True
assert limiter.allow("B") is True
assert limiter.purge_idle() == 0
try:
    limiter.allow("")
except ValueError:
    pass
else:
    raise AssertionError("empty key was accepted")
print("independent keys and idle cleanup passed")
```

purge_idle 先找出待删除 key 的列表，再逐项删除，不在遍历字典本身时直接改变其大小。它只清理已经空闲的 key，不能解决大量仍活跃 key 的容量上限问题。

4.10 再加一道练习：验证多线程争抢同一名额

要求在固定时间点，20 个任务申请 5 个名额，恰好 5 次通过。下面独立保留限流核心，固定时钟只为排除时间推进影响；它不包含主版本的状态查询接口。

```python
# runnable: hb24_limiter_thread_answer
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from threading import Lock


class RequestLimiter:
    def __init__(self, limit: int, window: float, clock) -> None:
        self.limit = limit
        self.window = window
        self.clock = clock
        self.timestamps = deque()
        self.lock = Lock()

    def allow(self) -> bool:
        with self.lock:
            now = self.clock()
            while self.timestamps and self.timestamps[0] <= now - self.window:
                self.timestamps.popleft()
            if len(self.timestamps) >= self.limit:
                return False
            self.timestamps.append(now)
            return True


limiter = RequestLimiter(5, 10.0, lambda: 0.0)
with ThreadPoolExecutor(max_workers=8) as pool:
    futures = [pool.submit(limiter.allow) for _ in range(20)]
    results = [future.result(timeout=5) for future in futures]
assert sum(results) == 5
assert len(limiter.timestamps) == 5
assert all(timestamp == 0.0 for timestamp in limiter.timestamps)
print(sum(results), len(results) - sum(results))
```

这里输入固定且可信，所以为聚焦并发验证省去了主版本的参数校验。不要用这个精简测试类替换前面完整版本。测试要证明的是完整临界区守住名额，不是观察“哪五个线程赢了”。

---

5）四个项目放在一起，应该能说清什么

人员管理把“记录有效性”和“记录集合管理”分开，失败修改不污染旧数据。队列把常见语法接到协议方法上，同时说明复制、快照和性能代价。

Account 让初始化、修改和显示走各自正确入口，证明 property 只是读写机制，不是安全方案。RequestLimiter 把状态、时间和锁放进同一条可验证的业务规则。

写完实现后，可以逐个问：第一次调用之前有什么状态；这次参数怎样进入方法；哪一句真正修改内部数据；异常发生之前是否已经写入；返回值表达成功结果还是状态快照。

继续扩展时，一次只加一条规则并补一条失败测试。加菜单、文件保存、HTTP 接口之前，先保证这些核心规则能独立运行，后面的接口层才只是把输入交进来、把结果交出去。

官方参考：[dataclasses](https://docs.python.org/3.11/library/dataclasses.html)、[JSON](https://docs.python.org/3.11/library/json.html)、[deque](https://docs.python.org/3.11/library/collections.html#collections.deque)、[property](https://docs.python.org/3.11/library/functions.html#property)、[monotonic](https://docs.python.org/3.11/library/time.html#time.monotonic)、[threading.Lock](https://docs.python.org/3.11/library/threading.html#lock-objects)。
