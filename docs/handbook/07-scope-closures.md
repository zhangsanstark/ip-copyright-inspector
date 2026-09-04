07 作用域、闭包与变量保存在哪里

这一章的核心不是背 LEGB 四个字母，而是回答：程序看到一个名字时去哪里找？找到以后，重新赋值是在改哪一层？

阅读导航：1–4 拆开名字查找、赋值与作用域；5–7 解释闭包、晚期绑定和修复；8 是完整练习。

```powershell
python scripts/check_handbook_examples.py --chapter 07 --show-output
```

---

1）同名不一定是同一个变量

1.1 从身边找起，找到就停

```python
# runnable: hb07_lookup
label = "模块里的 label"

def outer():
    label = "外层函数里的 label"

    def inner():
        return label

    return inner()

assert outer() == "外层函数里的 label"
assert label == "模块里的 label"
```

`inner` 自己没有定义 `label`，就去外层函数找。找到后不再继续读模块里的同名变量。外层定义的 `label` 没有改掉模块里的 `label`；它们只是名字拼写相同。

LEGB 正是这个常见查找顺序的缩写。

| 查找位置 | 通俗理解 | 这个例子对应哪里 |
| --- | --- | --- |
| Local | 当前函数里的名字 | inner 自己的局部名字 |
| Enclosing | 外面套着的函数里的名字 | outer 的 label |
| Global | 当前模块的名字 | 文件顶层的 label |
| Builtins | Python 预先提供的名字 | len、print 等 |

它描述的是常见函数作用域中的名字查找。对象的 `obj.name` 是属性查找，不要把它直接套成 LEGB；类体也有自己的规则，第 12 章会区分。

1.2 内置名被遮住时，不是 Python 丢了那个函数

```python
# runnable: hb07_shadow_builtin
import builtins

def demo():
    len = 10
    try:
        len([1, 2])
    except TypeError:
        return builtins.len([1, 2])
    raise AssertionError("局部 len 是整数，不能调用")

assert demo() == 2
assert len([1, 2, 3]) == 3
```

局部 `len` 把内置函数挡住了，`len(...)` 就变成“调用整数 10”。临时排查可以用 `builtins.len` 明确找到内置函数，正常代码则应把变量改名为 `length`、`count` 等。

这里遮蔽只发生在函数内部；同一模块的函数外仍能使用内置 `len`。如果你在模块顶层写 `len = 10`，影响范围会更大。

---

2）赋值不是沿着 LEGB 找到最近那个名字再修改

2.1 为什么先打印再赋值也会报错

```python
# runnable: hb07_unbound_local
count = 10

def broken():
    print(count)
    count = 20

try:
    broken()
except UnboundLocalError:
    print("count 被认定为局部名字，但读取时还没绑定值")
else:
    raise AssertionError("应该报局部变量未绑定")
assert count == 10
```

Python 在分析函数时看到 `count = 20`，就把这个函数里的 `count` 认定为局部名字。执行到 `print(count)` 时，局部名字还没有值，不会因为赋值语句在后面，就临时去读全局那个 10。

所以“先查局部，没有就查全局”不是对这类情况的完整解释。一个名字已经被认定为局部，但尚未绑定值，与它根本不是局部名字，是两种情况。

2.2 global 明确修改当前模块的绑定

```python
# runnable: hb07_global
count = 10

def increment():
    global count
    count += 1
    return count

assert increment() == 11
assert count == 11
```

这里 `global count` 声明后面的 `count` 指向当前模块那一层。所谓“全局”不是全电脑、也不是所有 Python 文件共用一个名字；不同模块有各自的命名空间。

共享全局状态会让测试与并发更难推理。能通过参数传入、返回值交回的内容，通常不必用 `global`。使用它是明确的设计选择，不是遇到报错就加上的补丁。

2.3 改对象内容不等于给名字重新赋值

```python
# runnable: hb07_mutation_vs_rebinding
events = []

def record():
    events.append("A")

def broken_extend():
    events += ["B"]

record()
assert events == ["A"]
try:
    broken_extend()
except UnboundLocalError:
    print("+= 也属于赋值语句，需要处理绑定范围")
else:
    raise AssertionError("预期局部变量未绑定")
assert events == ["A"]
```

`events.append` 读取已有列表对象并调用方法，不重新绑定名字，因此不用 `global`。`events += ...` 在语法上包含赋值，名字会被认作局部；即使列表的 `+=` 可以原地修改对象，也不能跳过这一步。

判断时看清两件事：有没有给名字赋值，以及所用操作会不会修改对象。只背“可变对象不需要 global”容易在这里出错。

---

3）nonlocal：修改外面那层函数的绑定

```python
# runnable: hb07_nonlocal
def make_counter(start=0):
    count = start

    def increment(step=1):
        nonlocal count
        count += step
        return count

    return increment

counter = make_counter(10)
assert counter() == 11
assert counter(3) == 14
another = make_counter(100)
assert another() == 101
assert counter() == 15
```

