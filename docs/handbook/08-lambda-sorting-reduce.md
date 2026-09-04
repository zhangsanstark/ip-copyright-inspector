08 lambda、排序与 map / filter / reduce

先把这章的几个动作分开：排序决定先后；map 把每项变一下；filter 决定每项留不留；reduce 把上轮结果带进下一轮。它们都可以接收一个函数，但做的不是同一件事。

阅读导航：1 是传函数和 lambda；2 是排序；3–4 是 map/filter；5–9 从普通循环走到 reduce；10–11 是组合与练习。

```powershell
python scripts/check_handbook_examples.py --chapter 08 --show-output
```

---

1）lambda 没有额外的神秘规则

1.1 先写成普通函数，再缩短

```python
# runnable: hb08_lambda_basics
def double(value):
    return value * 2

short_double = lambda value: value * 2
assert double(6) == short_double(6) == 12

def choose_large(a, b):
    return a if a > b else b

short_choose = lambda a, b: a if a > b else b
assert choose_large(3, 7) == short_choose(3, 7) == 7
```

`lambda 参数: 表达式` 创建函数，表达式算出的值自动成为返回值。它不是少写了 `return` 的任意代码块，只能容纳一个表达式。

所以多步校验、日志、循环或复杂分支通常写 `def`。函数不长不代表必须改成 lambda。给业务规则起个名字，也是在给读者解释代码。

1.2 没有名字也能有参数与默认值

```python
# runnable: hb08_lambda_parameters
constant = lambda: 7
scale = lambda value, factor=2: value * factor
sum_values = lambda *values: sum(values)
read_field = lambda **fields: fields.get("name", "未命名")
assert constant() == 7
assert scale(3) == 6 and scale(3, 4) == 12
assert sum_values(1, 2, 3) == 6
assert read_field(name="周") == "周"
```

参数绑定规则仍然是第 6 章那一套，默认参数也仍然只在创建函数时求值。循环晚期绑定问题仍然存在，详见第 7 章。

1.3 传规则，不是提前运行规则

```python
# runnable: hb08_function_argument
def apply(value, transform):
    return transform(value)

def square(value):
    return value * value

assert apply(5, square) == 25
assert apply(5, lambda value: value + 1) == 6
```

`apply(5, square)` 把函数交进去，随后由 `apply` 调用。若写成 `apply(5, square(5))`，第二项是 25，函数内部就会试图执行 `25(5)`，报整数不可调用。

---

2）排序：先给每项提取一个比较用的值

2.1 key 不是“比较两个对象”的函数

```python
# runnable: hb08_sort_key
records = [
    {"name": "小周", "age": 30},
    {"name": "小吴", "age": 20},
    {"name": "小赵", "age": 25},
]

def age_key(record):
    return record["age"]

ordered = sorted(records, key=age_key)
assert [record["age"] for record in ordered] == [20, 25, 30]
assert [record["age"] for record in records] == [30, 20, 25]
```

排序会为元素提取比较键：小周对应 30，小吴对应 20，小赵对应 25，然后按这些键排列。`age_key` 一次接收一个元素，不是像某些 Java Comparator 写法那样接收左右两个对象再返回大小关系。

一次排序中，key 对每个元素调用一次。因此不要把它写成会随机变化或修改列表的函数；排序键应该稳定表达当前元素的排序依据。

2.2 sorted 创建新列表，list.sort 修改原列表

```python
# runnable: hb08_sorted_vs_sort
values = [3, 1, 2]
copy = sorted(values, reverse=True)
assert copy == [3, 2, 1]
assert values == [3, 1, 2]
returned = values.sort()
assert values == [1, 2, 3]
assert returned is None
assert sorted((3, 1, 2)) == [1, 2, 3]
```

常见错误是 `values = values.sort()`：原列表虽然排好了，但赋给 `values` 的返回值是 `None`。是否原地修改与返回什么必须一起记。

2.3 多条件：先看第一个键，相同时再看后面

```python
# runnable: hb08_tuple_sort
records = [
    {"name": "A", "sales": 100, "age": 30},
    {"name": "B", "sales": 200, "age": 40},
    {"name": "C", "sales": 200, "age": 20},
    {"name": "D", "sales": 200, "age": 20},
]

def business_key(record):
    return -record["sales"], record["age"]

ordered = sorted(records, key=business_key)
assert [record["name"] for record in ordered] == ["C", "D", "B", "A"]
assert business_key(records[1]) == (-200, 40)
```

