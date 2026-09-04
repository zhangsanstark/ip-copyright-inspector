23 · 标准库工具：计数、分组、队列与连续数据处理

遇到“按接口分组”“统计状态码”“只留下最近三条记录”时，先别急着自己造一套工具。普通 dict 和 list 能做，但 collections 把这些常见动作准备好了；itertools 则负责按顺序连接、截取、分组和组合数据。

这一章用小输入把处理过程摊开，最后把工具组合成一个完整的日志统计例子。所有输入都在代码里，不访问网络，也不需要安装第三方包。

在仓库根目录运行 `python scripts/check_handbook_examples.py --chapter 23 --show-output`。完整代码块均可单独执行。

---

1）先分清：容器负责保存，迭代工具负责往下取

1.1 它们不是另一套陌生语法

`from collections import Counter` 的意思是从标准库模块里取出一个现成的类。导入之后，创建对象、调用方法、遍历元素，仍然沿用前面几章的规则。

| 要做的事 | 常见选择 | 少写的那部分代码 |
| --- | --- | --- |
| 一个键下面收集多项数据 | defaultdict(list) | 第一次遇到键时创建空列表 |
| 统计每个值出现几次 | Counter | 每次取旧次数，再加一 |
| 经常从队首拿数据 | deque | list.pop(0) 引起的整体移动 |
| 只保留最近 n 项 | deque(maxlen=n) | 手动删除过旧记录 |
| 把几段输入接着遍历 | itertools.chain | 多层衔接循环 |
| 每一步都想看累计结果 | itertools.accumulate | 保存并产出每次累积值 |

这张表是选择入口，不代表它们总比普通写法好。只有两三行、过程很清楚的 for 循环，不必硬换成工具组合。

1.2 别把“得到一个迭代器”看成“已经得到全部结果”

collections 里的三个类会保存内容；本章 itertools 函数返回的是迭代器。调用函数通常只是准备好取数过程，`next()`、for、list() 才会继续向后取。

```python
# runnable: hb23_lazy_chain
from itertools import chain

events = []

def source():
    for number in [1, 2]:
        events.append(f"读取 {number}")
        yield number

joined = chain(source(), [3])
assert events == []
assert next(joined) == 1
assert events == ["读取 1"]
assert list(joined) == [2, 3]
assert events == ["读取 1", "读取 2"]
assert list(joined) == []
print(events)
```

最后一次 list() 为空，不是数据丢了，而是同一个迭代器已经走到末尾。需要重新遍历，就重新创建迭代器，或者事先保存成列表。

---

2）defaultdict：第一次遇到键时，自动准备初始值

2.1 从普通分组代码开始看

有三条记录，想得到每个接口对应的耗时列表。普通 dict 必须在第一次遇到接口时创建空列表；后面的同名接口直接追加。

```python
# runnable: hb23_defaultdict_group_steps
from collections import defaultdict

records = [("/users", 10), ("/orders", 40), ("/users", 20)]

ordinary = {}
history = []
for path, duration in records:
    if path not in ordinary:
        ordinary[path] = []
    ordinary[path].append(duration)
    history.append({key: values.copy() for key, values in ordinary.items()})

groups = defaultdict(list)
for path, duration in records:
    groups[path].append(duration)

assert history == [
    {"/users": [10]},
    {"/users": [10], "/orders": [40]},
    {"/users": [10, 20], "/orders": [40]},
]
assert dict(groups) == ordinary
assert groups["/users"] is not groups["/orders"]
print(history)
```

`groups[path].append(duration)` 可以拆成三步理解：

1. 先执行 `groups[path]`，按键取列表。
2. 如果没有这个键，调用一次 `list()`，把得到的新空列表放进字典。
3. 对刚取到的列表调用 append，把耗时放进去。

`defaultdict(list)` 传的是 list 本身，不是 `list()` 的执行结果。它需要一份“缺值时调用谁”的配置，而不是现在就交给它一个空列表。

2.2 factory 是不带参数调用的函数

`defaultdict(default_factory)` 的第一个参数通常叫默认工厂。这里的“工厂”没有复杂含义，就是一个被调用后能返回初始值的对象：`int()` 返回 0，`list()` 返回新列表，`set()` 返回新集合。

```python
# runnable: hb23_defaultdict_factories
from collections import defaultdict

counts = defaultdict(int)
for status in [200, 500, 200]:
    counts[status] += 1
assert dict(counts) == {200: 2, 500: 1}

tags = defaultdict(set)
tags["a"].add("python")
tags["a"].add("python")
assert tags["a"] == {"python"}

limits = defaultdict(lambda: 3)
assert limits["new-user"] == 3
assert dict(limits) == {"new-user": 3}

try:
    defaultdict([])
except TypeError:
    pass
else:
    raise AssertionError("空列表不能被当作函数调用")
print(dict(counts), dict(limits))
```

`counts[200] += 1` 第一次执行时，先得到默认的 0，再算出 1，最后写回键 200；第二次得到旧值 1，算出 2。默认工厂不会每次都调用，只在方括号查找缺失键时调用。

2.3 get 不会自动创建；看一眼也可能改变字典

