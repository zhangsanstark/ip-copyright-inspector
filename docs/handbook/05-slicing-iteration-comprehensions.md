05 · 切片、遍历、zip 与推导式

这一章把“怎么依次取数据”讲清楚。切片按位置选择，迭代器按进度取下一项，zip 把多份输入配对，推导式把一个简单循环收进表达式。它们看起来都能少写几行，却不是同一种执行过程。

在仓库根目录运行 `python scripts/check_handbook_examples.py --chapter 05 --show-output`。每块例子可独立执行，先猜 assert 后面的结果，再运行。

---

1）切片的三个位置：start、stop、step

1.1 正向切片先看下标，不要先数值

`sequence[start:stop:step]` 表示从起点按步长选择，遇到不包含的终点边界就停。省略 step 时为 1。它选择的是下标，所以列表里的值是不是连续数字并不重要。

```python
# runnable: hb05_positive_slice
letters = ["a", "b", "c", "d", "e", "f"]
assert letters[1:4] == ["b", "c", "d"]
assert letters[:3] == ["a", "b", "c"]
assert letters[3:] == ["d", "e", "f"]
assert letters[::2] == ["a", "c", "e"]
selected = []
for index in range(1, 4):
    selected.append(letters[index])
assert selected == letters[1:4]
print(selected)
```

`[1:4]` 依次访问下标 1、2、3，最后一个下标 4 不取。边界都合法、步长为 1 时，长度可以用 stop-start 算；反向、越界或起点超过终点时，不能直接套这个减法。

1.2 负下标只是从末尾数位置

```python
# runnable: hb05_negative_indexes
letters = list("abcdef")
assert letters[-1] == "f"
assert letters[-2:] == ["e", "f"]
assert letters[:-2] == ["a", "b", "c", "d"]
assert letters[-4:-1] == ["c", "d", "e"]
assert letters[-4:-1] == letters[2:5]
print(letters[-4:-1])
```

长度为 6 时，下标 -4 对应 2，-1 对应 5。负下标不自动表示反向；上面的步长仍为正，所以仍从左向右取。

1.3 负步长才表示向左走

```python
# runnable: hb05_reverse_slice
text = "abcdef"
assert text[4:1:-1] == "edc"
assert list(range(4, 1, -1)) == [4, 3, 2]
assert text[::-1] == "fedcba"
assert text[1:4:-1] == ""
assert text[5:-1:-1] == ""
assert text[5::-1] == "fedcba"
print(text[4:1:-1], text[::-1])
```

`[4:1:-1]` 访问 4、3、2，在 1 前停。`[1:4:-1]` 则起点已经位于终点左侧，不满足继续向左取值的条件，所以直接空结果，不会交换边界。

省略负步长的 stop 与明确写 -1 不同。`[5:-1:-1]` 的 -1 被解释成最后一个实际下标 5，起终点重合，什么都不取；`[5::-1]` 的省略终点让它一直走过开头。

---

2）省略与越界：切片会调整边界

2.1 默认值随方向改变

| 省略位置 | step 为正 | step 为负 |
| --- | --- | --- |
| start | 从开头开始 | 从末尾开始 |
| stop | 走到末尾之后的边界 | 走到开头之前的边界 |
| step | 默认 1 | 要反向必须明确给负数 |

默认边界是给算法用的停止位置，不是说你可以用那个越界下标单独取元素。

```python
# runnable: hb05_slice_edges
values = [0, 1, 2, 3, 4]
assert values[100:200] == []
assert values[-100:3] == [0, 1, 2]
assert values[4:1] == []
assert values[-100:100] == values
assert [][::-1] == []
try:
    values[::0]
except ValueError:
    pass
else:
    raise AssertionError("zero step")
try:
    values[100]
except IndexError:
    pass
else:
    raise AssertionError("single index still fails")
print(values[100:200])
```

切片“通常安全截断”不等于任何参数都可接受。步长不能为 0，位置也需要满足索引协议，不能随意传小数或字符串。

2.2 slice 对象可以保存一段选择规则

