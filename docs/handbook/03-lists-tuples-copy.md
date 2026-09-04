03 · 列表、元组与复制：每一步到底改了谁

一批订单、几条日志、一个坐标都能写成“多个值放在一起”，但容器的选择会影响修改方式。列表适合顺序可变的数据；元组常表示固定的一组值。复制则是第三个问题：新容器与旧容器，究竟共享了哪一层。

在仓库根目录运行 `python scripts/check_handbook_examples.py --chapter 03 --show-output`。每个 runnable 块独立，结果用 assert 核对。切片的完整规则放在第 05 章，本章先用于观察容器修改。

---

1）建立列表：有顺序，允许重复，也允许原地修改

1.1 方括号与 list(iterable)

```python
# runnable: hb03_create
empty = []
values = [10, 20, 10]
characters = list("ab")
from_tuple = list((1, 2))
assert empty == []
assert values == [10, 20, 10]
assert characters == ["a", "b"]
assert from_tuple == [1, 2]
assert list() == []
print(values, characters)
```

list 接收一个可迭代对象并逐项装入。`list("ab")` 不是得到 `["ab"]`；想放一个完整字符串，直接写 `["ab"]`。列表可以混放类型，但业务代码中把同类数据放一起，通常更清楚。

1.2 下标从零开始，负下标从末尾数

```python
# runnable: hb03_indexing
items = ["first", "middle", "last"]
assert items[0] == "first"
assert items[-1] == "last"
assert items[-2] == "middle"
assert len(items) == 3
for index in [3, -4]:
    try:
        items[index]
    except IndexError:
        pass
    else:
        raise AssertionError(index)
print(items[-1])
```

空列表没有第 0 项，也没有第 -1 项。下标访问必须对应真实位置；切片可以得到空列表，不能由此推断单下标访问也会自动给空值。

---

2）添加：append、extend、insert 不是三个同义词

2.1 append(x) 把 x 当成一个元素

```python
# runnable: hb03_append
items = [1, 2]
returned = items.append([3, 4])
assert items == [1, 2, [3, 4]]
assert len(items) == 3
assert items[-1] == [3, 4]
assert returned is None
items.append("ab")
assert items[-1] == "ab"
print(items)
```

先有两项，再加一份列表对象，总长度是 3，不是 4。append 返回 None，因为修改已经发生在原列表上，不需要通过返回值再交回一个列表。

2.2 extend(iterable) 每取到一项，追加一项

```python
# runnable: hb03_extend
items = [1, 2]
returned = items.extend([3, 4])
assert items == [1, 2, 3, 4]
assert returned is None
items.extend("ab")
assert items == [1, 2, 3, 4, "a", "b"]
items.extend([])
assert len(items) == 6
expanded = [1, 2]
history = []
for value in [3, 4]:
    expanded.append(value)
    history.append(expanded.copy())
assert history == [[1, 2, 3], [1, 2, 3, 4]]
print(history)
```

普通循环展示的是这两份独立列表的扩展过程。这里 history 每次存一个浅拷贝，才能留下“那一轮”的状态；若一直保存 expanded 本身，最后看到的可能全是同一份最终列表。

如果输入迭代到一半失败，已经追加的元素不一定自动撤回。所以 extend 不是事务；需要全部成功后再修改时，可以先把输入收集好并校验。

2.3 insert(index, value) 插到该位置之前

```python
# runnable: hb03_insert
items = [10, 20, 30]
assert items.insert(1, 99) is None
assert items == [10, 99, 20, 30]
items.insert(100, 40)
assert items[-1] == 40
items.insert(-100, 0)
assert items[0] == 0
print(items)  # [0, 10, 99, 20, 30, 40]
```

插入不是覆盖，旧元素会后移。超出末尾的插入位置落到尾部，过小的负位置落到开头；这与 `items[100] = value` 会越界不同。大量在头部插入或删除会移动很多元素，队列通常改用 deque。