```python
# runnable: hb23_defaultdict_lookup_boundary
from collections import defaultdict

groups = defaultdict(list)
assert groups.get("missing") is None
assert "missing" not in groups
assert len(groups) == 0

value = groups["missing"]
assert value == []
assert "missing" in groups
assert len(groups) == 1

groups.default_factory = None
try:
    groups["another"]
except KeyError:
    pass
else:
    raise AssertionError("关闭默认工厂后，缺失键应报错")
assert groups["missing"] == []
print(dict(groups))
```

日志里随手输出 `groups[unknown_key]`，也会创建新键。只想探查、不想增加数据时，用 get 或 in。默认工厂设为 None 只影响以后缺失键的查找，已经存进去的键值还在。

2.4 错误工厂也会造成共享列表

```python
# runnable: hb23_defaultdict_shared_factory
from collections import defaultdict

shared = []
bad = defaultdict(lambda: shared)
bad["a"].append(1)
assert bad["b"] == [1]
assert bad["a"] is bad["b"]

good = defaultdict(list)
good["a"].append(1)
assert good["b"] == []
assert good["a"] is not good["b"]
print(dict(bad), dict(good))
```

错误不在 defaultdict，而在 lambda 每次都返回同一个 shared。想要每个键独立一份可变数据，就让工厂每次新建一份。

---

3）Counter：把“出现了几次”直接保存下来

3.1 输入一串元素，得到元素到次数的映射

```python
# runnable: hb23_counter_steps
from collections import Counter

statuses = [200, 500, 200, 404, 200]
manual = {}
history = []
for status in statuses:
    manual[status] = manual.get(status, 0) + 1
    history.append(manual.copy())

counts = Counter(statuses)
assert dict(counts) == {200: 3, 500: 1, 404: 1}
assert dict(counts) == manual
assert history[0] == {200: 1}
assert history[2] == {200: 2, 500: 1}
assert counts[999] == 0
assert 999 not in counts
assert counts.get(999) is None
print(history)
```

Counter 的键仍然遵守字典要求：需要可哈希。字符串、整数、可哈希的元组能当统计项；列表不能直接当统计项。

对不存在的键用方括号读取，Counter 返回 0，但不会像 defaultdict 那样自动把这个键存进去。get 沿用普通字典行为，不会自动替换成 0。

3.2 传入可迭代对象与传入映射，含义不同

```python
# runnable: hb23_counter_inputs
from collections import Counter

assert Counter("aba") == Counter({"a": 2, "b": 1})
assert Counter(["aba", "aba"]) == Counter({"aba": 2})
assert Counter({"a": 10})["a"] == 10

pairs = [("a", 2), ("a", 2)]
assert Counter(pairs) == Counter({("a", 2): 2})
assert Counter(dict([("a", 2), ("b", 3)])) == Counter(a=2, b=3)

try:
    Counter([[1], [1]])
except TypeError:
    pass
else:
    raise AssertionError("列表不能当 Counter 的键")
print(Counter("aba"), Counter(pairs))
```

`Counter("aba")` 一次读一个字符；`Counter(["aba", "aba"])` 一次读一个完整字符串。`Counter({"a": 10})` 接收的是已有次数，不会把字典值 10 当成一次出现。

如果手里是“键、次数”组成的二元组列表，要先转成 dict，再给 Counter。直接传二元组列表，会统计整个二元组出现了几次。

3.3 update 是累加，不是覆盖

```python
# runnable: hb23_counter_update_subtract
from collections import Counter

counts = Counter(a=2)
result = counts.update(["a", "b", "a"])
assert result is None
assert dict(counts) == {"a": 4, "b": 1}

counts.update({"a": 3})
assert counts["a"] == 7
counts.subtract({"a": 8, "b": 1})
assert dict(counts) == {"a": -1, "b": 0}
assert "b" in counts
assert counts.total() == -1

ordinary = {"a": 2}
ordinary.update({"a": 3})
assert ordinary == {"a": 3}
print(dict(counts), ordinary)
```

同样叫 update，dict 的意思是“新值替换旧值”，Counter 的意思是“把新次数加进去”。subtract 原地减去次数，允许结果变成 0 或负数，不会自动删除键。

3.4 most_common、elements、total 分别回答三个问题

| 方法 | 参数 | 返回什么 |
| --- | --- | --- |
| most_common(n) | 最多要几项；省略或 None 表示全部 | 按次数从多到少的二元组列表 |
| elements() | 无参数 | 按次数重复元素的迭代器，只展开正整数次数 |
| total() | 无参数 | 所有次数相加，包括零和负数 |

```python
# runnable: hb23_counter_reports
from collections import Counter

counts = Counter(["b", "a", "b", "c", "a"])
assert counts.most_common() == [("b", 2), ("a", 2), ("c", 1)]
assert counts.most_common(2) == [("b", 2), ("a", 2)]
assert counts.most_common(0) == []
assert counts.total() == 5
assert list(counts.elements()) == ["b", "b", "a", "a", "c"]

adjusted = Counter(a=2, b=0, c=-3)
assert list(adjusted.elements()) == ["a", "a"]
assert adjusted.total() == -1
assert +adjusted == Counter(a=2)
assert -adjusted == Counter(c=3)
assert dict(adjusted) == {"a": 2, "b": 0, "c": -3}
print(counts.most_common(2))
```

b 和 a 都出现两次，b 在输入中先出现，所以排在前面。elements 按键及其次数展开，不会还原原始输入顺序。

