01 · 运行代码、变量与基本控制流程

先从一行代码怎样运行开始，再看变量到底保存什么，最后写一个有输入、判断、循环和输出的小程序。这里不会要求你先背一套术语：每遇到一个词，都先看看它对应的实际现象。

在仓库根目录运行 `python scripts/check_handbook_examples.py --chapter 01 --show-output`，可以逐块验证本章标有 runnable 的例子。每块都能独立运行；assert 不输出内容，条件不成立时才会提醒你。

---

1）先分清：写代码、执行代码、显示结果

1.1 源文件和交互窗口

Python 源文件通常以 `.py` 结尾，终端用 `python 文件路径` 执行。交互窗口则适合只试一个表达式：输入 `python`，看到 `>>>` 后输入表达式，退出用 `exit()`。复制例子到文件时，不要把 `>>>` 一起复制。

```powershell
python --version
python examples/basics_lab.py
python
```

执行命令时还要看当前目录：相对路径从当前目录开始找，不是从你心里那个项目目录开始找。遇到“找不到文件”，先确认位置和文件名，再怀疑代码。

交互窗口可能自动显示一个表达式的结果，普通 `.py` 文件不会。下面真正负责显示的是 print；赋值只保存结果。

```python
# runnable: hb01_expression_and_print
total = 2 + 3
print(total)  # 5
assert total == 5
```

1.2 缩进就是代码块，不是排版装饰

Java 用大括号表示范围，Python 通常用四个空格缩进。冒号后的缩进语句属于这一段，退回上一层表示离开。不要把 Tab 和空格混在一起，也不要为了对齐注释改动代码的缩进。

```python
# runnable: hb01_indentation
enabled = True
messages = []
if enabled:
    messages.append("inside")
messages.append("outside")
print(messages)  # ['inside', 'outside']
assert messages == ["inside", "outside"]
```

把 enabled 改成 False，只跳过缩进的 append；最后一条仍执行。分号在某些位置语法允许，但不需要像 Java 那样每句都加。多行表达式可放在括号里，不必靠长长的一行。

---

2）变量不是固定类型的格子，而是对象的名字

2.1 赋值到底发生了什么

执行 `count = 3`，可以理解成让名字 count 指向整数对象 3。随后写 `count = "three"`，名字就改指向字符串对象，Python 不会因为前一次是整数就禁止这次赋值。

```python
# runnable: hb01_dynamic_binding
count = 3
assert type(count) is int
count = "three"
assert type(count) is str
print(count)  # three
```

这不是说业务代码应该随便换类型。一个变量始终承担明确的含义，通常更容易维护。动态类型表示解释器允许，不表示所有写法都值得用。

2.2 两个名字可以指向同一个列表

```python
# runnable: hb01_alias_and_rebind
first = [1, 2]
second = first
second.append(3)
assert first == [1, 2, 3]
assert second is first
second = [9]
assert second == [9]
assert first == [1, 2, 3]
assert second is not first
print(first, second)  # [1, 2, 3] [9]
```

按顺序看：第二行没有复制列表，只多了一个名字；append 修改共享的列表，因此 first 也看到 3。后来 `second = [9]` 才换了 second 的指向，first 没跟着换。

这条线索会贯穿函数传参、浅拷贝、默认参数和类变量。看到“怎么互相影响了”，先问是不是共用了一个对象。

2.3 ==、is 与 id，分别检查什么

`==` 比较值，`is` 判断是不是同一个对象。`id(obj)` 是对象当前生命周期内的身份标识，可以用来观察身份，但不要当永久业务编号。对象释放后，其标识可能被后来的对象重用。

```python
# runnable: hb01_identity
left = [1, 2]
right = [1, 2]
alias = left
assert left == right
assert left is not right
assert left is alias
assert id(left) == id(alias)
missing = None
assert missing is None
print(left == right, left is right)  # True False
```

不要拿普通数字、字符串试出一次 `is True` 就当规则。解释器可能复用一些不可变对象，这不影响你该用 `==` 比内容的原则。检查 None 用 `is None`。

---

3）常见类型：能做什么，比名字更重要

3.1 int、float、str、bool、None

int 表示整数，普通 Python 整数不像 Java int 固定只有 32 位；仍会受到内存和某些转换限制。float 是浮点数，不保证每个十进制小数都能精确表示。str 是文本，不会自动和数字混算。bool 只有 True、False；None 表示“没有这个值”，不是 0，也不是空字符串。

```python
# runnable: hb01_types
values = [42, 3.5, "42", True, None]
names = [type(value).__name__ for value in values]
assert names == ["int", "float", "str", "bool", "NoneType"]
assert 2 ** 100 > 2 ** 63
assert isinstance(True, int)
assert type(True) is not int
print(names)
```