---

3）删除：按位置、按值、清空、删名字

3.1 pop(index=-1) 删除并返回被删元素

```python
# runnable: hb03_pop
items = [10, 20, 30]
last = items.pop()
first = items.pop(0)
assert last == 30 and first == 10
assert items == [20]
assert items.pop(-1) == 20
try:
    items.pop()
except IndexError:
    pass
else:
    raise AssertionError("empty list")
assert items == []
print(last, first)
```

下标默认为 -1，所以常用于从尾部取一项。它与 Java 中可能按参数类型区分重载的方法不同：这里 `pop(20)` 是删下标 20，不是删值 20。

3.2 remove(value) 只删第一个相等的值

```python
# runnable: hb03_remove
items = [10, 20, 20, 30]
assert items.remove(20) is None
assert items == [10, 20, 30]
try:
    items.remove(99)
except ValueError:
    pass
else:
    raise AssertionError("value is missing")
print(items)
```

remove 用相等关系找值，找到第一项就结束；不会因为名字叫 remove 就自动删光所有重复项。需要删光时，建立筛选后的列表通常更稳妥。

3.3 del 与 clear

```python
# runnable: hb03_del_clear
items = [0, 1, 2, 3]
alias = items
del items[1:3]
assert items == [0, 3]
assert items.clear() is None
assert alias == []
del items
assert alias == []
try:
    items
except NameError:
    pass
else:
    raise AssertionError("name should be gone")
print(alias)
```

del 是语句，可以删除某项、一个切片或变量绑定。clear 是列表方法，清空原对象但保留它；另一个引用也会看到空列表。`del items` 则让这个名字不再可用，不保证对象立刻消失，因为 alias 仍然引用它。

---

4）修改、查找和遍历

4.1 下标赋值与切片赋值

```python
# runnable: hb03_assign
items = [10, 20, 30]
items[1] = 99
assert items == [10, 99, 30]
items[0:2] = [1, 2, 3]
assert items == [1, 2, 3, 30]
try:
    items[100] = 8
except IndexError:
    pass
else:
    raise AssertionError("assignment cannot create missing indexes")
print(items)
```

单位置赋值替换那个位置，不自动补齐空缺下标；连续切片赋值则是整段替换，可以改变长度。列表操作通常没有数据库式回滚，要清楚哪一步已经修改成功。

4.2 index、count、in、len

`items.index(value, start, stop)` 找第一个相等值的位置，可限定不含 stop 的查找范围，返回原列表下标；找不到抛 ValueError。count 统计相等值的次数；in 只回答有没有；len 返回项数。

```python
# runnable: hb03_lookup
items = [10, 20, 10, 30]
assert items.index(10) == 0
assert items.index(10, 1) == 2
assert items.count(10) == 2
assert items.count(99) == 0
assert 20 in items and 99 not in items
assert len(items) == 4
try:
    items.index(10, 1, 2)
except ValueError:
    pass
else:
    raise AssertionError("excluded occurrence")
print(items.index(10, 1), items.count(10))
```

这几个操作返回的不是同一种信息。尤其不能拿 `index()` 的异常去理解 `count()`，后者找不到就是 0。

4.3 for 与 while 的状态差别

```python
# runnable: hb03_traversal
items = [10, 20, 30]
with_for = []
for value in items:
    with_for.append(value * 2)
with_while = []
index = 0
while index < len(items):
    with_while.append(items[index] * 2)
    index += 1
assert with_for == with_while == [20, 40, 60]
assert list(enumerate(items, start=1)) == [(1, 10), (2, 20), (3, 30)]
print(with_for)
```

for 替你取下一项；while 则要自己检查边界、读下标、推进下标。没有特别的控制需求时，for 更少出错。enumerate 的 start 只改变计数，不改变列表真实下标。

4.4 边遍历边删除，为什么会漏项