`+adjusted` 返回一份只保留正次数的新 Counter；`-adjusted` 把负次数取反后保留。它们不修改原对象。通常让计数保持整数；虽然 Counter 能存别的值，elements 不能用 1.5 这样的次数来重复元素。

3.5 加减与集合符号，处理的是次数

```python
# runnable: hb23_counter_arithmetic
from collections import Counter

left = Counter(a=3, b=1)
right = Counter(a=1, b=2, c=1)
assert left + right == Counter(a=4, b=3, c=1)
assert left - right == Counter(a=2)
assert left & right == Counter(a=1, b=1)
assert left | right == Counter(a=3, b=2, c=1)
assert left == Counter(a=3, b=1, absent=0)
assert Counter(a=1) <= Counter(a=2, b=1)

subtracting = left.copy()
subtracting.subtract(right)
assert dict(subtracting) == {"a": 2, "b": -1, "c": -1}
print(left - right, dict(subtracting))
```

`left - right` 与 `left.subtract(right)` 不同：前者返回新 Counter，而且只留下正次数；后者修改 left，保留 0 和负数。`&` 取每个键的较小次数，`|` 取较大次数，不是普通 dict 的右侧覆盖。

比较相等时，缺失键按 0 次看待，因此多一个值为 0 的键仍可能相等。但 `dict(counter)` 会保留实际存在的零值键；字典形状与 Counter 的计数相等，不要混为一谈。

---

4）deque：左右两端都方便进出

4.1 从右边加入、左边取出，就是队列

`deque(iterable=(), maxlen=None)` 创建双端队列。可以把它看成两头都开口的列表：重点是两端操作，不是按任意下标反复访问。

```python
# runnable: hb23_deque_queue
from collections import deque

jobs = deque(["a", "b"])
assert jobs.append("c") is None
assert list(jobs) == ["a", "b", "c"]
assert jobs.popleft() == "a"
assert list(jobs) == ["b", "c"]
jobs.appendleft("urgent")
assert list(jobs) == ["urgent", "b", "c"]
assert jobs.pop() == "c"
assert jobs[0] == "urgent"
assert jobs[-1] == "b"
assert len(jobs) == 2
print(list(jobs))
```

append 从右端加入，appendleft 从左端加入；pop 从右端取走并返回，popleft 从左端取走并返回。空队列执行 pop 或 popleft 会抛 IndexError。

list 的 `pop(0)` 也能取队首，但后面的引用要往前移动。deque 的两端操作不需要搬动整段内容，适合反复进出队列的场景。经常按中间下标随机访问时，仍优先考虑 list。

4.2 extendleft 会把输入的顺序反过来

```python
# runnable: hb23_deque_extend
from collections import deque

right = deque([0])
right.extend([1, 2, 3])
assert list(right) == [0, 1, 2, 3]

left = deque([0])
history = []
for value in [1, 2, 3]:
    left.appendleft(value)
    history.append(list(left))
assert history == [[1, 0], [2, 1, 0], [3, 2, 1, 0]]

automatic = deque([0])
automatic.extendleft([1, 2, 3])
assert automatic == left
preserved = deque([0])
preserved.extendleft(reversed([1, 2, 3]))
assert list(preserved) == [1, 2, 3, 0]
print(history)
```

不是 extendleft 特意做了一次排序，而是它依次把 1、2、3 加到左端；后进来的自然站到最左边。如果希望最终仍是 1、2、3，就把输入反着喂进去。

4.3 maxlen 是保留上限，不是“满了就拒绝”

```python
# runnable: hb23_deque_maxlen
from collections import deque

recent = deque(maxlen=3)
history = []
for value in [10, 20, 30, 40]:
    recent.append(value)
    history.append(list(recent))
assert history == [[10], [10, 20], [10, 20, 30], [20, 30, 40]]
recent.appendleft(5)
assert list(recent) == [5, 20, 30]
assert recent.maxlen == 3

empty = deque([1, 2, 3], maxlen=0)
empty.append(4)
assert list(empty) == []

try:
    recent.insert(1, 99)
except IndexError:
    pass
else:
    raise AssertionError("有界队列满时，insert 不会自动挤走另一端")
assert list(recent) == [5, 20, 30]
print(history)
```

从右边追加满了，就丢掉最左边；从左边追加满了，就丢掉最右边。这里的丢弃不会返回被挤走的元素。若后续计算需要它，例如维护滚动总和，应在追加前先读出将要离开的那一项。

insert 是一个需要单独记住的边界：已满的有界 deque 插入会抛 IndexError，不采用 append 那种自动挤出的规则。

4.4 rotate 是轮转，不是反转

```python
# runnable: hb23_deque_rotate
from collections import deque

values = deque([1, 2, 3, 4])
assert values.rotate(1) is None
assert list(values) == [4, 1, 2, 3]
values.rotate(-2)
assert list(values) == [2, 3, 4, 1]
values.rotate(4)
assert list(values) == [2, 3, 4, 1]
assert values.reverse() is None
assert list(values) == [1, 4, 3, 2]

empty = deque()
empty.rotate(10)
assert list(empty) == []
print(list(values))
```

`rotate(n=1)` 中，正数向右轮转，负数向左轮转。右移一格等于把最后一项拿到最前面；reverse 才是把整段前后倒过来。