第一次调用 `make_counter(10)` 产生一份 `count` 绑定。返回的 `increment` 一直用这份绑定。`nonlocal count` 表示这次重新赋值不是新建局部 `count`，而是改外层函数里的那份。

再调用一次 `make_counter(100)` 会产生另一份，因此两个计数器互不影响。不是所有名字叫 `count` 的闭包都共享同一个数字。

`nonlocal` 要求外层函数里已经有对应绑定；不能凭空在外层创建一个名字，也不能用它修改模块全局变量。它会选择最近的那层已有函数绑定。

计数器例子没有处理并发。两个线程同时调用时，复合读改写需要同步；加了闭包不会自动变成线程安全。

---

4）“没有块级作用域”到底说的是哪些块

4.1 if、for、while 不另开局部名字空间

```python
# runnable: hb07_blocks
def demo():
    if True:
        message = "可在后面使用"
    for index in range(3):
        pass
    return message, index

assert demo() == ("可在后面使用", 2)

def empty_loop():
    for never_assigned in []:
        pass
    return never_assigned

try:
    empty_loop()
except UnboundLocalError:
    print("循环没执行，名字也没有被赋值")
else:
    raise AssertionError("不应产生一个凭空的循环值")
```

这和 Java 常见的花括号局部变量范围不同。不过“块结束后能用”不代表“分支没进入或循环没执行时也有值”。赋值那一行必须实际发生。

4.2 推导式是重要的区别

```python
# runnable: hb07_comprehension_scope
index = 99
values = [index * 2 for index in range(3)]
assert values == [0, 2, 4]
assert index == 99
```

Python 3 的列表、集合和字典推导式的循环变量有自己的作用域，不会像普通 `for` 一样把循环目标留在外层。因此不要把“if/for 没有块级作用域”扩写成“所有带缩进或循环语法都没有独立作用域”。

---

5）闭包保留的是外层绑定，不是外层函数整段永远运行着

5.1 返回一个带配置的函数

```python
# runnable: hb07_multiplier
def make_multiplier(factor):
    def multiply(value):
        return value * factor
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)
assert double(5) == 10
assert triple(5) == 15
assert double.__name__ == "multiply"
```

按时间顺序读一次：

1. `make_multiplier(2)` 把 `factor` 绑定为 2。
2. 定义内层 `multiply`，其函数体引用外层 `factor`。
3. 外层返回的是 `multiply` 函数对象，没有执行乘法。
4. 外层这次调用结束，但内层需要的绑定仍被保留。
5. `double(5)` 才取出保存的 `factor`，算出 10。

这类“函数连同它需要的外层变量绑定”就是闭包。外层函数不一定必须使用 `return` 交出它，也可以把它存到列表或注册为回调。关键是内层函数引用了外层函数作用域里的名字，并能在后续继续使用。

5.2 两个函数可以共享一份状态

```python
# runnable: hb07_shared_cell
def make_balance(start):
    balance = start

    def add(amount):
        nonlocal balance
        balance += amount
        return balance

    def read():
        return balance

    return add, read

add, read = make_balance(100)
assert read() == 100
assert add(20) == 120
assert read() == 120
```

`add` 与 `read` 出自同一次外层调用，引用同一份 `balance`。一个修改后另一个能看见。闭包不是“函数创建时自动复制所有外层值”。这点直接关系到下一节的循环陷阱。

---

6）循环里的函数为什么全拿到了最后一个值

6.1 创建函数不等于执行函数体

```python
# runnable: hb07_late_binding
def build_bad():
    functions = []
    for factor in range(3):
        def multiply(value):
            return value * factor
        functions.append(multiply)
    return functions

functions = build_bad()
assert [function(10) for function in functions] == [20, 20, 20]
```

循环确实创建了三个不同的函数对象。问题不在“只创建了一个函数”，而在三个函数都引用同一轮外层调用里的 `factor` 绑定。

| 时刻 | factor 的当前值 | 此时有没有算乘法 |
| --- | --- | --- |
| 第一次创建函数 | 0 | 没有 |
| 第二次创建函数 | 1 | 没有 |
| 第三次创建函数 | 2 | 没有 |
| 循环结束后调用函数 | 2 | 现在才读取 factor |

“晚期绑定”就是实际调用时才读取这个绑定当前指向的值。`lambda` 常出现在这类问题里，但普通 `def` 一样会发生，不能说成 lambda 专属的坑。

6.2 修法一：利用默认参数定义时求值

```python
# runnable: hb07_default_capture
functions = []
for factor in range(3):
    functions.append(lambda value, factor=factor: value * factor)

assert [function(10) for function in functions] == [0, 10, 20]
assert functions[0](10, factor=7) == 70
```