```python
# runnable: hb05_slice_object
text = "abcdef"
rule = slice(1, 5, 2)
assert text[rule] == "bd"
assert (rule.start, rule.stop, rule.step) == (1, 5, 2)
reverse_rule = slice(None, None, -1)
normalized = reverse_rule.indices(len(text))
assert normalized == (5, -1, -1)
positions = list(range(*normalized))
assert positions == [5, 4, 3, 2, 1, 0]
assert "".join(text[index] for index in positions) == text[reverse_rule]
print(normalized, positions)
```

`slice.indices(length)` 把省略值、负下标和越界情况换算成可供 range 使用的边界。这里返回的 -1 是归一化后的停止哨位，不要再拿它直接塞回 `[5:-1:-1]`，否则又被当成“最后一项”解释。

---

3）列表切片赋值：选择一段与替换一段

3.1 普通步长可以改变长度

```python
# runnable: hb05_slice_assignment
values = [0, 1, 2, 3]
alias = values
values[1:3] = [8, 9, 10]
assert values == [0, 8, 9, 10, 3]
assert alias is values
values[1:4] = []
assert values == [0, 3]
values[1:1] = [7]
assert values == [0, 7, 3]
print(values)
```

先选中旧 `[1, 2]`，再整段换成三项，所以长度增加。右边空列表表示删掉这段；左右边界相等是空区间，赋值相当于在这个位置插入。

3.2 隔位赋值要求数量一一对应

```python
# runnable: hb05_extended_assignment
values = [0, 1, 2, 3, 4]
values[::2] = [10, 20, 30]
assert values == [10, 1, 20, 3, 30]
try:
    values[::2] = [99]
except ValueError:
    pass
else:
    raise AssertionError("three positions need three values")
del values[::2]
assert values == [1, 3]
print(values)
```

步长不为 1 时，赋值是在替换多个分散位置，新元素数量必须匹配；但 del 可以直接删除选中的这些位置。字符串和元组支持读取切片，不支持这种原地赋值。

3.3 切片复制只有外层新了

```python
# runnable: hb05_slice_copy
source = [[1], [2]]
copied = source[:]
assert copied is not source
assert copied[0] is source[0]
copied[0].append(9)
assert source[0] == [1, 9]
print(source)
```

切片读出的列表是浅拷贝。不要看到 `[:]` 就以为已经隔开所有嵌套内容，这与第 03 章的 copy 是同一类问题。

---

4）可迭代对象与迭代器：能重新开始，还是已经读到一半

4.1 iter 拿到进度，next 推进一步

```python
# runnable: hb05_iterator_state
values = [10, 20]
cursor = iter(values)
assert next(cursor) == 10
assert list(cursor) == [20]
assert list(cursor) == []
assert list(values) == [10, 20]
assert list(iter(values)) == [10, 20]
assert next(cursor, "finished") == "finished"
print(list(values))
```

列表保存数据，能重新创建新的迭代器；迭代器保存当前进度，读完不会自动回到开头。`next(iterator, default)` 在耗尽时返回 default；不提供默认值则抛 StopIteration，for 会自动处理这个结束信号。

4.2 in 用在迭代器上，也会消耗它

```python
# runnable: hb05_membership_consumes
cursor = iter([1, 2, 3, 4])
assert 2 in cursor
assert list(cursor) == [3, 4]
cursor = iter([1, 2])
assert 9 not in cursor
assert list(cursor) == []
assert "py" in "python"
assert "aa" not in ("a", "b")
assert "name" in {"name": "Ada"}
print("membership can consume an iterator")
```

为了判断 2 是否存在，它先读了 1、再读 2；这些项已被取走。对无限输入查找一个永远不存在的值，就可能永不结束。容器里的 in 通常不会这样销毁自己的数据，不能把两种对象混着理解。

---

5）range、enumerate 与容器转换

5.1 range 是整数范围，不是预先做好的大列表

```python
# runnable: hb05_range
assert list(range(4)) == [0, 1, 2, 3]
assert list(range(2, 8, 2)) == [2, 4, 6]
assert list(range(5, 0, -2)) == [5, 3, 1]
assert list(range(5, 0)) == []
numbers = range(0, 10, 2)
assert numbers[2] == 4
assert len(numbers) == 5
assert 6 in numbers
assert list(numbers) == list(numbers)
try:
    range(0, 10, 0)
except ValueError:
    pass
else:
    raise AssertionError("zero range step")
print(list(numbers))
```