`type(x)` 查看直接类型；`isinstance(x, T)` 也认可子类。bool 是 int 的子类，因此严格要求“整数但不要布尔值”的校验，不能只靠 `isinstance(value, int)`。一般业务不需要每行都检查类型；知道边界即可。

3.2 可变和不可变，说的是对象能不能原地改

列表、字典、集合可以原地增删。字符串、整数、元组不能以同样方式替换自身内容。重新给变量赋值不算“把不可变对象变了”，只是换了指向。

```python
# runnable: hb01_mutability
text = "java"
upper = text.upper()
assert text == "java"
assert upper == "JAVA"
items = [1]
result = items.append(2)
assert items == [1, 2]
assert result is None
print(text, upper, items)  # java JAVA [1, 2]
```

append 已经改好原列表，返回 None；不要写 `items = items.append(2)`。字符串 upper 返回处理后的字符串，要接住它才有后续用途。方法是否原地修改、返回什么，是看例子时必须追的两件事。

---

4）输入和转换：看起来像数字，不等于已经是数字

4.1 input 成功读取时返回 str

下面是需要人在终端输入的交互片段，不会由本章验证器自动执行。先保存为 `.py` 文件，再从终端运行：

```python
# fragment: interactive_input_requires_terminal
raw_age = input("age: ")
age = int(raw_age)
print(age + 1)
```

输入 18 后，raw_age 是 `"18"`；int 才把它转换为整数。input 会去掉读入行末的换行，但不会把你输入的普通两端空格全删掉。遇到输入结束而没有读到数据时，会抛 EOFError，不是返回 None。

不需要交互时，可以直接用字符串模拟这一步，方便反复验证各种输入：

```python
# runnable: hb01_numeric_conversion
raw = " 18 "
age = int(raw)
assert age == 18
assert float("3.5") == 3.5
assert int(3.9) == 3
assert int(-3.9) == -3
assert str(18) == "18"
assert int("ff", 16) == 255
for invalid in ["", "18x", "3.5"]:
    try:
        int(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError(invalid)
print(age + 1)  # 19
```

`int(3.9)` 丢掉小数部分，向零截断；`int("3.9")` 则不接受这个整数文本。它们走的是两种输入转换，不能把前者的行为照搬到后者。`int(text, base)` 的第二个参数表示进制，只在这类字符串/字节输入转换中使用。

4.2 bool 不会读懂文本 true / false

```python
# runnable: hb01_parse_boolean
assert bool("False") is True
assert bool("") is False
raw = " FALSE "
normalized = raw.strip().lower()
if normalized in {"true", "1", "yes"}:
    enabled = True
elif normalized in {"false", "0", "no"}:
    enabled = False
else:
    raise ValueError("unrecognized boolean text")
assert enabled is False
print(enabled)  # False
```

bool 只看对象的真假规则，非空字符串为真。配置值则要先规定允许哪些文本，未知文本明确报错，别把拼错的 `"ture"` 默默当成 False。

---

5）print 与格式化：显示方式不等于数据本身

5.1 print 的 sep、end、file

`print(a, b, sep=" ", end="\n")` 默认用空格隔开多个对象，末尾加换行。sep 控制对象之间，end 控制最后；file 可以指定输出位置。下面用内存中的文本缓冲区检查结果，没有写磁盘文件。

```python
# runnable: hb01_print_options
from io import StringIO

buffer = StringIO()
returned = print("a", 2, "c", sep=" | ", end="!", file=buffer)
assert buffer.getvalue() == "a | 2 | c!"
assert returned is None
print(buffer.getvalue())  # a | 2 | c!
```

print 会把对象转换成显示用的文本，但不会反过来把原数字变量永久改成字符串。缓冲区只用来验证输出，可理解成一份暂存在内存里的文本。

5.2 % 格式、format 与 f-string

旧代码常见 `%s`，新代码通常用 f-string 更直观。字符串前有 f，大括号里才会求值；少了 f，就是普通文本。

```python
# runnable: hb01_format_styles
name, score = "Lin", 95.678
old = "name=%s, score=%.2f" % (name, score)
method = "name={}, score={:.2f}".format(name, score)
modern = f"name={name}, score={score:.2f}"
assert old == method == modern == "name=Lin, score=95.68"
assert "{name}" == "{name}"
assert f"{name}" == "Lin"
assert score == 95.678
print(modern)
```

`.2f` 是把显示结果保留两位小数，不会改变 score。真实数值如何计算、保存和舍入，是另一件事。

5.3 宽度、对齐、补零与调试输出

冒号后是格式说明。`>8` 表示最少宽度 8、靠右；`<8` 靠左；`^8` 居中。宽度太小时不会截断内容。`04d` 是十进制整数最少四位、不足补零。

