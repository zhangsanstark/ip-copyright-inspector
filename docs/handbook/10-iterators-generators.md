10 迭代器与生成器：需要下一个时，再往前走一步

生成器不是“换一种括号写列表”。它改变的是计算时机和保存方式：结果可以一项项产生，执行现场会暂停，读完以后通常不能直接再来一遍。

阅读导航：1–3 分清可迭代对象、迭代器和 yield；4–5 是表达式与流水线；6–8 解释内存、资源和进阶交互；9 是练习。

```powershell
python scripts/check_handbook_examples.py --chapter 10 --show-output
```

---

1）for 背后在反复要“下一个”

1.1 可迭代对象能提供迭代器，迭代器记住走到哪里

```python
# runnable: hb10_iter_next
values = [10, 20, 30]
iterator = iter(values)
assert next(iterator) == 10
assert next(iterator) == 20
assert list(iterator) == [30]
assert list(iterator) == []
assert list(values) == [10, 20, 30]
assert iter(iterator) is iterator
assert iter(values) is not iter(values)
```

列表还保存着全部元素，调用 `iter(values)` 可以获得新的遍历位置。迭代器则像这一次遍历的进度记录；上面的 iterator 已经走到末尾，再读不会自动倒回去。

`iter(iterator)` 返回它自身，说明“给我一个迭代器”不会替你重置它。排查第二次遍历为空时，先看保存的是列表，还是已经消耗过的迭代器。

1.2 StopIteration 表示没有下一项

```python
# runnable: hb10_stop_iteration
iterator = iter([7])
assert next(iterator) == 7
try:
    next(iterator)
except StopIteration:
    print("没有下一项了")
else:
    raise AssertionError("应该结束")
assert next(iterator, "结束") == "结束"
```

`next(iterator, default)` 在耗尽时返回默认值，不向外抛 StopIteration。默认值如果也可能是正常元素，要换一个独有的哨兵对象来区分。

for 循环内部会处理这个结束信号，所以你平时遍历到尾部不会看到异常。把它展开，大致就是下面的结构。

```python
# runnable: hb10_manual_for
iterator = iter([2, 4, 6])
result = []
while True:
    try:
        value = next(iterator)
    except StopIteration:
        break
    result.append(value * 2)
assert result == [4, 8, 12]
```

这里 try 只围住取下一项。业务处理如果也会抛 StopIteration，不应该不加区别地被认作“输入正常读完”。捕获范围越小，错误含义越清楚。

---

2）自己写一个迭代器，就能看到状态存在哪里

```python
# runnable: hb10_custom_iterator
class Countdown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value

counter = Countdown(3)
assert next(counter) == 3
assert list(counter) == [2, 1]
assert list(counter) == []
assert list(Countdown(0)) == []
```

`current` 就是进度。每次 next 会调用 `__next__`，先保存当前值，把进度减一，再返回刚保存的旧值。`__iter__` 返回自己，表示这个对象本身就是迭代器。

这段使用了类与魔术方法，不熟悉时先理解状态变化即可，第 12、13 章会补齐对象语法。生成器的好处是不用手动写这些方法，也能保留类似进度。

---

3）yield：交出一项结果，把执行位置留在这里

3.1 调用生成器函数，并不会立刻执行函数体

```python
# runnable: hb10_yield_trace
events = []

def numbers():
    events.append("开始")
    yield 10
    events.append("恢复到第二段")
    yield 20
    events.append("走到末尾")

generator = numbers()
assert events == []
assert next(generator) == 10
assert events == ["开始"]
assert next(generator) == 20
assert events == ["开始", "恢复到第二段"]
assert next(generator, "结束") == "结束"
assert events == ["开始", "恢复到第二段", "走到末尾"]
```

执行时间线很重要：