```python
# runnable: hb03_mutation_during_iteration
wrong = [1, 1, 2]
for value in wrong:
    if value == 1:
        wrong.remove(value)
assert wrong == [1, 2]
source = [1, 1, 2]
kept = []
for value in source:
    if value != 1:
        kept.append(value)
assert kept == [2]
alias = source
source[:] = kept
assert alias == [2]
print(wrong, kept)
```

第一次删除后，第二个 1 左移到下标 0；循环却接着读下标 1，直接看到 2。用新结果列表避免在遍历过程中改变位置。最后切片赋值把新内容放回原对象，因此 alias 也看到更新。

---

5）排序和反转：顺序怎么产生，结果放在哪里

5.1 sort 与 sorted

`items.sort(key=None, reverse=False)` 原地排序并返回 None。`sorted(iterable, key=None, reverse=False)` 接受任意可迭代对象，返回一个新列表。key 与 reverse 用关键字传，避免把含义写模糊。

```python
# runnable: hb03_sort_variants
items = [3, 1, 2]
ordered = sorted(items)
assert ordered == [1, 2, 3]
assert items == [3, 1, 2]
assert items.sort(reverse=True) is None
assert items == [3, 2, 1]
assert sorted((3, 1, 2)) == [1, 2, 3]
assert sorted([]) == []
print(items, ordered)
```

不要写 `items = items.sort()`，会把名字指向 None。数据类型混杂、不能互相比大小时，排序可能报 TypeError；先统一数据，或提供能统一比较的 key。

5.2 key 是单项映射，不是两项比较器

```python
# runnable: hb03_sort_keys
users = [
    {"name": "A", "score": 90, "age": 30},
    {"name": "B", "score": 95, "age": 31},
    {"name": "C", "score": 95, "age": 25},
]
def user_key(user):
    return -user["score"], user["age"]

keys = [user_key(user) for user in users]
assert keys == [(-90, 30), (-95, 31), (-95, 25)]
ordered = sorted(users, key=user_key)
assert [user["name"] for user in ordered] == ["C", "B", "A"]
assert users[0]["score"] == 90
print(keys, [user["name"] for user in ordered])
```

金额/分数等数值前加负号，只反转那个字段的次序，不修改原对象。元组从第一项开始比，相等再比第二项；字符串不能简单加负号。

5.3 稳定排序可以分两次表达不同方向

```python
# runnable: hb03_stable_sort
records = [("beta", 1), ("alpha", 2), ("beta", 0)]
by_second = sorted(records, key=lambda row: row[1])
result = sorted(by_second, key=lambda row: row[0], reverse=True)
assert by_second == [("beta", 0), ("beta", 1), ("alpha", 2)]
assert result == [("beta", 0), ("beta", 1), ("alpha", 2)]
ties = [("first", 2), ("second", 2), ("third", 1)]
assert sorted(ties, key=lambda row: row[1]) == [("third", 1), ("first", 2), ("second", 2)]
print(result)
```

先排次要字段，再排主要字段；第二次排序遇到相同主键时，会保留第一次排好的相对顺序。这比发明一个难懂的复合比较器更直观。

5.4 reverse、reversed、[::-1]

```python
# runnable: hb03_reverse
items = [2, 1, 3]
copy = items[::-1]
iterator = reversed(items)
assert copy == [3, 1, 2]
assert list(iterator) == [3, 1, 2]
assert list(iterator) == []
assert items == [2, 1, 3]
assert items.reverse() is None
assert items == [3, 1, 2]
print(items)
```

reverse 原地翻转，reversed 给反向迭代器，切片给反向列表副本。三者都不是按大小降序排序，`[3, 1, 2]` 就是反例。

---

6）二维列表与复制：先确定你在改哪一层

6.1 连续下标从外到内

```python
# runnable: hb03_matrix
matrix = [[1, 2], [3, 4], [5, 6]]
row = matrix[2]
value = row[1]
assert row == [5, 6]
assert value == matrix[2][1] == 6
matrix[2][1] = 9
assert row == [5, 9]
print(matrix)
```