一个参数表示 stop，两个参数表示 start、stop，第三个表示 step；都不含 stop。range 是可重复遍历的范围对象，支持长度和下标，不是一次性生成器。把它转成 list 才真正收集所有数字，占用相应内存。

5.2 enumerate 的 start 只是计数起点

```python
# runnable: hb05_enumerate
names = ["Ada", "Lin"]
numbered = list(enumerate(names, start=1))
assert numbered == [(1, "Ada"), (2, "Lin")]
assert names[0] == "Ada"
manual = []
number = 1
for name in names:
    manual.append((number, name))
    number += 1
assert manual == numbered
print(numbered)
```

它没有从列表下标 1 开始读，也没有把列表下标改成从 1 开始。处理文件行号时，start=1 很实用，因为给人看的行号通常从 1 数。

5.3 转换会丢掉什么信息

```python
# runnable: hb05_conversions
values = [3, 1, 3, 2]
assert tuple(values) == (3, 1, 3, 2)
assert set(values) == {1, 2, 3}
assert list("ab") == ["a", "b"]
assert list({"a": 1, "b": 2}) == ["a", "b"]
assert list(dict.fromkeys(values)) == [3, 1, 2]
assert sorted(set(values)) == [1, 2, 3]
print(list(dict.fromkeys(values)))
```

转集合去掉重复，也不保留原出现顺序；sorted(set(...)) 是排序后去重结果，不是保序去重。dict.fromkeys 借助键唯一且保留插入顺序的性质留下首次出现，但要求元素可哈希。

5.4 max 与 min：找极值，不是先排序才能取

有两种常见调用方式：一个可迭代对象，或至少两个分开的值。返回的是其中一个原元素，不会把整个输入排好再交回来。

```python
# runnable: hb05_extrema_signatures
values = [3, 9, 2, 9]
assert max(values) == 9
assert min(values) == 2
assert max(3, 9, 2) == 9
assert min(3, 9, 2) == 2
assert values == [3, 9, 2, 9]
assert max("cab") == "c"
assert min((5, 2, 8)) == 2
try:
    max(3)
except TypeError:
    print("只传一项时，这一项需要能被遍历")
else:
    raise AssertionError("整数 3 不是可迭代输入")
```

把 `max([3, 9, 2])` 展开理解：先把 3 当候选，看到 9 比当前候选大，就换成 9；看到 2 没有更大，就保留 9。它通常只需顺着扫描，不会改变列表顺序。

`max(3)` 不是“只有一个候选 3，所以返回 3”。单实参形式把这个实参当作可迭代对象；想表达一个元素的集合，写 `max([3])`。

5.5 空输入要明确处理，default 只属于可迭代对象形式

```python
# runnable: hb05_extrema_empty
assert max([], default=0) == 0
assert min([], default=None) is None
assert max([3, 5], default=100) == 5
assert min([], key=len, default=None) is None

for function in (max, min):
    try:
        function([])
    except ValueError:
        print(function.__name__, "没有元素，也没有默认结果")
    else:
        raise AssertionError("空输入应该失败")

try:
    max(3, 5, default=0)
except TypeError:
    pass
else:
    raise AssertionError("多个分开实参不接受 default")
```

default 是“一个元素都没有时返回什么”，不是参与竞争的额外候选。因此 `max([3, 5], default=100)` 仍然是 5。空输入返回默认值时也不需要先对它执行 key，所以这里 default=None、key=len 并不报错。

返回 None 还是 0 取决于业务：没有任何金额不一定代表最高金额为零。你要区分“没有数据”和“确实为零”时，None 往往更明确。

5.6 key 决定比较标准，返回的仍是原对象

```python
# runnable: hb05_extrema_key
records = [{"name": "A", "score": 80}, {"name": "B", "score": 95},
           {"name": "C", "score": 95}]
best = max(records, key=lambda record: record["score"])
assert best is records[1]
assert best == {"name": "B", "score": 95}
assert min(["long", "a", "bb"], key=len) == "a"

counts = {"z": 1, "a": 10}
assert max(counts) == "z"
assert max(counts.values()) == 10
assert max(counts, key=counts.get) == "a"
```