我们要销售额降序、年龄升序。默认升序下，`-200` 比 `-100` 小，所以销售额 200 的先来。销售额相同才比较年龄，20 比 40 小，所以 C、D 在 B 前面。

C、D 的两个键都相同，原来 C 在 D 前面，排序后仍如此。这叫稳定排序：相等键保留原先顺序。

如果写 `reverse=True`，反转的是整个键的比较方向，不是“只反转第一个条件”。不要把它和局部降序混为一谈。

2.4 字符串不能取负号，可以分两次稳定排序

```python
# runnable: hb08_stable_sort
records = [
    {"name": "A", "group": "beta", "age": 20},
    {"name": "B", "group": "alpha", "age": 30},
    {"name": "C", "group": "beta", "age": 18},
]
ordered = sorted(records, key=lambda row: row["age"])
ordered.sort(key=lambda row: row["group"], reverse=True)
assert [row["name"] for row in ordered] == ["C", "A", "B"]
```

先排次要条件年龄，后排主要条件组名。同组在第二轮键相同，会保留第一轮排好的年龄顺序。多轮稳定排序是“次要条件先做、主要条件后做”。

2.5 缺字段与明确的 None，要统一成可比较的键

用 `row["age"]` 会对缺字段报错；改成 `.get` 只是取默认值，不自动知道缺失项应该排前还是排后。下面约定已知年龄升序，未知年龄最后；缺字段和显式 None 都算未知，其他非整数输入直接报错。

```python
# runnable: hb08_missing_age_sort
def age_key(row):
    age = row.get("age")
    if age is None:
        return 1, 0
    if not isinstance(age, int) or isinstance(age, bool):
        raise TypeError("age 必须是整数或 None")
    return 0, age

rows = [{"id": "A", "age": 30}, {"id": "B"},
        {"id": "C", "age": None}, {"id": "D", "age": 20}]
assert [row["id"] for row in sorted(rows, key=age_key)] == ["D", "A", "B", "C"]
assert age_key({}) == age_key({"age": None}) == (1, 0)
```

键的第一项先区分已知与未知，第二项始终是能比较的整数。不要让缺字段产生 `(1, 0)`、显式 None 却产生 `(1, None)`，否则第一项相等时会继续比较 0 和 None，又会报 TypeError。

---

3）map：逐项变换，产生的是结果值

3.1 和普通 for 对照

```python
# runnable: hb08_map_loop
def normalize(value):
    return value.strip().lower()

raw = [" A ", "B ", " c"]
by_loop = []
for value in raw:
    by_loop.append(normalize(value))

by_map = list(map(normalize, raw))
assert by_loop == by_map == ["a", "b", "c"]
assert raw == [" A ", "B ", " c"]
```

map 每轮取出一项，把它作为参数交给 `normalize`，再把返回值作为这一轮结果。这里保留的是转换后的字符串，不是原来带空格的字符串。

3.2 map 返回迭代器，不会创建时立刻执行全部转换

```python
# runnable: hb08_map_lazy
calls = []

def double(value):
    calls.append(value)
    return value * 2

mapped = map(double, [1, 2, 3])
assert calls == []
assert next(mapped) == 2
assert calls == [1]
assert list(mapped) == [4, 6]
assert list(mapped) == []
assert calls == [1, 2, 3]
```

第一次 `next` 只处理 1；后面的 `list` 消耗剩下的 2、3。读完之后不会自动从头来一遍，需要重新创建 map。这也解释了为什么转换中的错误可能到真正遍历时才出现。

3.3 多个输入：每轮各取一项交给函数

```python
# runnable: hb08_map_multiple
def multiply(price, quantity):
    return price * quantity

totals = list(map(multiply, [10, 20, 30], [2, 3]))
assert totals == [20, 60]
```

第一轮 `multiply(10, 2)`，第二轮 `multiply(20, 3)`。较短的输入结束就停，30 不会自动配一个默认数量，也不会默认抛长度不一致错误。

如果长度必须一致，Python 3.11 基线可使用 `zip(..., strict=True)` 配合循环明确检查。不要照搬更新版本才有的参数而忘记运行环境。

---

4）filter：判断是否保留，留下的仍是原元素

```python
# runnable: hb08_filter
def useful(text):
    return bool(text.strip())

raw = [" A ", "  ", "B"]
by_loop = []
for text in raw:
    if useful(text):
        by_loop.append(text)

assert list(filter(useful, raw)) == by_loop == [" A ", "B"]
assert list(filter(None, [0, 1, "", "A", None, [], [2], False])) == [1, "A", [2]]
```