4.5 其余常用操作与边界

```python
# runnable: hb23_deque_other_methods
from collections import deque

values = deque([1, 2, 1])
assert values.count(1) == 2
assert values.index(1, 1, 3) == 2
values.insert(1, 9)
assert list(values) == [1, 9, 2, 1]
values.remove(1)
assert list(values) == [9, 2, 1]
values[0] = 8
del values[-1]
assert list(values) == [8, 2]
assert list(reversed(values)) == [2, 8]
assert 8 in values

copied = values.copy()
assert copied == values and copied is not values
values.clear()
assert len(values) == 0
assert list(copied) == [8, 2]

try:
    copied[:1]
except TypeError:
    pass
else:
    raise AssertionError("deque 不直接支持切片")

try:
    values.popleft()
except IndexError:
    pass
else:
    raise AssertionError("空队列不能弹出")
print(list(copied))
```

index 和 remove 找不到时都抛 ValueError；copy 只复制外层，里面如果装的是列表，仍然遵循浅拷贝规则。需要切片可以先 `list(d)[start:stop]`，但这样会把整个队列复制成列表；只想按迭代顺序取一段，可以用下面的 islice。

deque 的单次两端追加、弹出有线程安全保证，不代表“先判断非空，再弹出”这两步合起来也不可被打断。需要等待任务、跨线程交接与协调完成状态时，应看 `queue.Queue`，不要把 deque 当成完整的阻塞任务队列。

---

5）chain、islice、pairwise：接起来、取一段、看相邻两项

5.1 chain 顺序接上输入，不会深度展开

```python
# runnable: hb23_chain_variants
from itertools import chain

batches = [[1, 2], [], [3]]
assert list(chain([1, 2], [], [3])) == [1, 2, 3]
assert list(chain.from_iterable(batches)) == [1, 2, 3]

manual = []
for batch in batches:
    for item in batch:
        manual.append(item)
assert list(chain.from_iterable(batches)) == manual
assert list(chain()) == []
assert list(chain.from_iterable([])) == []
assert list(chain([[1], [2]], [[3]])) == [[1], [2], [3]]
print(manual)
```

`chain(*iterables)` 接收多份输入；`chain.from_iterable(iterable)` 接收一份“里面装着多份输入”的对象。后一种适合批次本身也是逐批生成的情况，不需要先用 `*batches` 把所有批次展开成实参。

它只连接一层。最后一个例子保留 `[1]`、`[2]`、`[3]` 这三项，不会一路递归拆到整数。

5.2 islice 取的是迭代进度，不能倒着取

常见写法是 `islice(iterable, stop)` 或 `islice(iterable, start, stop, step)`。start 默认从 0 开始，stop 不包含，step 默认是 1。它不接受负下标，也不接受 0 或负步长。

```python
# runnable: hb23_islice_progress
from itertools import islice

source = iter(range(10))
selected = islice(source, 1, 6, 2)
assert list(selected) == [1, 3, 5]
assert next(source) == 6
assert list(islice(range(5), 3)) == [0, 1, 2]
assert list(islice(range(5), 2, None)) == [2, 3, 4]
assert list(islice([], 10)) == []

try:
    list(islice(range(5), -1, None))
except ValueError:
    pass
else:
    raise AssertionError("islice 不支持负起点")
print([1, 3, 5])
```

取 1、3、5 的过程中，0、2、4 也必须从 source 里读过去，只是没有交给调用方。所以再取 source 时来到 6，而不是还停在没选中的某一项。

当一个有 stop 的 islice 被完全耗尽时，它会把源迭代器推进到 start 和 stop 中较大的位置，或源本身的末尾。不能把 islice 当成“不影响原迭代器的窗口”。

5.3 pairwise 把相邻项配成对

```python
# runnable: hb23_pairwise
from itertools import pairwise

timestamps = [10, 13, 20, 21]
pairs = list(pairwise(timestamps))
gaps = [current - previous for previous, current in pairs]
assert pairs == [(10, 13), (13, 20), (20, 21)]
assert gaps == [3, 7, 1]
assert list(pairwise([])) == []
assert list(pairwise([10])) == []
assert list(pairwise([10, 13])) == [(10, 13)]
print(gaps)
```

第一对是第 1、2 项，第二对是第 2、3 项，不是两两分组后互不重叠。输入有 n 项且 n 至少为 1 时，结果有 n-1 对。常见用途是计算相邻时间差、检查排序是否连续。

---

6）count、cycle、repeat：没有自然终点的输入，必须控制出口

6.1 count 从指定数字不断往后走

`count(start=0, step=1)` 每次返回当前值，然后加 step。它不设 stop，不能直接 `list(count())`，否则会一直取下去。

```python
# runnable: hb23_count_bounded
from itertools import count, islice

sequence = count(10, 3)
assert list(islice(sequence, 4)) == [10, 13, 16, 19]
assert next(sequence) == 22
assert list(islice(count(5, -2), 4)) == [5, 3, 1, -1]
assert list(islice(count(7, 0), 3)) == [7, 7, 7]
print(list(islice(count(100), 3)))
```

step 可以是负数或 0；是否会停止并不取决于数字大小，而取决于调用方是否停止取数。给一份已知有限的数据编号时，enumerate 往往更直接，不必绕到 count。