B、C 同为 95，max 保留先遇到的 B，不会因为后面又看到相同分数就替换。集合没有业务上稳定的先后，若并列也需要稳定选择，应提供完整比较规则或顺序明确的输入。

字典默认迭代的是键，所以 `max(counts)` 比较 `"z"` 与 `"a"`。`max(counts, key=counts.get)` 用各键对应的值比较，但最后返回获胜的键 `"a"`，不是数字 10。

5.7 元素之间必须能按你的规则比较

```python
# runnable: hb05_extrema_mixed
try:
    max([3, "20"])
except TypeError:
    print("整数和字符串不能直接按大小混比")
else:
    raise AssertionError("应该出现类型错误")
assert max([3, "20"], key=int) == "20"
assert max(int(value) for value in [3, "20"]) == 20
```

前一个 key 版本只把比较键转成整数，返回的还是原字符串 `"20"`。后一个先把输入项真正转换，返回值才是整数 20。这个差异与排序的 key 一样，理解一次可以通用。

如果可能出现 `"bad"`，int 转换仍会失败，需要另行校验；key 不是万能的脏数据清洗器。浮点 NaN 等特殊值也应按业务先处理，不能把它们与普通数字完全等同。

5.8 加号合并：序列类型要对应，是否改原对象要另看

```python
# runnable: hb05_sequence_concat
left = [1, 2]
right = [3, 4]
combined = left + right
assert combined == [1, 2, 3, 4]
assert left == [1, 2] and right == [3, 4]
assert combined is not left and combined is not right
assert "ip-" + "check" == "ip-check"
assert (1, 2) + (3,) == (1, 2, 3)

alias = left
left += [5]
assert alias is left
assert alias == [1, 2, 5]
try:
    [1, 2] + (3, 4)
except TypeError:
    pass
else:
    raise AssertionError("列表不能直接与元组相加")
```

列表加列表产生新列表；字符串加字符串产生拼接结果；元组加元组产生拼接元组。不会因为两边都“像一组数据”，就把 list 和 tuple 自动混合。

列表 `+=` 则会原地扩展，其他指向原列表的名字也能看到变化，接近 extend 的用途。字符串和元组不可变，它们的 `+=` 是计算结果后重新绑定，不能原地扩展同一个对象。

字典不能用加号合并；第 4 章用 update 或合并运算说明覆盖规则。集合也不用加号合并，而是用并集。操作符看起来一样，不代表所有容器都支持。

5.9 乘号重复：重复次数与复制深度是两回事

```python
# runnable: hb05_sequence_repeat
assert "ab" * 3 == "ababab"
assert 2 * [1, 2] == [1, 2, 1, 2]
assert (1, 2) * 2 == (1, 2, 1, 2)
assert "ab" * 0 == ""
assert [1, 2] * -3 == []
assert (1, 2) * 0 == ()

inner = [0]
repeated = [inner] * 2
assert repeated[0] is repeated[1]
repeated[0].append(1)
assert repeated == [[0, 1], [0, 1]]
```

零次或负次数得到相应的空序列，不会表示“倒着重复”。次数需要整数意义的值，不能用 2.5 表示复制两次半。

重复的是元素引用，不是递归复制元素。这里两项都指向 inner，改一处就看见两处一起变。第 3 章的独立二维表格用每轮新建列表来避免这个问题。

5.10 in / not in：问成员，字符串则支持子串判断

```python
# runnable: hb05_membership_meaning
assert "aa" in "baab"
assert "aa" not in ("a", "a", "b")
assert "aa" in ("aa", "b")
assert [1, 2] in [[1, 2], [3]]
assert 1 not in [[1, 2], [3]]
assert "name" in {"name": "周"}
assert "周" not in {"name": "周"}
assert "周" in {"name": "周"}.values()
assert "a" in {"a", "b"}
```

字符串问“有没有这段连续子串”；列表和元组通常按整体元素比较，不把嵌套内容自动拆平。字典默认问键是否存在，查值要明确使用 values。

not in 是这个成员判断的否定，不是另一套查找规则。对迭代器查成员还可能消耗输入，前面第 4.2 节已经给出过程；对无限迭代器查一个永远不存在的值，可能永远查不完。