| 操作 | 从哪里继续 | 到哪里停 | 调用方得到什么 |
| --- | --- | --- | --- |
| numbers() | 尚未进入函数体 | 等第一次取值 | 生成器对象 |
| 第一次 next | 函数开头 | yield 10 | 10 |
| 第二次 next | yield 10 后面 | yield 20 | 20 |
| 第三次 next | yield 20 后面 | 函数结束 | 默认值“结束” |

它不是每次从函数第一行重新跑，也不是把全部值偷偷算好。暂停时保留局部变量和执行位置，下次从暂停点继续。

3.2 yield 放进循环，循环进度也被保留

```python
# runnable: hb10_countdown_generator
def countdown(start):
    current = start
    while current > 0:
        yield current
        current -= 1

generator = countdown(3)
assert next(generator) == 3
assert next(generator) == 2
assert list(generator) == [1]
```

第一次 yield 3 时，`current -= 1` 还没执行。第二次 next 才从这句继续，然后检查 while，再 yield 2。观察变量何时变化，比笼统说“冻结状态”更容易记住。

3.3 return 是结束，不是再产生一项

```python
# runnable: hb10_generator_return
def one_then_finish():
    yield 7
    return "完成说明"

generator = one_then_finish()
assert next(generator) == 7
try:
    next(generator)
except StopIteration as end:
    assert end.value == "完成说明"
else:
    raise AssertionError("应该结束")
assert list(one_then_finish()) == [7]
```

return 后面的值是结束信息，普通 for 或 list 不会把它当作一项收集。写 `return 8` 不能代替 `yield 8`。

在生成器体里主动 `raise StopIteration` 不是推荐的结束方式。正常结束写 return 或走到末尾；把 StopIteration 意外漏出生成器体会被转换为 RuntimeError，以免真正错误伪装成正常耗尽。

---

4）生成器表达式：简短，但执行时机仍需想清楚

4.1 方括号立即收集，圆括号按需产生

```python
# runnable: hb10_expression
calls = []

def transform(value):
    calls.append(value)
    return value * value

eager = [transform(value) for value in range(3)]
assert eager == [0, 1, 4]
assert calls == [0, 1, 2]
calls.clear()
lazy = (transform(value) for value in range(3))
assert calls == []
assert next(lazy) == 0
assert calls == [0]
assert list(lazy) == [1, 4]
```

表达式里的 `transform` 在需要结果时才执行。但最外层 for 的可迭代对象表达式会在创建生成器表达式时求值，不能说圆括号里的所有内容都永远延后。

```python
# runnable: hb10_expression_outer
events = []

def source():
    events.append("构造来源")
    return [1, 2]

generator = (value * 2 for value in source())
assert events == ["构造来源"]
assert list(generator) == [2, 4]
```

4.2 外面的变量变化，也可能影响之后产出的值

```python
# runnable: hb10_expression_binding
factor = 2
generator = (value * factor for value in [1, 2])
factor = 10
assert list(generator) == [10, 20]
```

因为乘法发生在消费时，届时读到 factor 是 10。这和闭包的运行时查找有关。想固定配置，可以用工厂函数参数保存本次配置，不要假设表达式创建时自动复制全部环境。

---

5）把几步处理接起来，每次只让一条数据走完

```python
# runnable: hb10_pipeline_trace
events = []

def source():
    for value in [1, 2, 3]:
        events.append(f"取出 {value}")
        yield value

def doubled(values):
    for value in values:
        events.append(f"转换 {value}")
        yield value * 2

def over_two(values):
    for value in values:
        events.append(f"检查 {value}")
        if value > 2:
            yield value

pipeline = over_two(doubled(source()))
assert events == []
assert next(pipeline) == 4
assert events == ["取出 1", "转换 1", "检查 2", "取出 2", "转换 2", "检查 4"]
assert list(pipeline) == [6]
print(" → ".join(events))
```

为了得到第一条满足条件的结果，外层会一路向上游要数据。1 变成 2 没通过，继续要 2，变成 4 通过，这时整个链条暂停。不是先把 source 全读完，再把转换全做完，再统一筛选。