`matrix[2][1]` 先取第三行，再取这行的第二项。row 指向真实的那一行，不是自动复制它；从 row 或 matrix 任一路径修改，都可能落到同一个内层对象上。

6.2 赋值、浅拷贝与深拷贝的区别

```python
# runnable: hb03_copy_layers
from copy import deepcopy

source = [[1], [2]]
alias = source
shallow = source.copy()
deep = deepcopy(source)
assert alias is source
assert shallow is not source
assert shallow[0] is source[0]
assert deep[0] is not source[0]
shallow[0].append(9)
assert source == [[1, 9], [2]]
assert deep == [[1], [2]]
shallow[1] = [8]
assert source[1] == [2]
assert shallow[1] == [8]
print(source, shallow, deep)
```

赋值只多一个名字；浅拷贝新建外层，内层引用照抄；深拷贝会递归复制这类嵌套可变结构。`list(source)`、`source[:]` 也只是浅拷贝，不会因为换了写法就复制更深。

深拷贝不是一切对象的“完全隔离器”。自定义类型可以决定复制行为，文件和连接等资源也不能靠 deepcopy 安全复制成独立服务。业务上只需要几个字段时，显式构造目标数据通常更清楚。

6.3 乘法重复引用，为什么整行一起变

```python
# runnable: hb03_repetition_alias
wrong = [[0] * 3] * 2
assert wrong[0] is wrong[1]
wrong[0][0] = 9
assert wrong == [[9, 0, 0], [9, 0, 0]]
right = []
for _ in range(2):
    right.append([0] * 3)
assert right[0] is not right[1]
right[0][0] = 9
assert right == [[9, 0, 0], [0, 0, 0]]
print(wrong, right)
```

错误版本先创建一行，再引用它两次；正确版本每轮重新执行创建行列表。不是乘法有时失灵，而是你要两份对象，它却只负责重复已有元素引用。

6.4 深拷贝会保留内部本来存在的共享关系

```python
# runnable: hb03_deepcopy_shared_graph
from copy import deepcopy

row = [1]
source = [row, row]
copied = deepcopy(source)
assert copied is not source
assert copied[0] is not row
assert copied[0] is copied[1]
copied[0].append(2)
assert row == [1]
assert copied == [[1, 2], [1, 2]]
print(source, copied)
```

deepcopy 把原来的 row 复制为新 row，但不会故意把一份共享行拆成互不相关的两份。这里常用的理解是“复制整套关系”，而不是“每出现一次就新建一次”。

---

7）元组：位置固定，不代表里面所有对象都不能动

7.1 逗号创建元组

```python
# runnable: hb03_tuple_creation
assert type((10)) is int
assert type((10,)) is tuple
without_parentheses = 10, 20
assert without_parentheses == (10, 20)
assert tuple() == ()
assert tuple([1, 2]) == (1, 2)
print((10,), without_parentheses)
```

`(10)` 只是带括号的整数表达式；`(10,)` 才是一元素元组。空元组写 `()`。多个返回值实际经常由逗号打包成元组，再由调用方拆包。

7.2 常用读取与限制

```python
# runnable: hb03_tuple_operations
record = ("api", 200, "api")
assert len(record) == 3
assert record[0] == "api"
assert record[-1] == "api"
assert record[1:] == (200, "api")
assert record.index("api") == 0
assert record.count("api") == 2
assert "api" in record
assert record + (20,) == ("api", 200, "api", 20)
assert (1,) * 3 == (1, 1, 1)
try:
    record[0] = "db"
except TypeError:
    pass
else:
    raise AssertionError("tuple item cannot be replaced")
print(record)
```

没有 append、remove、sort 这类原地修改方法。拼接得到一个结果元组，不是改旧元组。想排序元组里的元素，sorted 返回列表；如确需元组，再用 tuple 包回去。