---

6）zip：每份输入各拿一项，凑成一组

6.1 配对不是相加，也不是所有组合

```python
# runnable: hb05_zip_basic
names = ["Ada", "Lin"]
scores = [95, 88]
pairs = list(zip(names, scores))
assert pairs == [("Ada", 95), ("Lin", 88)]
manual = []
for index in range(min(len(names), len(scores))):
    manual.append((names[index], scores[index]))
assert manual == pairs
assert dict(pairs) == {"Ada": 95, "Lin": 88}
assert list(zip([1], [2], [3])) == [(1, 2, 3)]
print(pairs)
```

第一轮各拿第 0 项，第二轮各拿第 1 项。zip 支持多份输入，不限两份；即使每组只有一项，返回的每项仍是元组。普通展开需要能取长度和下标，而 zip 还支持生成器等更一般的可迭代对象。

6.2 默认按最短，结果对象一次性

```python
# runnable: hb05_zip_exhaustion
paired = zip([1, 2, 3], ["a", "b"])
assert next(paired) == (1, "a")
assert list(paired) == [(2, "b")]
assert list(paired) == []
assert list(zip([], [1, 2])) == []
assert list(zip()) == []
assert list(zip([1, 2])) == [(1,), (2,)]
print("zip stops at the shortest input")
```

zip 对象按需取值，list 只收集它剩下的结果。输入不等长时，较长的一侧多出的项不出现在配对结果；如果传入的是会被消费的迭代器，不应依赖它未匹配部分完全没被读取，因为探测结束时也可能取走一些值。

6.3 strict=True 让长度不一致变成错误

```python
# runnable: hb05_zip_strict
paired = zip([1, 2], ["a"], strict=True)
assert next(paired) == (1, "a")
try:
    next(paired)
except ValueError:
    pass
else:
    raise AssertionError("different lengths")
assert list(zip([], [], strict=True)) == []
assert list(zip([1, 2], [3, 4], strict=True)) == [(1, 3), (2, 4)]
print("length mismatch detected while consuming")
```

检查在取数据时发生，不是在创建 zip 的一瞬间先读完所有输入。第一组可能已成功交出来，第二组才发现缺项。所以它不是“先替你做全量校验再启动批处理”的事务工具。

6.4 zip_longest 明确保留长的一侧

```python
# runnable: hb05_zip_longest
from itertools import zip_longest

rows = list(zip_longest([1, 2, 3], ["a"], fillvalue=None))
assert rows == [(1, "a"), (2, None), (3, None)]
missing = object()
rows = list(zip_longest([None, 2], ["a"], fillvalue=missing))
assert rows[0] == (None, "a")
assert rows[1][1] is missing
print([(1, "a"), (2, None), (3, None)])
```

fillvalue 默认是 None。业务允许真实 None 时，独特的哨兵对象能区分“原本就是 None”与“缺失补位”。其中一份输入无限长时，zip_longest 也不会自动结束，需要明确截取范围。

6.5 zip(*rows) 为什么能按列拆开

```python
# runnable: hb05_unzip
rows = [("Ada", 95), ("Lin", 88)]
names, scores = zip(*rows)
assert names == ("Ada", "Lin")
assert scores == (95, 88)
assert list(zip(*rows)) == list(zip(("Ada", 95), ("Lin", 88)))
empty_rows = []
if empty_rows:
    empty_names, empty_scores = zip(*empty_rows)
else:
    empty_names, empty_scores = (), ()
assert empty_names == empty_scores == ()
print(names, scores)
```

星号先把两行展开成 zip 的两个参数，再由 zip 各取两行的第 0 项组成姓名列，各取第 1 项组成分数列。空输入不会自动产生两列空元组，要像这里明确处理。行长不一致时，默认仍按最短，必要时使用 strict。

---

7）列表推导式：先找 for，再看 if，最后看结果表达式

7.1 单层转换与普通循环

```python
# runnable: hb05_list_comprehension
values = [1, 2, 3]
manual = []
history = []
for value in values:
    result = value * value
    manual.append(result)
    history.append(manual.copy())
compact = [value * value for value in values]
assert compact == manual == [1, 4, 9]
assert history == [[1], [1, 4], [1, 4, 9]]
print(history)
```