这适合逐行日志、分页数据、流式导出。它也意味着错误发生在哪一项，要等读到那一项才知道；只创建 pipeline 并不能证明整批数据没有问题。

5.1 yield from：把别的可迭代对象里的值逐个交出去

```python
# runnable: hb10_yield_from
def flatten_one_level(groups):
    for group in groups:
        yield from group

assert list(flatten_one_level([[1, 2], [], [3]])) == [1, 2, 3]
assert list(flatten_one_level(["ab", "cd"])) == ["a", "b", "c", "d"]
```

基础遍历场景下，可以把 `yield from group` 理解成 `for value in group: yield value`。字符串也是可迭代对象，所以会被拆成字符；它不会自动把字符串当作不可拆的业务值。

`yield from` 还会转交 send/throw 等交互，并能获得子生成器的 return 值。如果只是刚开始使用生成器，先把逐项转交这件事掌握即可。

---

6）省内存的前提：你没有在别处又把全部结果存下来

6.1 生成器省的是中间结果集合，不是所有内存

```python
# runnable: hb10_memory
import tracemalloc

def list_total(size):
    values = [number * number for number in range(size)]
    return sum(values)

def generator_total(size):
    return sum(number * number for number in range(size))

def measure(function, size):
    tracemalloc.start()
    try:
        result = function(size)
        _, peak = tracemalloc.get_traced_memory()
        return result, peak
    finally:
        tracemalloc.stop()

list_result, list_peak = measure(list_total, 5000)
generator_result, generator_peak = measure(generator_total, 5000)
assert list_result == generator_result
print("列表方案峰值字节：", list_peak)
print("生成器方案峰值字节：", generator_peak)
```

这里用相同计算比较 Python 内存分配峰值。具体数值与解释器、平台和输入有关，不把“省 90%”写成保证；tracemalloc 也不是所有原生库内存的完整监视器。

如果写 `list(generator)`，最终还是把全部结果放进列表。如果上游本来就是一个百万项列表，生成器也不会让原列表凭空消失；它主要避免再建立一整份中间结果。

6.2 惰性不等于更快，也不等于异步

每项经过 Python 层的暂停和恢复也有成本。小数据直接列表可能更简单；需要反复随机访问、排序、计算长度时，保留列表往往合理。

普通生成器不会自动开线程，不会自己并发请求，不会把阻塞操作变异步。它只是按需执行，运行在哪个线程仍由调用方决定。

---

7）提前停止时，谁来关资源

```python
# runnable: hb10_close
events = []

def values():
    try:
        yield 1
        yield 2
    finally:
        events.append("清理")

generator = values()
assert next(generator) == 1
assert events == []
generator.close()
assert events == ["清理"]
assert list(generator) == []
```

开始迭代后，`close()` 会让生成器在暂停点结束，finally 得到执行机会。普通 for 中 `break` 只是停止循环，并不保证立刻对任意迭代器调用 close。

因此生成器若内部持有文件、连接等资源，调用方可能提前退出时，应明确设计关闭方式。不要把垃圾回收时机当成“马上关文件”的可靠协议。

未开始执行的生成器，函数体里的资源还没创建，调用 close 也不会先跑进去执行那些清理逻辑。理解资源何时获得，是设计生命周期的前提。

第 11 章会用 `with` 与 `contextlib.closing` 把这件事写清楚。

---

8）选读：send 把一个值送回暂停点

```python
# runnable: hb10_send
def running_total():
    total = 0
    while True:
        received = yield total
        if received is None:
            return total
        total += received

generator = running_total()
assert next(generator) == 0
assert generator.send(5) == 5
assert generator.send(3) == 8
try:
    generator.send(None)
except StopIteration as end:
    assert end.value == 8
else:
    raise AssertionError("应该结束")
```