6.2 cycle 反复走同一批值，repeat 重复同一个对象

```python
# runnable: hb23_cycle_repeat
from itertools import cycle, islice, repeat

assert list(islice(cycle(["a", "b"]), 5)) == ["a", "b", "a", "b", "a"]
assert list(cycle([])) == []
assert list(repeat("x", 3)) == ["x", "x", "x"]
assert list(repeat("x", 0)) == []

shared = []
rows = list(repeat(shared, 3))
rows[0].append(1)
assert rows == [[1], [1], [1]]
assert rows[0] is rows[1]
independent = [[] for _ in range(3)]
independent[0].append(1)
assert independent == [[1], [], []]
print(rows)
```

`cycle(iterable)` 会记住已经读到的元素，源耗尽后再从记住的内容循环。输入为空时直接结束；输入很大时，缓存也会变大，不能把它理解成完全不保存数据。

`repeat(object, times)` 中，times 省略则不断重复。重复的是对象引用，不是每次创建副本。用 `repeat([], 3)` 构造二维列表，会出现三行共享同一个内层列表的问题。

---

7）accumulate：不仅要最终结果，还要每一步结果

7.1 从手写累计循环对照

`accumulate(iterable, func=operator.add, *, initial=None)` 默认逐步相加。未提供有效初值时，第一项先成为累计值；之后每次把“旧累计值”和“下一项”交给 func，func 的返回值成为新累计值。

```python
# runnable: hb23_accumulate_steps
from itertools import accumulate

values = [2, 3, 4]
manual = []
total = 0
for value in values:
    total += value
    manual.append(total)
assert manual == [2, 5, 9]
assert list(accumulate(values)) == manual
assert list(accumulate(values, initial=10)) == [10, 12, 15, 19]
assert list(accumulate([])) == []
assert list(accumulate([], initial=10)) == [10]
assert list(accumulate([7])) == [7]
print(manual)
```

给 initial=10 后，10 自己也会作为第一项产出：先得到 10，接着 10+2=12，再得到 12+3=15，最后 15+4=19。因此结果比输入多一项。

这里的 None 表示“没有提供累计初值”。它不能被用来要求“先输出一个 None，再拿 None 去调用函数”。这一点与可以接收任意初值对象的 reduce 不能生搬硬套。

7.2 换函数以后，累计的不一定是和

```python
# runnable: hb23_accumulate_custom
from itertools import accumulate
from operator import mul
from functools import reduce

assert list(accumulate([2, 3, 4], mul)) == [2, 6, 24]
assert list(accumulate([3, 1, 5, 2], max)) == [3, 3, 5, 5]
assert reduce(mul, [2, 3, 4]) == 24

calls = []
def subtract(previous, item):
    result = previous - item
    calls.append((previous, item, result))
    return result

result = list(accumulate([10, 3, 2], subtract))
assert result == [10, 7, 5]
assert calls == [(10, 3, 7), (7, 2, 5)]
print(calls)
```

reduce 只交出最终累计值；accumulate 逐步交出途中的累计值。需要画趋势、看余额变化、检查前缀最大值时，保留中间结果就有意义。只要求和，用 sum；不要为了显得高级把简单任务写复杂。

---

8）groupby：只合并相邻的同组项

8.1 它不会自动找遍全体同名键

```python
# runnable: hb23_groupby_consecutive
from itertools import groupby

records = [("a", 1), ("a", 2), ("b", 3), ("a", 4)]
groups = []
for key, group in groupby(records, key=lambda row: row[0]):
    groups.append((key, list(group)))
assert groups == [
    ("a", [("a", 1), ("a", 2)]),
    ("b", [("b", 3)]),
    ("a", [("a", 4)]),
]

sorted_records = sorted(records, key=lambda row: row[0])
merged = {
    key: [value for _, value in group]
    for key, group in groupby(sorted_records, key=lambda row: row[0])
}
assert merged == {"a": [1, 2, 4], "b": [3]}
print(groups, merged)
```

`groupby(iterable, key=None)` 一边向后走，一边比较相邻元素的 key。key 变化就结束这一组；后面再出现相同 key，会开一个新组。

因此它与常见 SQL GROUP BY 的直觉不同。要把所有同名键合并，可以先按同一套 key 排序，再 groupby；如果只是把无序记录收集到字典里，defaultdict(list) 更省心，也不必先排序。

8.2 每一组的 group 也是迭代器，要及时取完

```python
# runnable: hb23_groupby_shared_source
from itertools import groupby

outer = groupby("aaabb")
first_key, first_group = next(outer)
assert first_key == "a"
assert next(first_group) == "a"

second_key, second_group = next(outer)
assert second_key == "b"
assert list(first_group) == []
assert list(second_group) == ["b", "b"]

saved = [(key, list(group)) for key, group in groupby("aaabb")]
assert saved == [("a", ["a", "a", "a"]), ("b", ["b", "b"])]
print(saved)
```

外层迭代器和每组迭代器共用同一份输入。外层往下一组走时，会越过上一组剩余内容，所以不能把 group 对象攒起来，最后再统一读取。要保留每组内容，当场 list(group)；只要计数，就当场统计数量。

---

9）product 与排列组合：先问顺序是否重要、能否重复选

9.1 product：从每一份输入各选一项