右边的 `factor` 在创建函数时求值，左边的 `factor` 是这个新函数自己的参数。第一次默认值是 0，第二次是 1，第三次是 2。

代价是它出现在调用签名里，调用方仍然可以显式覆盖这个参数。所以它是一个简便写法，不是不可修改的“锁死变量”。

6.3 修法二：每轮调用工厂，获得独立绑定

```python
# runnable: hb07_factory_capture
def make_multiplier(factor):
    def multiply(value):
        return value * factor
    return multiply

functions = [make_multiplier(factor) for factor in range(3)]
assert [function(10) for function in functions] == [0, 10, 20]
```

每次 `make_multiplier` 调用都产生自己的外层局部绑定。这样对外仍只有一个 `value` 参数；如果希望配置不出现在调用参数里，工厂通常更清楚。

---

7）捕获对象不等于复制对象

```python
# runnable: hb07_capture_mutable
settings = {"prefix": "A"}
read_reference = lambda config=settings: config["prefix"]
read_snapshot = lambda config=settings.copy(): config["prefix"]

settings["prefix"] = "B"
assert read_reference() == "B"
assert read_snapshot() == "A"
```

默认参数保存的是对象引用。原字典内容后来改变，默认值仍指向原字典，就会读到新内容。这里 `.copy()` 只隔开顶层字典；如果里面再套字典，浅拷贝仍会共享内层对象。

想要固定一个简单值，可以直接取那个字段做默认值；想要保存结构快照，需要根据结构选择浅拷贝或深拷贝。先确定你要的是“以后读最新配置”还是“保存当时配置”，再决定写法。

闭包也会延长所引用对象的生命周期。把一个很大的列表抓进长期保存的回调里，即使外层函数结束，列表也未必能释放。它不是免费保存状态。

---

8）练习与参考实现

8.1 题目一：可调步长计数器

工厂接收起点和步长，返回两个函数：`next_value()` 每次推进，`reset()` 回到起点。两个函数必须共享当前值；两个工厂实例必须互不影响。

```python
# runnable: hb07_exercise_counter
def make_counter(start=0, step=1):
    current = start

    def next_value():
        nonlocal current
        current += step
        return current

    def reset():
        nonlocal current
        current = start
        return current

    return next_value, reset

next_a, reset_a = make_counter(10, 2)
next_b, _ = make_counter(100, 5)
assert next_a() == 12
assert next_a() == 14
assert reset_a() == 10
assert next_a() == 12
assert next_b() == 105
```

`current` 会被重新绑定，所以需要 `nonlocal`。`start` 和 `step` 只是读取，不需要。不要为了统一外观给所有外层变量都加声明。

8.2 题目二：给一组扩展名生成检查函数

输入 `['.txt', '.md', '.csv']`，生成三个函数，用它们分别检查同一个文件名。检查 `report.md` 的结果应为 `[False, True, False]`。

```python
# runnable: hb07_exercise_suffix
def make_checker(suffix):
    def check(filename):
        return filename.endswith(suffix)
    return check

checkers = [make_checker(suffix) for suffix in [".txt", ".md", ".csv"]]
assert [check("report.md") for check in checkers] == [False, True, False]
assert [check("report.txt") for check in checkers] == [True, False, False]
```

试着把工厂改为循环里的 `lambda filename: filename.endswith(suffix)`，解释错误版为什么会全检查 `.csv`。先解释，再动手改，比记住 `i=i` 四个字符更有用。

8.3 题目三：不使用 global 的调用统计

返回一个 `record(kind)` 函数，每次增加对应类别次数，再返回统计结果的副本。调用方修改返回字典，不应污染内部状态。

```python
# runnable: hb07_exercise_stats
def make_stats():
    counts = {}

    def record(kind):
        counts[kind] = counts.get(kind, 0) + 1
        return counts.copy()

    return record

record = make_stats()
snapshot = record("ok")
assert snapshot == {"ok": 1}
snapshot["ok"] = 999
assert record("ok") == {"ok": 2}
assert record("error") == {"ok": 2, "error": 1}
```

没有 `nonlocal counts` 也能运行，因为我们改的是字典内容，没有重新绑定 `counts`。返回副本则把读者容易忽略的“外部也能改同一对象”堵住了。

---

9）判断口诀要落到代码上

遇到名字问题，依次问：它在哪里被定义？函数里有没有给同名变量赋值？本次是在改对象还是改绑定？这份状态属于哪一次外层函数调用？函数创建与实际调用之间，状态有没有变化？

这五个问题比单独背 LEGB 更能帮助定位错误。

名字绑定规则可对照 [执行模型](https://docs.python.org/3.11/reference/executionmodel.html#resolution-of-names)，循环函数的常见问题可查 [Python 官方编程问答](https://docs.python.org/3.11/faq/programming.html#why-do-lambdas-defined-in-a-loop-with-different-values-all-return-the-same-result)。