```python
# runnable: hb01_format_details
assert f"{'py':>5}" == "   py"
assert f"{'py':<5}" == "py   "
assert f"{'py':^6}" == "  py  "
assert f"{42:04d}" == "0042"
assert f"{12345:04d}" == "12345"
assert f"{1234567:,}" == "1,234,567"
assert f"{0.256:.1%}" == "25.6%"
assert f"{' a '!r}" == "' a '"
assert f"{{value}}" == "{value}"
print(f"{42:04d}", f"{0.256:.1%}")  # 0042 25.6%
```

`!r` 使用 repr 显示，适合观察引号、空格和转义；要输出大括号本身则写双大括号。

---

6）运算：除法、余数和优先级别按 Java 习惯猜

6.1 /、//、%、**

`/` 是通常意义的除法，整数相除也可能得到 float；`//` 向负无穷方向取整，负数时与向零截断不同；`%` 是对应余数；`**` 表示乘方，不是 `^`。

```python
# runnable: hb01_arithmetic
assert 7 / 2 == 3.5
assert 7 // 2 == 3
assert -7 // 2 == -4
assert int(-7 / 2) == -3
assert -7 % 2 == 1
assert (-7 // 2) * 2 + (-7 % 2) == -7
assert 2 ** 3 == 8
assert 2 ^ 3 == 1
assert -2 ** 2 == -4
assert (-2) ** 2 == 4
print(7 / 2, -7 // 2, -7 % 2)  # 3.5 -4 1
```

对除数为正的例子，余数不会因为被除数为负就直接变成负数。`-7 = (-4) × 2 + 1` 同时解释了整除和余数。优先级不确定时加括号，比让读代码的人一起猜更好。

6.2 浮点误差与比较

```python
# runnable: hb01_float_comparison
from math import isclose
from decimal import Decimal

value = 0.1 + 0.2
assert value != 0.3
assert isclose(value, 0.3, rel_tol=1e-9, abs_tol=1e-12)
exact = Decimal("0.1") + Decimal("0.2")
assert exact == Decimal("0.3")
assert round(2.5) == 2
assert round(3.5) == 4
print(value, exact)  # 0.30000000000000004 0.3
```

float 常用二进制近似，显示成短小数不代表内部精确。isclose 用容差比较近似结果；Decimal 从字符串创建，可以避免先把十进制文本变成 float 再带入误差。round 在恰好中间时采用向偶数舍入，也不是所有场景都按口头的“四舍五入”理解。

6.3 位运算可用于标志，但不要和逻辑运算混写

```python
# runnable: hb01_bit_flags
READ, WRITE = 1, 2
permissions = READ | WRITE
assert permissions == 3
assert permissions & READ == READ
assert permissions & 4 == 0
assert 1 << 3 == 8
assert 8 >> 2 == 2
assert ~0 == -1
print(permissions)  # 3
```

这里 `|`、`&` 处理整数的二进制位；条件连接通常写 and、or。相同符号在集合里又表示集合运算，因此要结合操作对象的类型理解。

---

7）条件判断：真假、短路和分支

7.1 哪些值为假

None、False、数值零和空容器通常为假。自定义对象还可通过自己的协议决定真假，因此“其他对象为真”只是常用内置类型的入门规则。

```python
# runnable: hb01_truth_values
for value in [None, False, 0, 0.0, "", [], (), {}, set()]:
    assert not value
assert bool("0") is True
assert bool([0]) is True
assert bool(-1) is True
print(bool([]), bool([0]))  # False True
```

`[0]` 不是空列表，里面那个 0 为假，不等于列表本身为假。检查有没有项与检查每一项的内容，是不同的问题。

7.2 and / or 会短路，而且返回操作数

and 遇到假值就不需要继续，or 遇到真值就不需要继续；它们返回决定结果的操作数，不保证返回 bool。not 才会得到明确的布尔值。

```python
# runnable: hb01_short_circuit
calls = []
def expensive():
    calls.append("called")
    return "value"

assert ("name" or expensive()) == "name"
assert ("" and expensive()) == ""
assert calls == []
assert ("" or expensive()) == "value"
assert calls == ["called"]
assert (0 or 10) == 10
timeout = 0
chosen = 10 if timeout is None else timeout
assert chosen == 0
print(chosen)  # 0
```

如果超时 0 是合法配置，就不能用 `timeout or 10` 补默认值，那会误把 0 替换掉。只想处理“没提供”，应明确判断 None。

7.3 if / elif / else 从上往下只选一条

```python
# runnable: hb01_branches
score = 85
if score >= 90:
    level = "A"
elif score >= 60:
    level = "B"
else:
    level = "C"
assert level == "B"
assert 60 <= score < 90
print(level)  # B
```

85 没有进入第一条，进入第二条后不再继续选分支。连续写多个独立 if 则可能执行多条。`60 <= score < 90` 是链式比较，表示两个条件都满足；不是先得到一个 bool 再拿它与 90 比。