```python
# runnable: hb23_product
from itertools import product

regions = ["east", "west"]
modes = ["read", "write"]
result = list(product(regions, modes))
manual = []
for region in regions:
    for mode in modes:
        manual.append((region, mode))
assert result == manual == [
    ("east", "read"), ("east", "write"),
    ("west", "read"), ("west", "write"),
]
assert list(product([0, 1], repeat=2)) == [(0, 0), (0, 1), (1, 0), (1, 1)]
assert list(product([], [1, 2])) == []
assert list(product()) == [()]
print(result)
```

`product(*iterables, repeat=1)` 对应多层嵌套循环。repeat=2 是把整组输入参数重复两遍，`product(A, B, repeat=2)` 相当于 `product(A, B, A, B)`，不是把最终结果简单重复两次。

每份输入长度相乘就是组合数量。10 份输入各 10 个选项，结果就有 100 亿项；返回迭代器只能推迟创建结果，不会让组合数量变少。

9.2 permutations 与 combinations 的差别看两个字母就够

```python
# runnable: hb23_combinatorics
from itertools import permutations, combinations, combinations_with_replacement

assert list(permutations("ABC", 2)) == [
    ("A", "B"), ("A", "C"), ("B", "A"),
    ("B", "C"), ("C", "A"), ("C", "B"),
]
assert list(combinations("ABC", 2)) == [("A", "B"), ("A", "C"), ("B", "C")]
assert list(combinations_with_replacement("AB", 2)) == [
    ("A", "A"), ("A", "B"), ("B", "B"),
]
assert list(permutations("AB", 3)) == []
assert list(combinations("AB", 3)) == []
assert list(combinations("AB", 0)) == [()]
assert list(combinations_with_replacement("", 2)) == []
print(list(combinations("ABC", 2)))
```

`permutations(iterable, r=None)` 取 r 个位置排出顺序，AB 与 BA 算两个结果；省略 r 就取全部位置。`combinations(iterable, r)` 不把 AB 与 BA 分成两个结果，而且同一个输入位置不能重复选。

`combinations_with_replacement(iterable, r)` 允许重复使用输入位置，所以能得到 AA。它仍不另外产生 BA，因为它处理的是组合，不是排列。

这几个工具按输入位置区分元素，不负责给输入值去重：`combinations("AAB", 2)` 可能给出两次外观相同的 AB。它们也会先保存输入以便反复选择，不要把无限迭代器当参数交进去。

```python
# runnable: hb23_combinations_duplicate_positions
from itertools import combinations

result = list(combinations("AAB", 2))
assert result == [("A", "A"), ("A", "B"), ("A", "B")]
assert set(result) == {("A", "A"), ("A", "B")}
print(result)
```

---

10）再认识六个按条件处理输入的工具

10.1 filterfalse 与 compress：按条件或标记保留

```python
# runnable: hb23_filterfalse_compress
from itertools import filterfalse, compress

values = [1, 2, 3, 4]
assert list(filterfalse(lambda value: value % 2 == 0, values)) == [1, 3]
assert list(filterfalse(None, [0, 1, "", "a", None])) == [0, "", None]

data = ["a", "b", "c", "d"]
assert list(compress(data, [1, 0, True, False])) == ["a", "c"]
assert list(compress(data, [True, False])) == ["a"]
assert list(compress([], [True])) == []
print(list(compress(data, [1, 0, 1, 0])))
```

`filterfalse(predicate, iterable)` 保留判断结果为假的项，正好与 filter 的保留方向相反；predicate=None 时直接用元素本身的真假值。

`compress(data, selectors)` 将数据和标记按位置配对，标记为真就保留。任意一边耗尽就停止，标记比数据短不会自动补成 True，也不会抛长度错误。

10.2 takewhile 与 dropwhile：只关心开头的一段

```python
# runnable: hb23_take_drop_while
from itertools import takewhile, dropwhile

values = [1, 2, 5, 1]
assert list(takewhile(lambda value: value < 3, values)) == [1, 2]
assert list(dropwhile(lambda value: value < 3, values)) == [5, 1]
assert list(takewhile(lambda value: value < 3, [])) == []
assert list(dropwhile(lambda value: value < 3, [1, 2])) == []

source = iter([1, 2, 5, 1])
prefix = list(takewhile(lambda value: value < 3, source))
assert prefix == [1, 2]
assert next(source) == 1
print(prefix)
```

takewhile 从开头一直保留，遇到第一个不满足条件的 5 就结束，后面的 1 不会再检查。为了知道 5 不满足，它已经从源里取出了 5；5 不会退回源，因此上例再 next(source) 直接得到后面的 1。

dropwhile 从开头一直丢弃，遇到第一个不满足条件的值后，从这个值开始全部保留。后续即使又满足条件，也不会重新开始丢弃。它们不是对全体元素做筛选；全体筛选通常用 filter 或推导式。

10.3 starmap：把每一项拆成函数实参

```python
# runnable: hb23_starmap
from itertools import starmap

pairs = [(2, 3), (3, 2), (5, 0)]
result = list(starmap(pow, pairs))
manual = []
for base, exponent in pairs:
    manual.append(pow(base, exponent))
assert result == manual == [8, 9, 1]
assert list(starmap(pow, [])) == []
print(result)
```