`useful(" A ")` 返回 True，但 filter 不会把结果换成 True，也不会把原字符串去掉空格；它只根据真假决定留下原来的 `" A "`。

`filter(None, iterable)` 的意思是直接按元素本身的真假筛选，不是只过滤 `None`。所以数字 0、空字符串、空列表和 False 都会消失。业务里 0 如果是有效值，要写 `lambda value: value is not None`。

filter 同样是惰性迭代器，一次读完就耗尽。筛选函数只需要返回能判断真假的对象，不强制必须返回 bool；但判断规则最好写得清楚。

---

5）reduce：先从你已经看得懂的循环开始

5.1 把累计结果一轮轮接下去

```python
# runnable: hb08_reduce_loop
values = [2, 3, 4]
total = 10
for current in values:
    previous = total
    total = total + current
    print(previous, "+", current, "=", total)
assert total == 19
```

这里有三个角色：输入 `[2, 3, 4]`、起点 10、每轮的合并规则“旧 total 加当前元素”。reduce 只是把这三件事分别作为参数接进去。

```python
# runnable: hb08_reduce_first
from functools import reduce

def combine(accumulator, current):
    result = accumulator + current
    print(accumulator, "+", current, "=", result)
    return result

answer = reduce(combine, [2, 3, 4], 10)
assert answer == 19
```

三个位置参数依次是：处理函数、可迭代输入、初始值。为了兼容 Python 3.11，本书把初始值作为第三个位置参数传递。

5.2 不要只盯着最终答案，盯住 return 的去向

| 轮次 | accumulator 收到什么 | current 收到什么 | 本轮 return | 下一轮第一个参数 |
| --- | --- | --- | --- | --- |
| 1 | 初始值 10 | 2 | 12 | 12 |
| 2 | 上轮的 12 | 3 | 15 | 15 |
| 3 | 上轮的 15 | 4 | 19 | 没有下一轮，直接作为总结果 |

`combine` 这个普通函数不会自己记忆上次结果。是 reduce 调用它、拿到返回值，再把返回值传给下一次调用。把“保存累计结果”的责任分清，就不必猜为什么它能一直累加。

这里 accumulator 是累计结果，current 是当前输入项。它们的名字可以换，参数顺序不能理解反了。

---

6）没写初始值时，第一项会被直接拿来当起点

```python
# runnable: hb08_reduce_no_initial
from functools import reduce

calls = []

def combine(accumulator, current):
    calls.append((accumulator, current))
    return accumulator + current

answer = reduce(combine, [2, 3, 4])
assert answer == 9
assert calls == [(2, 3), (5, 4)]
```

这次起点直接用输入第一项 2，因此函数只调用两次。不要脑补一个隐含的 0；reduce 不知道你想做加法、乘法、字符串拼接还是别的事情，不能擅自挑一个起点。

6.1 空输入、单元素输入单独看

```python
# runnable: hb08_reduce_edges
from functools import reduce

calls = []

def combine(a, b):
    calls.append((a, b))
    return a + b

assert reduce(combine, [], 100) == 100
assert calls == []
assert reduce(combine, [7]) == 7
assert calls == []
assert reduce(combine, [7], 100) == 107
assert calls == [(100, 7)]
try:
    reduce(combine, [])
except TypeError:
    print("空输入又没有起点，无法得到结果")
else:
    raise AssertionError("预期空输入错误")
```

有初始值、空输入时直接返回初始值，不调用处理函数。无初始值、单元素时直接返回那一项，也不调用处理函数。

因此只拿单元素测试错误回调，可能根本没测到它。至少用两项，或者明确提供初始值，让回调真的运行。

6.2 None 是一个明确的初始值，不代表没提供

```python
# runnable: hb08_reduce_none
from functools import reduce

calls = []

def first_or_add(accumulator, current):
    calls.append((accumulator, current))
    if accumulator is None:
        return current
    return accumulator + current

assert reduce(first_or_add, [2, 3], None) == 5
assert calls == [(None, 2), (2, 3)]
```

这次第一轮真的收到 `(None, 2)`。把“没传第三个参数”和“第三个参数传 None”混在一起，会在处理空值时出现很难发现的差异。

---

7）reduce 从左到右算，不保证换顺序还是同一个答案