---

8）循环：每轮取到什么，结束后留下什么

8.1 for 通常直接取元素

```python
# runnable: hb01_for_accumulation
total = 0
history = []
for number in [2, 4, 6]:
    total += number
    history.append(total)
assert history == [2, 6, 12]
assert total == 12
print(history)  # [2, 6, 12]
```

第一轮 total 从 0 到 2，第二轮在旧值 2 上加 4，第三轮再加 6。不是每轮把 total 重新设为 0；初始化放在哪里，决定数据是否跨轮保留。

8.2 while 先判断，再决定要不要进入

```python
# runnable: hb01_while
remaining = 3
visited = []
while remaining > 0:
    visited.append(remaining)
    remaining -= 1
assert visited == [3, 2, 1]
assert remaining == 0
print(visited)  # [3, 2, 1]
```

每轮都要让状态向结束条件靠近。把减一漏掉，条件一直为真，就会无限循环。若初值是 0，循环体一次也不会执行。

8.3 break、continue 和循环 else

continue 只跳过本轮余下部分，break 退出当前这一层循环。循环后面的 else 表示“没有被 break 提前结束”，不是“循环条件一开始为假”这一种情况才执行。

```python
# runnable: hb01_loop_control
visited = []
for value in [0, 1, 2, 3, 4]:
    if value == 0:
        continue
    if value == 3:
        break
    visited.append(value)
else:
    visited.append("completed")
assert visited == [1, 2]

target = 9
for value in [1, 2, 3]:
    if value == target:
        found = True
        break
else:
    found = False
assert found is False
print(visited, found)  # [1, 2] False
```

嵌套循环里的 break 只退出最近的一层，外层不会自动结束。变量作用域也别照搬 Java 花括号：普通 if、for、while 不创建独立的局部作用域；但分支没执行、循环没进入时，里面的名字可能根本没被赋值。

---

9）错误信息怎么读，assert 在这里做什么

从报错最后一行看异常类型和说明，再沿调用位置往上找。SyntaxError 是代码没能按语法解析；NameError 常见于名字没定义；TypeError 常见于操作对象类型不合适；ValueError 常见于类型形式可以、值的内容不合要求。

```python
# runnable: hb01_expected_errors
for expression, error_type in [("'2' + 3", TypeError), ("int('bad')", ValueError)]:
    try:
        eval(expression)
    except error_type:
        pass
    else:
        raise AssertionError(expression)
assert 2 + 3 == 5
print("expected errors confirmed")
```

这里 eval 只执行我们写死的两个示例表达式，绝不能拿来执行不可信输入。assert 用于演示和测试，表达“结果必须满足这个条件”；开启 Python 优化模式时 assert 可能被移除，生产输入校验应明确写 if 和 raise，不能只靠 assert。

---

10）动手题与参考答案

10.1 端口文本校验

题目：把文本转换为 1 到 65535 的整数。不合法时抛 ValueError；`" 8080 "` 合法，`"bad"`、`"0"` 不合法。先想清楚“转换失败”和“范围不对”是两步。

```python
# runnable: hb01_exercise_port
def parse_port(raw):
    port = int(raw)
    if not 1 <= port <= 65535:
        raise ValueError("port out of range")
    return port

assert parse_port(" 8080 ") == 8080
for bad in ["bad", "0", "65536"]:
    try:
        parse_port(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(bad)
print(parse_port("443"))  # 443
```

10.2 累计前 N 个偶数

题目：不用求和公式，算出 2、4、6、8 的和，并保存每一步累计值。不要把初始化写到循环里面。

```python
# runnable: hb01_exercise_even_sum
total = 0
steps = []
for number in range(2, 9, 2):
    total += number
    steps.append(total)
assert steps == [2, 6, 12, 20]
assert total == 20
print(steps)
```

10.3 预测共享与重新赋值

题目：两个名字原本指向同一列表，先添加元素，再把其中一个名字赋为新列表，另一个最终看到什么？先写答案再运行。

```python
# runnable: hb01_exercise_alias
left = [10]
right = left
right.append(20)
right = [30]
assert left == [10, 20]
assert right == [30]
print(left, right)  # [10, 20] [30]
```

---

11）查阅位置

本章用 Python 3.11 的语法范围。需要核对 input、print、int、isinstance 等参数时查 [内置函数](https://docs.python.org/3.11/library/functions.html)；真假与数值运算查 [标准类型](https://docs.python.org/3.11/library/stdtypes.html)；分支循环查 [控制流程教程](https://docs.python.org/3.11/tutorial/controlflow.html)；格式说明查 [格式说明迷你语言](https://docs.python.org/3.11/library/string.html#format-specification-mini-language)。