最前面写“每轮产出什么”，for 后面写“从哪里来”。它不是先计算一个不知从哪来的 value，再开始循环，而是每轮先把 value 取出来。

7.2 末尾 if 是筛选，通过后才求结果

```python
# runnable: hb05_filter_comprehension
values = [2, 0, 4]
manual = []
for value in values:
    if value != 0:
        manual.append(1 / value)
compact = [1 / value for value in values if value != 0]
assert manual == compact == [0.5, 0.25]
assert [x * 2 for x in []] == []
assert [x for x in [1, 2] if x > 10] == []
print(compact)
```

0 在执行除法前已经被筛掉，所以没有除零错误。末尾条件回答“这项还要不要”；不通过时不是放一个 None，而是根本不追加。

7.3 前面的 if/else 选择替换值，不减少项数

```python
# runnable: hb05_conditional_expression
values = [-2, 0, 3]
manual = []
for value in values:
    if value > 0:
        chosen = value
    else:
        chosen = 0
    manual.append(chosen)
compact = [value if value > 0 else 0 for value in values]
assert compact == manual == [0, 0, 3]
assert len(compact) == len(values)
print(compact)
```

每个输入都走到一次 append，只是值由分支决定。把筛选式与三元表达式的位置放对，通常只需先用一句话说明：我要“删掉不符合的”，还是“把不符合的换成某个值”。

---

8）多层推导式：左边 for 是外层

8.1 两个范围产生所有组合

```python
# runnable: hb05_nested_comprehension
manual = []
for x in range(2):
    for y in range(3):
        manual.append((x, y))
compact = [(x, y) for x in range(2) for y in range(3)]
assert compact == manual == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
assert len(compact) == 6
assert len(list(zip(range(2), range(3)))) == 2
print(compact)
```

先固定 x=0，把 y 全跑完；再固定 x=1，又跑一轮。这个过程得到笛卡尔组合，不是 zip 的按位置配对。

8.2 内层输入可以依赖外层结果

```python
# runnable: hb05_flatten
matrix = [[1, 2], [], [3, 4]]
manual = []
for row in matrix:
    for value in row:
        manual.append(value)
compact = [value for row in matrix for value in row]
assert compact == manual == [1, 2, 3, 4]
positives = [value for row in matrix if row for value in row if value > 2]
assert positives == [3, 4]
print(compact, positives)
```

先有 row，内层才能遍历 row。外层后面的 if 筛行，内层后面的 if 筛元素。代码开始绕时，恢复成普通 for，省下的几行不值得换来读不懂的处理规则。

8.3 推导式循环变量不会泄漏到外面

```python
# runnable: hb05_comprehension_scope
value = "outside"
numbers = [value * 2 for value in range(3)]
assert numbers == [0, 2, 4]
assert value == "outside"
print(value)
```

这与普通 for 循环变量的行为不同。这里讨论的是普通推导式循环变量，不把所有复杂表达式的绑定规则都压成一句“括号里全有独立作用域”。

---

9）字典、集合与生成器表达式

9.1 字典推导式每轮写入一对键值

```python
# runnable: hb05_dict_comprehension
rows = [("Ada", 80), ("Lin", 88), ("Ada", 95)]
manual = {}
for name, score in rows:
    manual[name] = score
compact = {name: score for name, score in rows}
assert manual == compact == {"Ada": 95, "Lin": 88}
passed = {name: score for name, score in compact.items() if score >= 90}
assert passed == {"Ada": 95}
print(compact, passed)
```

重复键覆盖旧值，不会自动求平均或保存历史。想保留所有记录，应把值设计成列表，再逐项追加，而不是套一个字典推导式就结束。

9.2 集合推导式每轮 add，重复项不增长

```python
# runnable: hb05_set_comprehension
manual = set()
for value in range(7):
    manual.add(value % 3)
compact = {value % 3 for value in range(7)}
assert compact == manual == {0, 1, 2}
assert {x for x in []} == set()
assert type({}) is dict
print(sorted(compact))
```

0、1、2 加入后，再遇到相同余数不会新增成员。集合要求结果元素可哈希；生成列表元素时应使用列表推导式，不能把方括号随手换成花括号。