```python
# runnable: hb08_reduce_order
from functools import reduce

def subtract(a, b):
    return a - b

assert reduce(subtract, [10, 3, 2]) == 5
assert (10 - 3) - 2 == 5
assert 10 - (3 - 2) == 9
assert reduce(subtract, [2, 3, 10]) == -11
```

实际过程是先算 `10 - 3`，再把 7 带到下一轮算 `7 - 2`。不是先算右边，也不是帮你选择最合理的运算顺序。

来自 Java Stream 的读者要注意：这里没有自动并行归约，也没有额外的“合并两个分区结果”参数。不要把并行流的前提和这个顺序调用过程混在一起。

输入是集合时尤其要小心，因为集合不保证业务意义上的顺序。减法、拼接等顺序敏感的操作应使用顺序明确的数据来源。

---

8）累计结果与输入元素可以是不同类型

8.1 当前项是订单字典，累计结果是金额数字

```python
# runnable: hb08_reduce_orders
from functools import reduce

orders = [
    {"unit_price": 100, "quantity": 2},
    {"unit_price": 50, "quantity": 3},
]

def add_order(total, order):
    line_total = order["unit_price"] * order["quantity"]
    return total + line_total

assert reduce(add_order, orders, 0) == 350
assert reduce(add_order, [], 0) == 0
```

初始值 0 确定第一轮 `total` 是数字，`order` 是字典。第一轮返回 200，第二轮收到 `(200, 第二张订单)`，返回 350。

如果省略 0，第一项订单字典会变成累计起点；`total + line_total` 变成字典加数字，当然报错。初始值不只是空列表的兜底，也可以决定累计状态的类型。

8.2 累计结果也可以是一个统计字典

```python
# runnable: hb08_reduce_summary
from functools import reduce

def include(summary, amount):
    return {"count": summary["count"] + 1, "total": summary["total"] + amount}

initial = {"count": 0, "total": 0}
summary = reduce(include, [10, 20, 30], initial)
assert summary == {"count": 3, "total": 60}
assert initial == {"count": 0, "total": 0}
```

每轮返回新字典，这份新字典再给下一轮。也可以原地修改累计字典，但要明确初始字典会跟着变，并且一定返回它。

```python
# runnable: hb08_reduce_mutating
from functools import reduce

def append_value(bucket, value):
    bucket.append(value)
    return bucket

initial = []
result = reduce(append_value, [1, 2], initial)
assert result is initial
assert initial == [1, 2]
```

这个写法用来观察共享对象，真实代码只是收集列表时直接 `list(input)` 更清楚。不是能用 reduce 就值得用。

---

9）出错时，先检查每轮的两个输入和返回值

9.1 漏 return 会把 None 传给下一轮

```python
# runnable: hb08_reduce_missing_return
from functools import reduce

def broken(a, b):
    a + b

try:
    reduce(broken, [1, 2, 3])
except TypeError:
    print("第一轮没返回，第二轮实际上计算 None + 3")
else:
    raise AssertionError("应该失败")
assert broken(1, 2) is None
```

`return bucket.append(value)` 也是常见变体：append 做了修改，但返回 None，因此下一轮拿到 None。正确修法是先 append，再 `return bucket`，或者直接改用清楚的循环。

9.2 函数必须能接收这两个实参

reduce 每次给回调传两个位置值。因此 `lambda x: ...` 接不住；带第三个必填参数的函数也接不住。

准确说法是“回调必须能接收每轮这两个实参”，而不是“定义时只能写两个参数”。`def f(a, b, scale=1)` 或适当的 `*args` 也能接住；只是本章采用明确的两个形参，便于读过程。

9.3 一个接近 reduce 行为的简化实现

```python
# runnable: hb08_reduce_reimplementation
MISSING = object()

def fold(function, iterable, initial=MISSING):
    iterator = iter(iterable)
    if initial is MISSING:
        try:
            result = next(iterator)
        except StopIteration:
            raise TypeError("empty input without initial") from None
    else:
        result = initial
    for current in iterator:
        result = function(result, current)
    return result

assert fold(lambda a, b: a + b, [2, 3, 4], 10) == 19
assert fold(lambda a, b: a + b, [2, 3, 4]) == 9
assert fold(lambda a, b: b, [], None) is None
```

先拿起点，再循环，把每次返回值重新保存为 result。看懂这十来行，reduce 就没有额外秘密了。这里的实现用于讲执行过程，不是为了在项目里取代标准库。

---