`starmap(function, iterable)` 每次取出一项，再用 `function(*item)` 调用函数。第一项 `(2, 3)` 变成 `pow(2, 3)`。相比之下，普通 map 会把这一整个元组当作一个实参传入。

每项长度必须满足被调用函数的参数要求。例如给 pow 传 `(2,)`，只有底数，没有指数，会在实际取结果时抛 TypeError；starmap 不负责替你补参数。

10.4 tee：分出读取进度，不是复制所有元素对象

```python
# runnable: hb23_tee
from itertools import tee

first, second = tee(iter([10, 20, 30]), 2)
assert next(first) == 10
assert next(first) == 20
assert next(second) == 10
assert list(first) == [30]
assert list(second) == [20, 30]

shared = []
left, right = tee(iter([shared]))
next(left).append(1)
assert next(right) == [1]
assert tee([1, 2], 0) == ()
print("两份进度独立，元素引用仍共享")
```

`tee(iterable, n=2)` 返回 n 个迭代器。快的一份已经读到 20，慢的一份还停在 10 时，tee 需要暂存慢的一份尚未读过的数据，所以进度相差越大，缓存可能越大。

不要在 tee 之后继续从原迭代器直接取数；那会绕开分流过程。tee 也不是线程安全队列。若一份要先把全部数据读完，另一份很久之后才开始，直接 list 保存一份数据通常更直观。

---

11）完整例子：把几行日志汇成接口统计

11.1 先写清输入约定和各工具的职责

每行包含三项，用空白分开：接口路径、HTTP 状态码、耗时毫秒。例子只接受以 `/` 开头的路径、100 到 599 的整数状态码、非负整数耗时；格式不对的行记入错误列表，不把整批处理中断。

这不是完整日志协议解析器，只处理这里明确给出的三列格式。真实日志带时间、引号字段、多行异常时，应该先约定或采用相应格式，不能直接拿 split 硬拆所有文本。

| 保存什么 | 容器 | 原因 |
| --- | --- | --- |
| 每个接口的耗时列表 | defaultdict(list) | 新接口第一次出现时需要空列表 |
| 每种状态码出现次数 | Counter | 每读到一个状态码就加一 |
| 每个接口出错次数 | Counter | 状态码大于等于 400 时加一 |
| 最近三条有效记录 | deque(maxlen=3) | 追加新记录时自动淘汰旧记录 |
| 按接口排序后的明细 | groupby | 相邻同接口记录汇成一个明细组 |

11.2 从解析到报告，整个脚本可以单独运行

```python
# runnable: hb23_log_aggregation
from collections import Counter, defaultdict, deque
from itertools import groupby

lines = [
    "/users 200 10",
    "/orders 500 40",
    "/users 200 20",
    "bad",
    "/orders 200 20",
    "/users 404 30",
]

def parse_line(line):
    parts = line.split()
    if len(parts) != 3:
        raise ValueError("需要路径、状态码、耗时三项")
    path, raw_status, raw_duration = parts
    status = int(raw_status)
    duration = int(raw_duration)
    if not path.startswith("/"):
        raise ValueError("路径必须以 / 开头")
    if not 100 <= status <= 599:
        raise ValueError("状态码不在 100 到 599 范围内")
    if duration < 0:
        raise ValueError("耗时不能为负数")
    return path, status, duration

durations = defaultdict(list)
status_counts = Counter()
error_counts = Counter()
recent = deque(maxlen=3)
valid = []
invalid = []
snapshots = []

for line_number, line in enumerate(lines, start=1):
    try:
        path, status, duration = parse_line(line)
    except ValueError as error:
        invalid.append((line_number, str(error)))
        continue

    record = (path, status, duration)
    valid.append(record)
    durations[path].append(duration)
    status_counts[status] += 1
    if status >= 400:
        error_counts[path] += 1
    recent.append(record)
    snapshots.append((line_number, dict(status_counts), list(recent)))

report = {}
for path, values in durations.items():
    report[path] = {
        "count": len(values),
        "total_ms": sum(values),
        "average_ms": sum(values) / len(values),
        "errors": error_counts[path],
    }

detail = {}
for path, group in groupby(sorted(valid, key=lambda row: row[0]),
                           key=lambda row: row[0]):
    detail[path] = [(status, duration) for _, status, duration in group]

assert dict(durations) == {"/users": [10, 20, 30], "/orders": [40, 20]}
assert dict(status_counts) == {200: 3, 500: 1, 404: 1}
assert status_counts.total() == 5
assert invalid == [(4, "需要路径、状态码、耗时三项")]
assert report == {
    "/users": {"count": 3, "total_ms": 60, "average_ms": 20.0, "errors": 1},
    "/orders": {"count": 2, "total_ms": 60, "average_ms": 30.0, "errors": 1},
}
assert list(recent) == [
    ("/users", 200, 20), ("/orders", 200, 20), ("/users", 404, 30),
]
assert detail == {
    "/orders": [(500, 40), (200, 20)],
    "/users": [(200, 10), (200, 20), (404, 30)],
}
assert snapshots[0] == (1, {200: 1}, [("/users", 200, 10)])
assert snapshots[2][1] == {200: 2, 500: 1}
assert len(snapshots) == 5

for path, summary in report.items():
    print(path, summary)
print("状态码次数:", status_counts.most_common())
print("无效行:", invalid)
print("最近三条:", list(recent))
```