9.3 生成器表达式不是“元组推导式”

```python
# runnable: hb05_generator_expression
result = (value * value for value in range(3))
assert next(result) == 0
assert list(result) == [1, 4]
assert list(result) == []
tuple_result = tuple(value * value for value in range(3))
assert tuple_result == (0, 1, 4)
assert sum(value * value for value in range(3)) == 5
print(tuple_result)
```

圆括号产生按需取值的生成器对象；要元组需要 tuple 显式收集。求和时可直接消费生成器，不必先存一份完整结果列表。生成器的暂停和资源生命周期会在专门章节展开。

---

10）拆包与展开：左边收集，右边分发

10.1 同时赋值与星号接收

```python
# runnable: hb05_unpacking
a, b = 10, 20
a, b = b, a
assert (a, b) == (20, 10)
head, *body, tail = range(5)
assert head == 0 and body == [1, 2, 3] and tail == 4
head, *body, tail = [0, 4]
assert body == []
try:
    head, tail = [1, 2, 3]
except ValueError:
    pass
else:
    raise AssertionError("too many values")
print(head, body, tail)
```

右边先求值，再交给左边，所以交换无需临时变量。星号接收余项时得到列表，普通位置所需数量仍必须满足。

10.2 容器里的 * 与 ** 是展开输入

```python
# runnable: hb05_unpack_containers
left, right = [1, 2], [3, 4]
merged = [*left, *right]
assert merged == [1, 2, 3, 4]
base = {"timeout": 3, "debug": False}
override = {"timeout": 9}
config = {**base, **override}
assert config == {"timeout": 9, "debug": False}
assert base["timeout"] == 3
keys = tuple(base)
assert keys == ("timeout", "debug")
print(merged, config)
```

普通星号逐项展开可迭代对象；双星号在字典构造里展开键值对，后面的同名键覆盖前面的。函数调用中的星号还受参数规则限制，会在函数章节单独讲。

---

11）练习与参考答案

11.1 取出 8、6、4、2

题目：从 `list(range(10))` 用切片取出这四个数，解释停止位置为什么不能随便省略。

```python
# runnable: hb05_exercise_slice
values = list(range(10))
selected = values[8:0:-2]
assert selected == [8, 6, 4, 2]
assert values[8::-2] == [8, 6, 4, 2, 0]
print(selected)
```

明确 stop=0 才会排除下标 0；省略时会继续取到开头，所以多一个 0。

11.2 严格合并字段与值

题目：字段 `id、name` 对应 `7、Ada`，长度不一致时必须报错。

```python
# runnable: hb05_exercise_strict_record
def build_record(fields, values):
    return dict(zip(fields, values, strict=True))

assert build_record(["id", "name"], [7, "Ada"]) == {"id": 7, "name": "Ada"}
assert build_record([], []) == {}
try:
    build_record(["id", "name"], [7])
except ValueError:
    pass
else:
    raise AssertionError("field count mismatch")
print(build_record(["id"], [7]))
```

这个函数只构造本地结果，没有边遍历边执行外部写入。字段重复时后值仍会覆盖，strict 只检查长度，不检查键是否唯一。

11.3 扁平化后只保留正数平方

题目：输入 `[[1, -2], [], [0, 3]]`，输出 `[1, 9]`；分别用普通循环和推导式实现。

```python
# runnable: hb05_exercise_nested_filter
matrix = [[1, -2], [], [0, 3]]
manual = []
for row in matrix:
    for value in row:
        if value > 0:
            manual.append(value * value)
compact = [value * value for row in matrix for value in row if value > 0]
assert manual == compact == [1, 9]
print(compact)
```

---

12）查阅位置

切片和 range 的规则见 [Python 3.11 序列类型](https://docs.python.org/3.11/library/stdtypes.html#sequence-types-list-tuple-range)。iter、next、enumerate、zip 见 [内置函数](https://docs.python.org/3.11/library/functions.html)。推导式展开方式见 [数据结构教程](https://docs.python.org/3.11/tutorial/datastructures.html)，zip_longest 见 [itertools](https://docs.python.org/3.11/library/itertools.html#itertools.zip_longest)。