10）想看中间结果用 accumulate，想写简单代码用直接工具

```python
# runnable: hb08_accumulate
from functools import reduce
from itertools import accumulate

values = [2, 3, 4]
assert reduce(lambda a, b: a + b, values, 10) == 19
assert list(accumulate(values, initial=10)) == [10, 12, 15, 19]
assert sum(values, 10) == 19
assert max(values) == 4
assert any(value > 3 for value in values) is True
assert all(value > 0 for value in values) is True
```

accumulate 交出过程中的累计状态，这里还包括初始值 10；reduce 只交最终状态。两者返回形式也不同，前者是迭代器，后者直接给最终累计结果。

纯求和用 `sum`，最大值用 `max`，判断有没有满足用 `any`，判断是否全满足用 `all`。这些名字直接表达意图，不需要读者再还原你的合并函数。

10.1 筛选、转换、累计接在一起

```python
# runnable: hb08_pipeline
raw = [" 10 ", "", "20", "  ", "30"]
total = 0
for text in raw:
    cleaned = text.strip()
    if cleaned:
        total += int(cleaned)

cleaned_values = map(str.strip, raw)
nonempty = filter(None, cleaned_values)
numbers = map(int, nonempty)
assert total == sum(numbers) == 60
```

前半段更方便插入日志和调试，后半段把处理步骤拆成流水线。这里没有处理 `"abc"`，因为它虽然非空却不能转整数。输入校验规则不能因为写成 map/filter 就凭空出现。

---

11）练习与答案

11.1 题目一：手算不同起点

求 `[2, 3, 4]` 的乘积，分别不写起点、起点 1、起点 0。答案应该是 24、24、0。为什么第三种一直是 0？因为第一轮已经是 `0 * 2`，后面再乘也回不来。

```python
# runnable: hb08_exercise_product
from functools import reduce

def multiply(a, b):
    return a * b

assert reduce(multiply, [2, 3, 4]) == 24
assert reduce(multiply, [2, 3, 4], 1) == 24
assert reduce(multiply, [2, 3, 4], 0) == 0
assert reduce(multiply, [], 1) == 1
```

11.2 题目二：统计字符串总长度，不保留空白项

输入 `[' A ', ' ', 'BCD']`，去掉两端空白，忽略空字符串，总长度为 4。先写循环，再写一条可读的生成器表达式。

```python
# runnable: hb08_exercise_lengths
raw = [" A ", " ", "BCD"]
total = 0
for text in raw:
    cleaned = text.strip()
    if cleaned:
        total += len(cleaned)

cleaned_values = (text.strip() for text in raw)
answer = sum(len(text) for text in cleaned_values if text)
assert total == answer == 4
```

这里只关心最终数字，不需要先创建一份长度列表。生成器表达式的执行时机在第 10 章展开。

11.3 题目三：把记录按状态分组

用 reduce 做一次状态字典累计。输入 `['ok', 'fail', 'ok']`，结果 `{'ok': 2, 'fail': 1}`；空输入得到空字典。再想一想第 23 章的 Counter 是否更直接。

```python
# runnable: hb08_exercise_counts
from functools import reduce

def count_status(counts, status):
    counts[status] = counts.get(status, 0) + 1
    return counts

assert reduce(count_status, ["ok", "fail", "ok"], {}) == {"ok": 2, "fail": 1}
assert reduce(count_status, [], {}) == {}
```

本题每次调用都在调用位置新建 `{}`，不是把字典放在函数定义的默认值里。两种写法表面都出现大括号，创建时机却不一样。

---

12）这章读完，应该能解释的不只是定义

拿一个三元素输入，说出 map 每轮返回什么、filter 根据什么保留、reduce 如何传递上一轮结果；再说明哪些对象读完就耗尽，哪些操作会立即遍历完成。

如果只能背“map 映射、filter 过滤、reduce 归约”，还没有抓住程序运行时实际发生的事。回到 3.2 与 5.2 的过程，再亲手改一个输入试试。

接口细节见 [functools.reduce](https://docs.python.org/3.11/library/functools.html#functools.reduce)、[内置 map](https://docs.python.org/3.11/library/functions.html#map)、[内置 filter](https://docs.python.org/3.11/library/functions.html#filter)。排序细节可查 [官方排序指南](https://docs.python.org/3.11/howto/sorting.html)，中间累计状态可查 [itertools.accumulate](https://docs.python.org/3.11/library/itertools.html#itertools.accumulate)。