读 `received = yield total` 时分两边：暂停时，total 向外产生；恢复时，send 的值成为 yield 表达式的结果，再赋给 received。

第一次要用 `next` 或 `send(None)` 启动，因为还没有暂停在某个 yield 上，不能直接把非 None 值送进去。普通 `next(generator)` 在恢复时相当于送入 None，所以本例用它继续会结束。

这比普通逐项产出更难，日常数据处理不一定需要。先把 next/yield/耗尽掌握好，再看 send，不必为了“高级”强行改写清楚的循环。

---

9）练习与参考答案

9.1 题目一：按批输出，最后一批允许不足

输入 `range(7)`，每批 3 个，结果应为 `[[0, 1, 2], [3, 4, 5], [6]]`；空输入没有批次；批量大小必须为正整数。本实现兼容 Python 3.11，不依赖更新版本增加的批处理函数。

```python
# runnable: hb10_exercise_batches
def batches(iterable, size):
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise ValueError("size 必须是正整数")
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch

assert list(batches(range(7), 3)) == [[0, 1, 2], [3, 4, 5], [6]]
assert list(batches([], 3)) == []
try:
    next(batches([1], 0))
except ValueError:
    pass
else:
    raise AssertionError("大小必须校验")
```

产生一批后用 `batch = []` 新建下一批。若对同一个 batch 反复 `.clear()`，调用方保存的上一批也可能被清空，因为它们指向同一个列表。

还要注意：校验写在生成器函数体内，要开始取值才执行。若接口要求调用 `batches(...)` 当下就报错，可以用普通外层函数先校验，再返回内层生成器。

9.2 题目二：相邻去重，不是全局去重

输入 `[1, 1, 2, 2, 1, 3, 3]`，结果 `[1, 2, 1, 3]`。只跳过与紧前一个相同的值，后面重新出现的 1 要保留。

```python
# runnable: hb10_exercise_unique_adjacent
def unique_adjacent(iterable):
    missing = object()
    previous = missing
    for value in iterable:
        if previous is missing or value != previous:
            yield value
        previous = value

assert list(unique_adjacent([1, 1, 2, 2, 1, 3, 3])) == [1, 2, 1, 3]
assert list(unique_adjacent([None, None, 0, 0])) == [None, 0]
assert list(unique_adjacent([])) == []
```

独有 object 用来表示“还没有上一项”，这样正常输入 None 不会与起始状态混淆。这个规则比较相邻元素，不需要保存一个越长越大的 seen 集合。

9.3 题目三：把错误留在结果里，不让整批中断

输入数字字符串，逐项产出 `(原字符串, 转换结果, 错误说明)`。合法项错误说明为 None，非法项结果为 None。不要用宽泛的 except 把所有代码错误都吞掉。

```python
# runnable: hb10_exercise_parse
def parse_numbers(strings):
    for text in strings:
        try:
            number = int(text)
        except ValueError:
            yield text, None, "不是整数文本"
        else:
            yield text, number, None

result = list(parse_numbers(["10", "bad", " 20 "]))
assert result == [("10", 10, None), ("bad", None, "不是整数文本"), (" 20 ", 20, None)]
```

题目明确输入是字符串，因此捕获 ValueError 处理内容不合法。如果实际接口还允许 None、字典等任意值，需要另外制定输入类型策略，不应该默认把程序本身的 TypeError 都当成普通脏数据。

---

10）回看时用这四个问题检查

什么时候开始执行？每次停止在哪一行？当前保存了哪些状态或资源？调用方提前不读了怎么办？

能回答这四项，再去看生成器流水线就不容易被“简洁写法”遮住实际行为。

相关协议见 [迭代器类型](https://docs.python.org/3.11/library/stdtypes.html#iterator-types)，暂停与交互规则见 [yield 表达式](https://docs.python.org/3.11/reference/expressions.html#yield-expressions)，基本写法见 [生成器教程](https://docs.python.org/3.11/tutorial/classes.html#generators)。