11.3 按输入逐步检查，不要只盯最终报告

| 读到第几行 | 关键变化 | 200 的次数 | 最近记录保留的原行号 |
| --- | --- | --- | --- |
| 1 | 创建 /users 分组，加入耗时 10 | 1 | 1 |
| 2 | 创建 /orders 分组，记录一次 500 错误 | 1 | 1、2 |
| 3 | /users 分组已有列表，继续追加 20 | 2 | 1、2、3 |
| 4 | 三列校验失败，记入 invalid 后 continue | 2 | 1、2、3 |
| 5 | 加入新记录时，行 1 从 recent 左端离开 | 3 | 2、3、5 |
| 6 | 新增 404 次数，行 2 从 recent 左端离开 | 3 | 3、5、6 |

report 里用 len(values) 做除数不会遇到空组，因为 durations 只在解析成功后追加时创建分组。若在别处随手访问了一个不存在的 durations 键，制造了空列表，这个假设就会失效——这也是前面强调“方括号读取可能新增键”的原因。

本例为了展示分组明细保存了 valid 和各接口的全部耗时。面对很大输入、只需要次数和平均值时，可以改成每个接口只存 count 和 total，最后 total/count；这样不必把每条耗时都保留。是否节省内存由实际保存的数据决定，不是导入 itertools 就自然变省。

---

12）练习与参考答案

12.1 练习一：规范化标签并统计次数

输入 `[" Python ", "java", "PYTHON", "", "  ", "Java"]`。先去两边空白并忽略大小写，空字符串不要计入；给出出现最多的两个标签。相同次数按首次出现顺序保留。

参考答案：

```python
# runnable: hb23_exercise_counter
from collections import Counter

raw_tags = [" Python ", "java", "PYTHON", "", "  ", "Java"]
normalized = []
for raw in raw_tags:
    tag = raw.strip().casefold()
    if tag:
        normalized.append(tag)
counts = Counter(normalized)
assert normalized == ["python", "java", "python", "java"]
assert counts.most_common(2) == [("python", 2), ("java", 2)]
assert Counter([]).most_common(2) == []
print(counts.most_common(2))
```

先规范化再统计，否则 Python、PYTHON 和带空白的字符串会被当成三个不同的键。Counter 不知道哪些文本在业务含义上“应该算同一个”。

12.2 练习二：每次给出最近三项的平均值

输入 `[10, 20, 30, 40]`，依次得到 `[10.0, 15.0, 20.0, 30.0]`。前两次不足三项时，用当前实际项数作除数；空输入返回空列表。要求维护滚动总和，不要每次重新 sum 整个队列。

参考答案：

```python
# runnable: hb23_exercise_moving_average
from collections import deque

def moving_averages(values, size=3):
    if size <= 0:
        raise ValueError("窗口大小必须大于 0")
    window = deque(maxlen=size)
    total = 0
    result = []
    for value in values:
        if len(window) == size:
            total -= window[0]
        window.append(value)
        total += value
        result.append(total / len(window))
    return result

assert moving_averages([10, 20, 30, 40]) == [10.0, 15.0, 20.0, 30.0]
assert moving_averages([]) == []
assert moving_averages([10, 20], size=1) == [10.0, 20.0]
try:
    moving_averages([1], size=0)
except ValueError:
    pass
else:
    raise AssertionError("零大小窗口应被拒绝")
print(moving_averages([10, 20, 30, 40]))
```

第四项 40 到来前，total 是 60，窗口是 `[10, 20, 30]`。先减去即将离开的 10，得到 50；追加 40 后再加上它，得到 90。窗口实际变成 `[20, 30, 40]`，90/3=30。

12.3 练习三：同名事件要合并，但不能覆盖前面的组

输入 `[('b', 1), ('a', 2), ('b', 3), ('a', 4)]`，使用 groupby 得到 `{'a': 6, 'b': 4}`。请解释为什么直接对原输入 groupby 后转成 dict 不可靠。

参考答案：

```python
# runnable: hb23_exercise_groupby
from itertools import groupby

events = [("b", 1), ("a", 2), ("b", 3), ("a", 4)]
wrong = {
    key: sum(value for _, value in group)
    for key, group in groupby(events, key=lambda row: row[0])
}
assert wrong == {"b": 3, "a": 4}

ordered = sorted(events, key=lambda row: row[0])
right = {
    key: sum(value for _, value in group)
    for key, group in groupby(ordered, key=lambda row: row[0])
}
assert ordered == [("a", 2), ("a", 4), ("b", 1), ("b", 3)]
assert right == {"a": 6, "b": 4}
assert list(groupby([])) == []
print(right)
```

原输入依次形成 b、a、b、a 四个相邻组；转成字典时，后面的 b 覆盖前面的 b，后面的 a 覆盖前面的 a。groupby 没算错，是我们错误地把“相邻分组”当成了“全体合并”。

---

13）本章对应的官方资料

[Python 3.11 collections：defaultdict、Counter、deque](https://docs.python.org/3.11/library/collections.html)

[Python 3.11 itertools：迭代工具及参数](https://docs.python.org/3.11/library/itertools.html)

[Python 3.11 queue：线程间同步队列](https://docs.python.org/3.11/library/queue.html)