7.3 元组里面的列表仍然可变

```python
# runnable: hb03_tuple_nested_mutable
record = ("team", ["Ada"])
record[1].append("Lin")
assert record == ("team", ["Ada", "Lin"])
try:
    hash(record)
except TypeError:
    pass
else:
    raise AssertionError("contains unhashable list")
key = ("team", 1)
mapping = {key: "ok"}
assert mapping[key] == "ok"
print(record)
```

不能变的是“这个位置指向哪个对象”；指向的列表仍有自己的修改能力。元组也不是天然都可当字典键，元素必须都可哈希，里面有列表就不行。

7.4 拆包与星号接住剩余项

```python
# runnable: hb03_tuple_unpack
x, y = (10, 20)
first, *middle, last = (1, 2, 3, 4)
assert (x, y) == (10, 20)
assert first == 1 and middle == [2, 3] and last == 4
first, *middle, last = (1, 4)
assert middle == []
try:
    x, y = (1, 2, 3)
except ValueError:
    pass
else:
    raise AssertionError("unpacking size mismatch")
print(first, middle, last)
```

星号接到的是列表；普通位置先满足，其余项再交给它。没有足够元素满足普通变量时仍会报错，星号不是自动补缺值。

---

8）方法返回值速查，用来避免把列表变成 None

| 操作 | 是否修改原对象 | 返回什么 |
| --- | --- | --- |
| append、extend、insert | 是 | None |
| remove、clear、sort、reverse | 是 | None |
| pop | 是 | 被删除元素 |
| index、count | 否 | 整数 |
| copy | 否 | 浅拷贝列表 |
| sorted | 否 | 新列表 |
| reversed | 否 | 反向迭代器 |

没有一种统一规则叫“所有列表方法都返回 None”。正确习惯是每遇到一个方法，就分开问修改位置与返回内容。

---

9）练习与参考答案

9.1 删光重复项，并保留原列表对象

题目：`[1, 2, 1, 3]` 删除所有 1；另一个引用也应看到 `[2, 3]`。

```python
# runnable: hb03_exercise_remove_all
items = [1, 2, 1, 3]
alias = items
kept = []
for value in items:
    if value != 1:
        kept.append(value)
items[:] = kept
assert items is alias
assert alias == [2, 3]
print(alias)
```

先生成结果，再替换原对象内容，避免遍历时移动下标，也避免仅重新绑定当前变量。

9.2 创建独立的三行表格

题目：创建 3 行 2 列零值表格，只修改中间行第一列为 7，其他行不变。

```python
# runnable: hb03_exercise_matrix
matrix = [[0, 0] for _ in range(3)]
matrix[1][0] = 7
assert matrix == [[0, 0], [7, 0], [0, 0]]
assert matrix[0] is not matrix[1]
assert matrix[1] is not matrix[2]
print(matrix)
```

9.3 按分数降序，同分按姓名升序

题目：不改原列表，输出排序后的姓名。分数用负号，姓名保持正常顺序。

```python
# runnable: hb03_exercise_sort
records = [("Bob", 90), ("Ada", 90), ("Lin", 80)]
ordered = sorted(records, key=lambda row: (-row[1], row[0]))
assert ordered == [("Ada", 90), ("Bob", 90), ("Lin", 80)]
assert records[0] == ("Bob", 90)
print([name for name, score in ordered])
```

---

10）查阅位置

列表完整方法与返回行为见 [Python 3.11 数据结构教程](https://docs.python.org/3.11/tutorial/datastructures.html)。序列与元组规则见 [序列类型](https://docs.python.org/3.11/library/stdtypes.html#sequence-types-list-tuple-range)。复制层次见 [copy 模块](https://docs.python.org/3.11/library/copy.html)，排序键与稳定性见 [排序指南](https://docs.python.org/3.11/howto/sorting.html)。
