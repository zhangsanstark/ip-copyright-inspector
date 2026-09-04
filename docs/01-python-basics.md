Python 基础与容器

写过 Java，再看 Python，最容易卡住的往往不是少了分号，而是“这行代码到底改了原对象，还是得到了一个新对象”。把这件事弄清楚，列表复制、函数传参、字符串处理就能连起来理解。示例使用 Python 3.11 及以上版本。

查找顺序：1–2 是变量和输入输出；3–7 分别是字符串、列表、元组、字典、集合；8–12 是切片、遍历、zip、推导式和拆包；13–15 用来排错、动手验证和回顾。

配套代码在 `examples/basics_lab.py`。在仓库根目录执行：

```powershell
python examples/basics_lab.py
```

每次读一小段，先猜输出，再运行。猜错的地方先别急着背结论，沿着变量看一遍：它指向谁，谁被改了？之后可以暂时注释参考实现，自己写一遍。

1）变量与对象：换一个对象，还是改原来的内容

先记住容器的用途：一段文本用字符串，一排可增删的数据用列表，固定的一组值常用元组，按名称查数据用字典，去重和判断成员用集合。后面会逐个展开，不必一次记住所有方法。

1.1 先把代码运行起来

Python 源文件通常以 `.py` 结尾。下面三种方式最常用：

```powershell
python --version
python examples/basics_lab.py
python
```

最后一条命令会进入交互式解释器，适合快速验证一个表达式。退出时可输入 `exit()`。

先对照几个写 Java 时容易顺手写错的地方：

| Python | Java 对照 | 要点 |
| --- | --- | --- |
| 变量直接绑定对象 | 变量有编译期声明类型 | Python 变量名本身没有固定类型 |
| 缩进形成代码块 | 大括号形成代码块 | 通常使用 4 个空格，不能随意混用 Tab |
| `None` | `null` | 应使用 `is None` 判断 |
| `True`、`False` | `true`、`false` | Python 布尔值首字母大写 |
| `and`、`or`、`not` | `&&`、`||`、`!` | Python 逻辑运算会短路，并可能返回操作数本身 |
| `//` | 整数除法 | Python 的 `//` 是向下取整，不是向零截断 |

1.2 两个变量，可能指向同一个对象

常用内置类型包括 `int`、`float`、`str`、`bool`。Python 的整数没有 Java `int` 的 32 位上限，通常只受可用内存限制。

```python
age = 30
price = 19.9
name = "Ada"
enabled = True

print(type(age))       # <class 'int'>
print(isinstance(age, int))  # True
```

`type(x)` 返回对象的直接类型；业务代码中判断类型时，`isinstance(x, SomeType)` 通常更合适，因为它也认可子类。

看下面的 `b = a`：它没有再造一个列表，只是让 `b` 也指向 `a` 指向的列表。所以从 `b` 添加元素，再从 `a` 看，内容同样变了。这就是“变量保存对象引用”的具体含义。

```python
a = [1, 2]
b = a
print(id(a) == id(b))  # True

b.append(3)
print(a)               # [1, 2, 3]
```

比较时先问自己：想知道“内容一样吗”，还是“本来就是同一个对象吗”？前者用 `==`，后者用 `is`。`id()` 可以辅助观察对象身份：

```python
x = [1, 2]
y = [1, 2]

print(x == y)  # True，内容相同
print(x is y)  # False，不是同一个列表对象
print(x is None)  # False
```

不要用 `is` 比较普通数字或字符串。某些小整数、短字符串可能被解释器复用，这属于实现细节，不能作为业务逻辑依据。

1.3 可变与不可变：原对象能不能直接改

把字符串变成大写后，原字符串还在；给列表添加元素后，原列表已经变了。这两种行为分别对应“不可变”和“可变”：

| 类型 | 是否可变 | 修改时发生什么 |
| --- | --- | --- |
| `int`、`float`、`bool` | 否 | 产生或绑定到另一个对象 |
| `str` | 否 | 字符串方法返回新字符串 |
| `tuple` | 否 | 元组自身元素引用不能替换 |
| `list`、`dict`、`set` | 是 | 可以原地增删改 |

```python
text = "java"
upper_text = text.upper()
print(text)        # java
print(upper_text)  # JAVA

numbers = [1, 2]
result = numbers.append(3)
print(numbers)     # [1, 2, 3]
print(result)      # None
```

这里别漏看最后一行：`append()` 已经把列表改好了，返回的是 `None`，不是修改后的列表。所以写 `numbers.append(3)` 就够了；写成 `numbers = numbers.append(3)`，反而会把变量变成 `None`。多数原地修改列表的方法都有这个特点。

2）输入与输出：先转对类型，再整理显示方式

2.1 输入的数字，起初也是字符串

在终端输入 `30`，`input()` 读到的是字符串 `"30"`，不是整数 `30`。因此，要算“明年几岁”，先用 `int()` 转一下：

```python
raw_age = input("age: ")
age = int(raw_age)
print(age + 1)
```

如果输入不是合法整数，`int()` 会抛出 `ValueError`：

```python
try:
    count = int("12x")
except ValueError as exc:
    print("invalid integer", exc)
```

常见转换有 `int("42")`、`float("3.14")`、`str(42)` 和 `bool(value)`。但 `bool()` 不会替你读懂英文：`bool("False")` 仍是 `True`，因为这个字符串不为空。配置文件里的 `"false"` 要按允许的文本值判断：

```python
enabled = "false".strip().lower() in {"1", "true", "yes", "on"}
print(enabled)  # False
```

`print()` 可以一次输出多个值：

```python
name = "Lin"
score = 95.678
print("name:", name, "score:", score)
print("a", "b", "c", sep=" | ", end="\n")
```

2.2 格式化：把变量放进输出文本

旧式 `%s` 格式仍能见到：

```python
name = "Lin"
score = 95.678
print("name=%s, score=%.2f" % (name, score))
```

f-string 更接近“在要插入内容的位置直接写变量”，新代码通常用它更直观：

```python
print(f"name={name}, score={score:.2f}")
print(f"{1234567:,}")       # 1,234,567
print(f"{0.256:.1%}")       # 25.6%
print(f"{name!r}")          # 'Lin'，适合调试
```

常用格式说明：

| 写法 | 含义 | 示例结果 |
| --- | --- | --- |
| `{x:.2f}` | 固定两位小数 | `3.14` |
| `{x:>8}` | 宽度 8，右对齐 | 前面补空格 |
| `{x:<8}` | 宽度 8，左对齐 | 后面补空格 |
| `{x:^8}` | 宽度 8，居中 | 两侧补空格 |
| `{x:04d}` | 整数宽度 4，补零 | `0042` |

2.3 条件判断：空值为假，and / or 不一定返回布尔值

判断“列表里有没有东西”，不必总写 `len(items) == 0`。`None`、`False`、数值零，以及空字符串、空列表、空元组、空字典、空集合，在条件里都按假处理；其他对象通常按真处理：

```python
items = []
if not items:
    print("empty")
```

`and` 与 `or` 不一定返回 `bool`，它们返回决定结果的那个操作数：

```python
display_name = "" or "anonymous"
print(display_name)  # anonymous

token = "abc"
result = token and token.upper()
print(result)        # ABC
```

因此 `name or "anonymous"` 可以补默认名字。但要想一想：`0` 或空字符串算不算有效输入？如果算，`or` 就会误把它换掉；只想处理 `None` 时，老老实实判断 `value is None`。

3）字符串：查找、清理、拆开，再拼起来

这一组按实际处理文本的顺序看：先取字符，再查找内容，接着拆分和清理，最后检查格式。

3.1 写法与下标

字符串是不可变字符序列，可使用单引号、双引号或三引号。三引号适合多行文本和文档字符串。

```python
single = 'hello'
double = "hello"
multi = """line 1
line 2"""
```

下标从 0 开始，负下标从末尾倒数：

```python
word = "python"
print(word[0])   # p
print(word[-1])  # n
```

字符串越界下标会抛出 `IndexError`，而越界切片通常会安全截断。

3.2 查找：找不到时，是返回值还是报错

| 方法 | 找到时 | 找不到时 | 适合场景 |
| --- | --- | --- | --- |
| `find(sub)` | 返回首次下标 | 返回 `-1` | 不希望异常 |
| `rfind(sub)` | 返回最右下标 | 返回 `-1` | 从右查找 |
| `index(sub)` | 返回首次下标 | 抛 `ValueError` | 找不到属于错误 |
| `rindex(sub)` | 返回最右下标 | 抛 `ValueError` | 找不到属于错误 |
| `count(sub)` | 返回次数 | 返回 `0` | 统计非重叠出现次数 |

```python
text = "banana"
print(text.find("na"))    # 2
print(text.rfind("na"))   # 4
print(text.find("xy"))    # -1
print(text.count("na"))   # 2
```

`find()` 最容易踩的坑是：没找到返回 `-1`，而 `text[-1]` 又恰好能取最后一个字符。拿查找结果当下标之前，一定先判断是不是 `-1`，否则代码没报错，结果却错了。

3.3 拆分、替换与拼接

先把三个方法的参数分清：`split(sep, maxsplit)` 的 `sep` 是按什么拆，`maxsplit` 是最多拆几次，不是最多得到几项；`replace(old, new, count)` 的 `count` 是最多替换几次；`separator.join(parts)` 则把分隔符放在相邻两项之间，不会自动加到开头和结尾。

```python
raw = "java,python,go"
parts = raw.split(",", maxsplit=1)
print(parts)  # ['java', 'python,go']

text = "one one one"
print(text.replace("one", "1", 2))  # 1 1 one

words = ["clean", "small", "functions"]
print(" ".join(words))  # clean small functions
```

`split()` 会移除实际用来切分的分隔符；达到 `maxsplit` 指定的次数后，剩余部分保持原样，所以前面的 `"python,go"` 里仍有逗号。拼接则写成 `"分隔符".join(一组字符串)`，不是 `列表.join()`；可以和 Java 的 `String.join()` 放在一起记。列表里如果有数字，要先转成字符串：

```python
numbers = [1, 2, 3]
print(",".join(map(str, numbers)))  # 1,2,3
```

一行连写看着短，但刚接触时容易不知道每一步拿到了什么。先把 `"  Java, Python,Go  "` 拆成四步：

```python
raw = "  Java, Python,Go  "
trimmed = raw.strip()
parts = trimmed.split(",")
cleaned = []
for part in parts:
    cleaned.append(part.strip().lower())
result = " | ".join(cleaned)

print(repr(trimmed))  # 'Java, Python,Go'
print(parts)          # ['Java', ' Python', 'Go']
print(cleaned)        # ['java', 'python', 'go']
print(result)         # java | python | go
```

外层的 `strip()` 只处理整段文本的两端，不会删掉逗号后、`Python` 前的空格；因此拆分后还要给每一项做 `part.strip()`。`repr()` 把字符串连同引号显示出来，方便看清空格还在不在。理解上面的普通循环后，再缩成 `[part.strip().lower() for part in parts]` 就不会靠猜了。

拆分方式不同，空项的处理也不同：

```python
print(" a  b \t c ".split())  # ['a', 'b', 'c']
print("a,,b,".split(","))     # ['a', '', 'b', '']
print("".split(","))          # ['']
print("".split())             # []
print("-".join([]))           # 输出空字符串，即空行
print("-".join(["a"]))        # a
```

不传 `sep` 时，`split()` 按连续空白拆分，会忽略两端空白，不产生这些空项；明确按逗号拆时，两个逗号之间没有内容，也会保留一个 `""`。所以解析用户输入时，要自己决定空项是跳过、保留，还是报错。不能把空字符串 `""` 当分隔符传给 `split()`，那会抛 `ValueError`。

3.4 大小写、两端空白与对齐

处理输入时，`strip()` 很常见；统一大小写用 `lower()` 或 `upper()`。`capitalize()` 只把开头改为大写，其余改为小写；`title()` 则按单词处理。对齐方法主要用在日志或终端输出里：

```python
text = "  pyThon backend  "
print(text.strip())
print(text.lstrip())
print(text.rstrip())
print(text.lower())
print(text.upper())
print(text.capitalize())
print(text.title())

print("42".rjust(5, "0"))  # 00042
print("py".ljust(5, "."))  # py...
print("py".center(6, "-")) # --py--
```

`strip("ab")` 不是删除两端完整的 `"ab"`。它会从两端不断去掉 `a` 或 `b`，直到碰到别的字符才停：

```python
print("abbaXabba".strip("ab"))  # X
```

若要删除固定前后缀，Python 3.9 及以上可用 `removeprefix()` 和 `removesuffix()`：

```python
print("Bearer token".removeprefix("Bearer "))  # token
print("report.csv".removesuffix(".csv"))       # report
```

3.5 判断：检查前后缀、字母、数字和空白

```python
print("python.py".startswith("py"))     # True
print("python.py".endswith((".py", ".pyi")))  # True
print("Python".isalpha())                # True
print("123".isdigit())                   # True
print("abc123".isalnum())                # True
print(" \t\n".isspace())                 # True
```

这些方法回答的是各自的小问题，不等于完整的输入校验。例如 `"²".isdigit()` 是 `True`，但 `int("²")` 会失败。因此“全是数字字符”和“能转成整数”不是同一个判断。只允许 ASCII 的 `0` 到 `9` 时，可检查字符范围或使用正则表达式。

3.6 常用方法速查

| 类别 | 方法 |
| --- | --- |
| 查找 | `find`、`rfind`、`index`、`rindex`、`count` |
| 修改并返回新串 | `replace`、`removeprefix`、`removesuffix` |
| 拆分拼接 | `split`、`rsplit`、`splitlines`、`partition`、`join` |
| 大小写 | `lower`、`upper`、`capitalize`、`title`、`swapcase`、`casefold` |
| 两端处理 | `strip`、`lstrip`、`rstrip` |
| 对齐填充 | `ljust`、`rjust`、`center`、`zfill` |
| 判断 | `startswith`、`endswith`、`isalpha`、`isdigit`、`isalnum`、`isspace`、`islower`、`isupper` |

做不区分大小写的文本比较时，国际化场景下 `casefold()` 比 `lower()` 更强：

```python
print("straße".casefold() == "STRASSE".casefold())  # True
```

字符串记忆口诀：`find` 找不到给 `-1`，`index` 找不到就报错；`split` 负责拆，`join` 负责装；字符串方法多数返回新字符串，不会原地改。

小练习：把 `"  Java,Python,Go  "` 整理成 `"java | python | go"`。先想清楚 `strip`、`split`、列表推导式、`join` 的执行顺序，再运行验证。

4）列表：按顺序存放，随时增删改

一组用户、一批订单、几条待处理记录，都可以放进列表。它保留顺序，也允许增删改，使用感觉更接近 Java 的动态数组。虽然能混放不同类型，但让一个列表只装同一类业务数据，后续代码会好读很多。

下面依次看添加、删除、读取修改、复制和排序。

```python
users = ["alice", "bob"]
mixed = [1, "two", True, None]
```

4.1 添加：append 放一个，extend 放一批

```python
items = [1, 2]
items.append([3, 4])
print(items)  # [1, 2, [3, 4]]

items = [1, 2]
items.extend([3, 4])
print(items)  # [1, 2, 3, 4]

items.insert(1, 99)
print(items)  # [1, 99, 2, 3, 4]
```

`append(x)` 把 `x` 作为一个整体加入；`extend(iterable)` 逐个加入可迭代对象中的元素。执行 `items.extend("ab")` 会加入字符 `"a"` 和 `"b"`。

拿 `extend([3, 4])` 来说，过程可以拆成“取出 3，追加 3；再取出 4，追加 4”。对下面这两个独立列表，效果就等同于这个循环：

```python
items = [1, 2]
incoming = [3, 4]
for value in incoming:
    items.append(value)
    print(items)

# [1, 2, 3]
# [1, 2, 3, 4]
```

`insert(index, value)` 是插到该下标前面。原来的元素顺次后移，不是把它覆盖掉；覆盖才写 `items[index] = value`。另外，传入空列表也能看清 append 和 extend 的区别：

```python
first = [1]
second = [1]
first.append([])
second.extend([])
print(first)   # [1, []]：真的加进了一个空列表
print(second)  # [1]：空列表没有元素可以逐项加入
```

4.2 删除：按位置删，还是按值删

```python
items = [10, 20, 20, 30]
removed = items.pop(1)
print(removed, items)  # 20 [10, 20, 30]

items.remove(20)
print(items)           # [10, 30]

del items[0]
print(items)           # [30]

items.clear()
print(items)           # []
```

区别如下：

- `pop(index)` 按下标删除并返回元素，默认删除最后一个；越界抛 `IndexError`。
- `remove(value)` 只删除第一个匹配值；找不到抛 `ValueError`。
- `del` 是语句，可删除元素、切片或整个变量绑定。
- `clear()` 原地清空，仍保留同一个列表对象。

顺着上面的例子看：`pop(1)` 先删掉下标 1 的第一个 `20`，剩下 `[10, 20, 30]`；接着 `remove(20)` 按值找到现在仅剩的 `20`，再删成 `[10, 30]`。列表删完一项后，下标会重新接上，所以后续下标要按当前列表来理解。

“清空列表”和“删除变量”也不是一回事：

```python
items = [1, 2]
alias = items
items.clear()
print(alias)       # []：两个名字看到的列表都被清空
del items
print(alias)       # []：列表仍然可以通过 alias 访问
```

此时再访问 `items` 会得到 `NameError`，但 `alias` 没有消失。空列表上调用 `pop()` 则会得到 `IndexError`，不存在的值交给 `remove()` 会得到 `ValueError`；需要容忍空数据时，要在调用前判断或明确捕获相应异常。

4.3 修改、查找与遍历

```python
items = [10, 20, 30]
items[1] = 99
items[0:2] = [1, 2, 3]
print(items)  # [1, 2, 3, 30]

print(items.index(3))
print(items.count(3))
print(30 in items)

for index, value in enumerate(items, start=1):
    print(index, value)
```

也可以使用 while 按下标遍历。它适合“需要自己控制下标变化”的场景；普通逐项读取优先用 for：

```python
index = 0
while index < len(items):
    print(index, items[index])
    index += 1
```

二维列表通过连续下标访问：

```python
matrix = [[1, 2], [3, 4], [5, 6]]
print(matrix[2][1])  # 6
```

4.4 复制：外层换了，内层可能还共用

复制一个二维列表后，改副本却影响了原数据，通常不是 `copy()` 失灵，而是只复制了一层。`copy()` 和 `[:]` 得到新的外层列表，里面的小列表仍是原来那几个，这叫浅拷贝：

```python
original = [[1], [2]]
shallow = original.copy()
shallow[0].append(99)
print(original)  # [[1, 99], [2]]
```

不要只记“浅拷贝不独立”，要看清独立到哪一层。重新从一份干净数据开始：

```python
original = [[1], [2]]
shallow = original.copy()
print(shallow is original)        # False：外层是两个列表
print(shallow[0] is original[0])  # True：第一个内层列表是同一个

shallow.append([3])
print(original)                   # [[1], [2]]：外层追加没有影响原表

shallow[0] = [9]
print(shallow)                    # [[9], [2], [3]]
print(original)                   # [[1], [2]]：只换了副本第一格的指向
```

`shallow[0].append(99)` 是先找到共享的小列表，再修改它；`shallow[0] = [9]` 是把副本的第一格改指向新列表。两个语句只差一点写法，动的却不是同一层。判断复制问题时，先问“这一句改的是外层位置，还是里面那个对象”。

如果需要像下面这样，让嵌套列表也各自独立，可以用标准库的 `copy.deepcopy()`：

```python
from copy import deepcopy

original = [[1], [2]]
independent = deepcopy(original)
independent[0].append(99)
print(original)  # [[1], [2]]
```

下面的乘法也有类似问题：`[[0] * 3] * 2` 没有造出两行独立数据，而是重复引用了同一行。要让每行独立，就在推导式里每次新建一行：

```python
wrong = [[0] * 3] * 2
wrong[0][0] = 9
print(wrong)  # [[9, 0, 0], [9, 0, 0]]

right = [[0] * 3 for _ in range(2)]
right[0][0] = 9
print(right)  # [[9, 0, 0], [0, 0, 0]]
```

错误版本可以想成先做 `row = [0, 0, 0]`，再做 `[row, row]`：两行实际是同一个对象。正确版本每循环一次，都重新执行 `[0] * 3`，所以得到两个不同的行列表。这里 `_` 只是普通变量名，表示“不需要使用这次循环的序号”。

4.5 排序与反转：sort 改原表，sorted 返回新表

`list.sort()` 原地排序并返回 `None`；`sorted()` 接受任意可迭代对象并返回新列表。

```python
numbers = [3, 1, 2]
ordered = sorted(numbers)
print(numbers)  # [3, 1, 2]
print(ordered)  # [1, 2, 3]

numbers.sort(reverse=True)
print(numbers)  # [3, 2, 1]

numbers.reverse()
print(numbers)  # [1, 2, 3]
```

排序时 `key` 告诉 Python“拿什么来比较”。下面先比负分数，再比年龄，所以分数高的在前，同分时年龄小的在前。Python 排序还是稳定的：比较键完全相同时，原本谁在前，排完仍是谁在前。

```python
users = [
    {"name": "A", "score": 90, "age": 30},
    {"name": "B", "score": 95, "age": 31},
    {"name": "C", "score": 95, "age": 25},
]

users.sort(key=lambda user: (-user["score"], user["age"]))
print([user["name"] for user in users])  # ['C', 'B', 'A']
```

排序键没有把原字典里的分数改成负数，只是临时拿来比较。上面三人的比较键分别是 A 的 `(-90, 30)`、B 的 `(-95, 31)`、C 的 `(-95, 25)`。先比较第一项，`-95 < -90`，所以 B、C 都在 A 前；再比较 B 和 C 的第二项，`25 < 31`，所以最后是 C、B、A。

也别把 `reverse()` 当成降序排序。它只翻转当前排列，比如 `[2, 1, 3]` 翻转后是 `[3, 1, 2]`，并没有排好大小。想按大小降序，使用 `sort(reverse=True)` 或 `sorted(..., reverse=True)`。

4.6 筛掉多项时，不要一边遍历原列表一边删除

假设要删除所有 `1`，循环中调用 `remove()` 很容易漏项：

```python
items = [1, 1, 2]
for value in items:
    if value == 1:
        items.remove(value)
print(items)  # [1, 2]：第二个 1 被漏掉了
```

第一次删掉下标 0，原来下标 1 的那个 `1` 会移到下标 0；但循环下一次已经往下标 1 走了，于是直接读到 `2`。更容易写对的办法是新建结果列表，只把要保留的元素放进去：

```python
items = [1, 1, 2]
kept = []
for value in items:
    if value != 1:
        kept.append(value)
print(kept)  # [2]
```

对应的推导式是 `[value for value in items if value != 1]`。如果其他变量也引用原列表，而且必须让它们看到筛选后的内容，可以用 `items[:] = kept` 替换原列表的全部内容，而不只是写 `items = kept` 换掉当前名字的指向。

列表记忆口诀：`append` 整包放，`extend` 拆开放；`pop` 按位置删并带回结果，`remove` 按值只删第一个；`sort` 改自己，`sorted` 给新表。

小练习：从 `[3, 1, 2, 1]` 中删除第一个 `1`，再降序排列。预期结果是 `[3, 2, 1]`。

5）元组：固定的一组值，重点看逗号

5.1 单元素元组怎么写

元组是有序、不可变序列。单元素元组的关键是逗号，而不是小括号：

```python
not_a_tuple = (10)
one_item = (10,)
also_tuple = 10,

print(type(not_a_tuple))  # <class 'int'>
print(type(one_item))     # <class 'tuple'>
```

5.2 “元组不可变”，不等于里面的东西都不能变

元组支持下标、切片、`index()`、`count()` 和 `len()`。不能改的是“这个位置指向哪个对象”；如果指向的是列表，列表里面仍能增删。下面没有替换 `record[1]`，只是在那份列表里加了一个名字：

```python
record = ("team", ["alice"])
record[1].append("bob")
print(record)  # ('team', ['alice', 'bob'])
```

只有所有元素都可哈希的元组才能作为字典键或集合元素。包含列表的元组不可哈希。

5.3 拆包：把一组值分别取出来

坐标 `(10, 20)`、函数返回的最小值与最大值，都适合一次拆给几个变量。加星号的变量会接住中间剩下的元素：

```python
point = (10, 20)
x, y = point
print(x, y)

first, *middle, last = [1, 2, 3, 4, 5]
print(first, middle, last)  # 1 [2, 3, 4] 5
```

元组记忆口诀：单元素看逗号，不看括号；元组自己不能换，里面的可变对象仍能变。

6）字典：用键找值，不用记下标

6.1 键和值怎么放

用户的 `id`、`name`、`role` 用字典保存，读起来比“第 0 项、第 1 项”清楚。它很像 Java 的 Map。Python 3.7 及以后还保证按插入顺序遍历，但取业务字段时仍应使用键名，而不是依赖它排在第几个。

```python
user = {"id": 1, "name": "Ada"}
user["role"] = "admin"  # 新增
user["name"] = "Lin"    # 修改
```

键要能用于哈希查找，也就是“可哈希”。常用的字符串、数字，以及只含可哈希元素的元组都可以；列表、字典、普通集合不能直接当键。

6.2 查找：必须有用方括号，可以没有用 get

```python
user = {"name": "Ada", "nickname": None}
print(user["name"])              # Ada
print(user.get("missing"))        # None
print(user.get("missing", "N/A")) # N/A
```

`user["missing"]` 会抛 `KeyError`。`get()` 找不到时返回默认值，但要注意：当键存在且值就是 `None` 时，`get()` 同样返回 `None`。需要区分时使用 `key in mapping`。

默认值只在“键不存在”时生效，不会替换已经存在的 `None`、`0` 或空字符串；`get()` 也不会把默认值自动写回字典：

```python
user = {"nickname": None, "visits": 0}
print(user.get("nickname", "guest"))  # None：键存在
print(user.get("visits", 10))         # 0：键存在
print(user.get("role", "reader"))     # reader：键不存在
print("role" in user)                 # False：没有自动插入
```

所以“没填昵称”和“根本没传昵称字段”如果业务上不同，就先检查 `"nickname" in user`，再看对应的值。

6.3 增删改与合并

```python
config = {"timeout": 3, "debug": False}
config.update({"timeout": 5, "retries": 2})
print(config)

removed = config.pop("debug")
print(removed)  # False

del config["retries"]
config.clear()
```

Python 3.9 及以后可用 `|` 创建合并后的新字典，右侧同名键覆盖左侧：

```python
defaults = {"timeout": 3, "retries": 1}
custom = {"timeout": 10}
merged = defaults | custom
print(merged)  # {'timeout': 10, 'retries': 1}
```

6.4 遍历：只要键，还是键和值一起要

```python
scores = {"alice": 95, "bob": 88}

for key in scores:
    print(key)

for value in scores.values():
    print(value)

for key, value in scores.items():
    print(key, value)
```

`keys()`、`values()`、`items()` 不是把当前内容复制一份，而是给你一个能看到字典内容的“视图”。原字典变了，视图也跟着变。需要保存当时的结果，就用 `list()` 转成列表。

`items()` 每次给出一个 `(键, 值)` 元组，所以 `for key, value in scores.items()` 实际每次都在做一次拆包。把两种写法放在一起看：

```python
scores = {"alice": 95, "bob": 88}
for item in scores.items():
    key, value = item
    print(key, value)

# alice 95
# bob 88
```

动态视图和列表快照的区别，也可以直接打印出来：

```python
scores = {"alice": 95}
keys_view = scores.keys()
keys_snapshot = list(scores)
scores["bob"] = 88
print(list(keys_view))  # ['alice', 'bob']
print(keys_snapshot)   # ['alice']
```

这里的列表快照只保存当时的元素引用，不等于深拷贝。另一个边界是：遍历字典时不要同时给它增删键，否则可能抛 `RuntimeError` 或漏掉本来想处理的项。需要删除时，可以先收集要删的键，循环结束后再逐个删除。

6.5 分组追加：先准备列表，再放元素

往 `groups["backend"]` 里追加时，第一次可能还没有这个键。`setdefault()` 会在缺键时放入默认值，并返回对应的值；已有键时就直接返回旧值。分组代码多时，也可以用 `collections.defaultdict` 简化：

```python
groups: dict[str, list[int]] = {}
groups.setdefault("backend", []).append(1)
groups.setdefault("backend", []).append(2)
print(groups)  # {'backend': [1, 2]}
```

把第一行拆开：先查 `"backend"`，没找到，就放入一个空列表；`setdefault()` 返回的正是字典里那份列表，随后 `.append(1)` 修改它。第二次调用时键已经存在，返回旧列表 `[1]`，所以追加后变成 `[1, 2]`，不会重新清空。

用熟悉的普通分支展开，当前这个例子等价于：

```python
groups = {}
for member_id in [1, 2]:
    if "backend" not in groups:
        groups["backend"] = []
    groups["backend"].append(member_id)
    print(groups)

# {'backend': [1]}
# {'backend': [1, 2]}
```

不过 `setdefault()` 不会检查旧值的类型。如果字典里本来是 `{"backend": None}`，它会返回 `None`，后面的 `.append()` 就会报 `AttributeError`。它解决的是“缺键时初始化”，不是“自动修复不合适的旧值”。

字典记忆口诀：方括号是“必须有”，没有就报错；`get` 是“可以没有”，给默认值继续走；遍历键值对就用 `items()`。

小练习：把 `["a", "bb", "ccc"]` 转成 `{"a": 1, "bb": 2, "ccc": 3}`。预期可用一行字典推导式完成。

7）集合：去重、查成员、比较两组数据

7.1 添加和删除

只关心标签有没有重复、不关心“第几个标签”时，就适合用集合。相同元素只保留一份，可以增删，但不能用下标取值，也不要依赖打印出来的顺序。

空集合要写 `set()`，不能写 `{}`，因为 `{}` 已经表示空字典。集合元素和字典键一样，需要可哈希，所以字符串、数字可以直接放，列表不能直接放。

```python
tags = {"python", "backend", "python"}
print(len(tags))  # 2

tags.add("api")
tags.update(["async", "orm"])
tags.discard("missing")  # 不存在也不报错
```

`remove(value)` 在元素不存在时抛 `KeyError`，`discard(value)` 不抛异常。`pop()` 删除并返回某个任意元素，不是“最后一个”。

7.2 并集、交集和差集

拿权限举例：并集是“双方所有权限”，交集是“双方都有的权限”，差集是“我有而你没有的权限”，对称差集是“只属于其中一方的权限”。`<=` 则可以直接检查“需要的权限是不是全都有”：

```python
required = {"read", "write"}
owned = {"read", "write", "admin"}

print(required <= owned)          # True，子集
print(owned >= required)          # True，超集
print(required | {"audit"})      # 并集
print(owned & {"admin", "read"}) # 交集
print(owned - required)           # 差集 {'admin'}
print(owned ^ required)           # 对称差集 {'admin'}
```

上例里 `required` 完全包含在 `owned` 内，差集和对称差集刚好一样，容易误以为它们是同一种运算。换成两边各有独有元素，就能看出区别：

```python
left = {"read", "write"}
right = {"read", "audit"}
print(sorted(left | right))  # ['audit', 'read', 'write']
print(sorted(left & right))  # ['read']
print(sorted(left - right))  # ['write']
print(sorted(right - left))  # ['audit']
print(sorted(left ^ right))  # ['audit', 'write']
```

`left - right` 只看左边剩下什么，交换左右就会变；`left ^ right` 把两边各自独有的都留下。这里加 `sorted()` 只是为了输出顺序固定，运算本身返回的仍是集合。

若需要不可变集合，可使用 `frozenset`，它在元素可哈希时自身也可哈希，可作为字典键。

集合记忆口诀：集合没有下标；`add` 加一个，`update` 加一批；`discard` 找不到也安静，`remove` 找不到会报错。

8）切片：从哪里开始，到哪里停，每次走几步

8.1 基本写法与负步长

字符串、列表、元组都能切片。读 `[start:stop:step]` 时，按顺序念成“从 start 开始，在 stop 前停，每次走 step 步”。因此 `[1:4]` 取下标 `1、2、3`，不取 `4`，也就是常说的“包头不包尾”。

先不背所有缩写，三个位置分别看：

- `start`：尝试从哪个下标开始；越界时会调整边界，最终也可能没有元素可取。
- `stop`：在哪个边界之前停，这个位置不取。
- `step`：每次下标加多少；不写时是 `1`，不能是 `0`。

当步长为正时，省略起点表示从开头，省略终点表示走到末尾之后；当步长为负时，默认从末尾往前走，省略终点表示一直走过最前一项。因此 `[::-1]` 能完整反转，而不是只有“给步长写负数”这么简单。

```python
values = [0, 1, 2, 3, 4, 5]
print(values[1:4])    # [1, 2, 3]
print(values[:3])     # [0, 1, 2]
print(values[3:])     # [3, 4, 5]
print(values[::2])    # [0, 2, 4]
print(values[-2:])    # [4, 5]
print(values[::-1])   # [5, 4, 3, 2, 1, 0]
```

步长是负数，就从右往左走；只是方向变了，“不包含 stop”的规则没有变：

```python
text = "abcdef"
print(text[4:1:-1])  # edc
```

这里的下标依次是 `4 → 3 → 2`，对应 `e → d → c`；下一个下标是 `1`，碰到停止边界，不再取 `b`。如果改为 `text[1:4:-1]`，起点 1 已经在停止边界 4 的左边，不满足反向切片继续取值的条件，所以直接得到空字符串，不会自动帮你交换起终点。

对于边界都已经合法、无需换算负下标的例子，可以借普通循环理解取值过程：

```python
text = "abcdef"
characters = []
for index in range(4, 1, -1):
    characters.append(text[index])
    print(index, characters)
print("".join(characters))  # edc

# 4 ['e']
# 3 ['e', 'd']
# 2 ['e', 'd', 'c']
```

这个展开只帮助理解当前例子；不要把任意切片机械换成原始参数的 `range()`，因为切片还会换算负下标、截断越界边界。

容易误解的一点是，负步长下仍然不包含 `stop`。可用 `slice(start, stop, step)` 显式创建切片对象：

```python
part = slice(1, 5, 2)
print("abcdef"[part])  # bd
```

8.2 切片赋值：用一段新内容替换旧内容

读一个列表切片，会得到浅拷贝；给列表切片赋值，则是在改原列表。下面替换的是普通步长为 1 的区间，新旧两段长度可以不同：

```python
items = [0, 1, 2, 3]
items[1:3] = [8, 9, 10]
print(items)  # [0, 8, 9, 10, 3]
```

它先选中旧区间 `[1, 2]`，再整段换成 `[8, 9, 10]`，所以长度从 4 变成 5。普通连续切片还可以删除一段，或者在空区间处插入：

```python
items = [0, 1, 2, 3]
items[1:3] = []
print(items)        # [0, 3]
items[1:1] = [8, 9]
print(items)        # [0, 8, 9, 3]
```

但 `items[::2] = ...` 这种步长不为 1 的切片，是给隔开的位置逐个换值。右边必须提供同样数量的元素，不能多也不能少：

```python
items = [0, 1, 2, 3, 4]
items[::2] = [10, 20, 30]  # 选中下标 0、2、4，正好三个位置
print(items)              # [10, 1, 20, 3, 30]
try:
    items[::2] = [99]
except ValueError:
    print("replacement length mismatch")
```

8.3 空结果、越界与负下标，怎么提前判断

```python
values = [0, 1, 2, 3, 4, 5]
print(values[100:200])  # []：整个范围都在末尾之外
print(values[-100:3])   # [0, 1, 2]：过小的起点截到开头
print(values[4:1])      # []：步长默认向右，起点却已超过终点
print(values[5:-1:-1])  # []：-1 是最后一项的下标，也就是 5
print(values[5::-1])    # [5, 4, 3, 2, 1, 0]：省略终点才走完整段
try:
    print(values[::0])
except ValueError:
    print("slice step cannot be zero")
```

尤其记住最后两个反向切片的区别：省略 `stop` 不是写了一个字面上的 `-1`。明确写 `-1` 时，它代表最后一项；省略时，Python 根据向左的方向选择“走过开头”的默认边界。单独访问 `values[100]` 会报 `IndexError`，切片 `values[100:200]` 却是空列表，这是“取一个位置”和“取一个范围”的区别。

切片记忆口诀：起点算，终点不算，步长决定方向；`[::-1]` 从尾走到头。

小练习：从 `list(range(10))` 取出 `8、6、4、2`。预期切片是从下标 8 开始、向左每次走 2，并在下标 0 之前停止。

9）常用操作：长度、成员判断、遍历与转换

9.1 拼接、重复、长度和最大最小值

```python
print([1, 2] + [3, 4])  # [1, 2, 3, 4]
print(("a",) * 3)       # ('a', 'a', 'a')
print(len("python"))
print(max([3, 1, 5]))
print(min([3, 1, 5]))
```

9.2 in 到底在找什么

同样一个 `in`，放在字符串里是找子串，放在列表或元组里是找完整元素，放在字典里是找键。`not in` 就是把结果反过来：

```python
print("py" in "python")          # True，字符串按子串判断
print("aa" in ("a", "b"))       # False，元组按完整元素判断
print("name" in {"name": "Ada"}) # True，字典按键判断
print("write" not in {"read"})   # True，not in 表示“不属于”
```

列表和元组通常要一项项找，内容越多可能越慢；字典和集合依靠哈希查找，平均情况下查找时间不会随元素数量成比例增长。因此大量判断“某项在不在”时，集合通常更合适。

9.3 range 和 enumerate：生成序号，或给元素带上序号

`range()` 表示一段整数范围，不会一开始就建好完整列表，同样不包含终点：

```python
print(list(range(5)))          # [0, 1, 2, 3, 4]
print(list(range(2, 8, 2)))    # [2, 4, 6]
print(list(range(5, 0, -1)))   # [5, 4, 3, 2, 1]
```

只有一个参数 `range(5)` 时，这个 5 是终点，默认从 0 开始；两个参数是起点和终点；第三个才是步长。`range(5, 0)` 仍默认向右走，所以结果为空；要倒着走，必须明确写负步长。和切片一样，步长不能是 0。

如果只是同时拿到序号和内容，写 `for index, value in enumerate(items)` 就够了。只有确实需要自己控制下标，或借同一下标访问多个序列时，再考虑 `range(len(items))`。

`enumerate(..., start=1)` 只把显示的计数从 1 开始，不会跳过第一个元素，也不会改变列表的真实下标：

```python
names = ["Ada", "Lin"]
for number, name in enumerate(names, start=1):
    print(number, name)
print(names[0])  # Ada：实际下标仍然从 0 开始

# 1 Ada
# 2 Lin
```

9.4 容器转换与保序去重

```python
values = [3, 1, 3, 2]
print(tuple(values))          # (3, 1, 3, 2)
print(sorted(set(values)))    # [1, 2, 3]
print(list("abc"))           # ['a', 'b', 'c']
print(list(("a", "b")))      # ['a', 'b']
```

用集合去重会丢失原始顺序。需要保持首次出现顺序时，可借助字典键唯一且保序的性质：

```python
values = [3, 1, 3, 2, 1]
unique_in_order = list(dict.fromkeys(values))
print(unique_in_order)  # [3, 1, 2]
```

这行可以拆成两步。`dict.fromkeys(values)` 先得到 `{3: None, 1: None, 2: None}`：第一次见到 3、1、2 时各放一个键，后面重复的键不会再占一个位置。`list(字典)` 又只取键，所以最后是 `[3, 1, 2]`，保留的是第一次出现的顺序。

它要求元素能当字典键。字符串、整数没有问题；如果元素本身是列表，不能直接套这个写法。`fromkeys()` 的另一个坑是传入可变默认值：

```python
groups = dict.fromkeys(["a", "b"], [])
groups["a"].append(1)
print(groups)  # {'a': [1], 'b': [1]}

independent = {name: [] for name in ["a", "b"]}
independent["a"].append(1)
print(independent)  # {'a': [1], 'b': []}
```

前一种只创建了一份默认列表，两个键共用；后一种每次循环都新建 `[]`。这和二维列表乘法的问题是同一个原因，不需要当作两个孤立的坑来背。

10）zip：把几列数据按位置配成一组

10.1 一个人名配一个分数

姓名和分数分别在两个列表里，想把第一个姓名配第一个分数、第二个配第二个，就用 `zip()`。每一组得到一个元组，结果按需产生；这里用 `list()` 把它们全部展开来看：

```python
names = ["alice", "bob"]
scores = [95, 88]
pairs = list(zip(names, scores))
print(pairs)  # [('alice', 95), ('bob', 88)]
print(dict(zip(names, scores)))
```

如果先不使用 `zip()`，对这两份普通列表，可以把配对过程写成：

```python
names = ["alice", "bob"]
scores = [95, 88]
pairs = []
for index in range(min(len(names), len(scores))):
    pair = (names[index], scores[index])
    pairs.append(pair)
    print(pairs)

# [('alice', 95)]
# [('alice', 95), ('bob', 88)]
```

第一轮各取下标 0，第二轮各取下标 1，`min(...)` 表示只走到较短的那边。这个展开需要列表能取长度和下标；`zip()` 更通用，也能处理生成器等没有这些能力的输入。

还要留意“结果按需产生”意味着什么：保存下来的同一个 zip 对象，不会每次都自动从头开始。

```python
paired = zip(["alice", "bob"], [95, 88])
print(next(paired))  # ('alice', 95)：取走第一组
print(list(paired))  # [('bob', 88)]：只收集剩下的
print(list(paired))  # []：已经读完
```

需要多次使用全部配对时，一开始就用 `pairs = list(zip(...))` 保存结果列表，或者每次重新创建 zip 对象。

10.2 长度不一样时，默认只配到短的那一边

`zip()` 像拉链：某一边没有下一项，就结束；较长那一边剩下的元素不会自动出现在结果里：

```python
print(list(zip([1, 2, 3], ["a", "b"])))
```

预期输出为 `[(1, 'a'), (2, 'b')]`。

如果长度不一致代表数据错误，Python 3.10 及以上可使用 `strict=True`：

```python
try:
    list(zip([1, 2, 3], ["a", "b"], strict=True))
except ValueError as exc:
    print("length mismatch", exc)
```

这比默默截断更适合账务、批处理等要求严格对齐的数据。若业务要求补齐最长序列，可用 `itertools.zip_longest()`。

`strict=True` 不是创建 zip 对象那一刻就检查所有长度，而是在取数据时检查。前面能够成功配对的数据可能已经交出来了：

```python
paired = zip([1, 2], ["a"], strict=True)
print(next(paired))  # (1, 'a')：第一组能配对
try:
    next(paired)    # 继续取，才发现第二组少了一项
except ValueError:
    print("length mismatch")
```

因此，批处理中如果“长度不对就一条都不能写入”，不要一边循环 strict zip 一边执行不可撤销的写入。对于规模允许的数据，可以先完整收集、确认配对通过，再执行后续操作。

需要保留长的一侧，则明确指定补充值：

```python
from itertools import zip_longest

print(list(zip_longest([1, 2, 3], ["a", "b"], fillvalue=None)))
# [(1, 'a'), (2, 'b'), (3, None)]
print(list(zip([], [1, 2])))  # []：默认 zip 中任意一边为空就结束
```

`fillvalue` 不写时也是 `None`。它只是补上缺项，不会替你判断缺项是否合理；业务数据本来可能就是 `None` 时，还要区分“原值就是空”和“因为长度不足补的空”。

10.3 用 zip(*pairs) 把一组组数据重新拆成列

```python
pairs = [("alice", 95), ("bob", 88)]
names, scores = zip(*pairs)
print(names)   # ('alice', 'bob')
print(scores)  # (95, 88)
```

这不是 zip 的另一个特殊模式，而是两步普通操作：`*pairs` 先把两行展开，相当于调用 `zip(("alice", 95), ("bob", 88))`；zip 再按位置配对，先得到两行的第 0 项 `("alice", "bob")`，再得到第 1 项 `(95, 88)`。最后左边的 `names, scores` 把这两组结果接住。

如果 `pairs` 是空列表，zip 就没有任何一组能交出来，无法拆给两个变量：

```python
pairs = []
try:
    names, scores = zip(*pairs)
except ValueError:
    print("no rows to unpack")
```

确实允许没有数据时，可以先写 `if pairs:`，空的分支给 `names, scores` 都设为空元组，别假设拆列会自动产生两个空列。

`zip` 记忆口诀：像拉链，按位扣；默认看最短，严格对齐加 `strict=True`；前面加星号可以反向拆列。

11）推导式：把简单循环写得紧凑一点

11.1 列表推导式与筛选

“每个数求平方”和“只保留偶数的平方”，本来都可以用循环加 `append()`。规则简单时，推导式能把“取谁、怎么算、留不留”写在一行：

```python
squares = [number * number for number in range(6)]
even_squares = [number * number for number in range(6) if number % 2 == 0]

print(squares)       # [0, 1, 4, 9, 16, 25]
print(even_squares)  # [0, 4, 16]
```

先展开第二行，不追求短，看看执行顺序：

```python
even_squares = []
for number in range(6):
    if number % 2 == 0:
        square = number * number
        even_squares.append(square)
    print(number, even_squares)

# 0 [0]
# 1 [0]
# 2 [0, 4]
# 3 [0, 4]
# 4 [0, 4, 16]
# 5 [0, 4, 16]
```

真实处理顺序是：从 `range(6)` 取一个数 → 检查末尾的 `if` → 通过后才计算最前面的 `number * number` → 放进结果。不是先对所有数字求平方，再统一筛选。读推导式时先找 `for`，顺着 `if` 往下看，最后看开头要产出什么。

“先判断，再计算”还能避开不合法的运算：

```python
values = [2, 0, 4]
reciprocals = [1 / value for value in values if value != 0]
print(reciprocals)  # [0.5, 0.25]
print([x * 2 for x in []])  # []：输入为空，不执行转换表达式
```

这里 `0` 在除法发生前就被筛掉了；去掉末尾条件，运行到它时才会抛 `ZeroDivisionError`。

11.2 两种 if：一个决定留不留，一个决定变成什么

`for` 后面的 `if` 是筛选：不满足条件的元素不进入结果。前面的 `A if 条件 else B` 是逐项选结果：每个元素都会得到 A 或 B，不会因为分支而少一项。

```python
labels = ["even" if number % 2 == 0 else "odd" for number in range(5)]
print(labels)  # ['even', 'odd', 'even', 'odd', 'even']
```

这一种的普通循环长这样，每轮都追加一次，只是追加的内容不同：

```python
labels = []
for number in range(5):
    if number % 2 == 0:
        label = "even"
    else:
        label = "odd"
    labels.append(label)
print(labels)  # ['even', 'odd', 'even', 'odd', 'even']
```

所以 `[表达式 for ... if 条件]` 里的条件回答“要不要这项”；`[A if 条件 else B for ...]` 里的条件回答“这项变成 A 还是 B”。前一种可能减少项数，后一种对每个输入都给出一项结果。

11.3 多个 for：左边是外层，右边是内层

下面先固定一个 `x`，把所有 `y` 走完，再换下一个 `x`。读法和展开成嵌套循环一样：

```python
pairs = [(x, y) for x in range(2) for y in range(3)]
print(pairs)
```

预期输出为 `[(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]`。

把 `for` 按从左到右的顺序逐层展开：

```python
pairs = []
for x in range(2):
    for y in range(3):
        pairs.append((x, y))
    print(x, pairs)

# 0 [(0, 0), (0, 1), (0, 2)]
# 1 [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
```

因此双层 for 不是 zip。这里每个 x 都会配所有 y，共 `2 × 3 = 6` 项；zip 则只按相同位置配对，两个长度分别为 2 和 3 的输入默认只配出 2 项。

二维列表扁平化也是同样顺序：先拿到一行，再拿到该行每一个元素。空行没有元素，内层循环就执行 0 次：

```python
matrix = [[1, 2], [], [3]]
flat = []
for row in matrix:
    for item in row:
        flat.append(item)
print(flat)  # [1, 2, 3]
print([item for row in matrix for item in row])  # [1, 2, 3]
```

11.4 字典与集合推导式

想得到字典，就把最前面的结果写成 `键: 值`：

```python
names = ["alice", "bob"]
scores = [95, 88]
score_by_name = {name: score for name, score in zip(names, scores)}
passed = {name: score for name, score in score_by_name.items() if score >= 90}
print(passed)  # {'alice': 95}
```

第一段字典推导式相当于先建 `score_by_name = {}`，每取到 `(name, score)` 就执行 `score_by_name[name] = score`，中间先有 `{'alice': 95}`，再变成 `{'alice': 95, 'bob': 88}`。第二段再遍历键值对，只把分数至少 90 的项写入 `passed`。

若推导过程中出现重复键，后出现的值覆盖先前值。

```python
records = [("alice", 80), ("bob", 88), ("alice", 95)]
score_by_name = {}
for name, score in records:
    score_by_name[name] = score
    print(score_by_name)

# {'alice': 80}
# {'alice': 80, 'bob': 88}
# {'alice': 95, 'bob': 88}
```

写成 `{name: score for name, score in records}` 也是同样结果，不会自动替你给 alice 求和或取平均。多个同名记录都要留下时，应把值设计成列表，而不是让新值覆盖旧值。

集合推导式自动去重：

```python
remainders = {number % 3 for number in range(10)}
print(sorted(remainders))  # [0, 1, 2]
```

这相当于先建 `remainders = set()`，每轮计算 `number % 3` 后调用 `remainders.add(...)`。0、1、2 分别加入后，后面的余数重复出现，不会新增元素。因此推导式前面是表达式，但结果放进列表、字典还是集合，决定了它会不会保留重复项。

推导式适合一眼能看懂的转换。出现多层条件、异常处理、副作用或复杂业务规则时，普通循环更清楚。不要为了“Pythonic”把所有逻辑压成一行。

推导式记忆口诀：最前面写“要什么”，后面写“从哪来”；末尾 `if` 是筛掉，前面三元表达式是逐个替换。

12）赋值与拆包：一次接住多个值

12.1 交换变量与收集剩余元素

交换两个变量不必再准备临时变量。Python 先算好右边的值，再依次交给左边的名字，因此不会刚改了 `a` 就把原值弄丢：

```python
a = 10
b = 20
a, b = b, a
print(a, b)  # 20 10
```

星号拆包可收集剩余元素：

```python
head, *body, tail = range(6)
print(head)  # 0
print(body)  # [1, 2, 3, 4]
print(tail)  # 5
```

先把两端需要的元素留出来，剩下的都交给带星号的变量；它接到的是列表，即使来源是元组或 range。没有剩余元素时，也能接到空列表：

```python
first, *middle, last = [10, 20]
print(first, middle, last)  # 10 [] 20
try:
    first, last = [10, 20, 30]
except ValueError:
    print("too many values to unpack")
```

没有星号时，左右数量必须一致；带一个星号可以吸收多出的项，但普通变量需要的最少项数仍要满足。比如 `first, *middle, last = [10]` 仍然会失败，因为连首尾两个位置都不够。

12.2 拆字典时，默认拿到键

直接遍历或拆包字典，得到的都是键，不是值：

```python
record = {"name": "Ada", "role": "admin"}
first_key, second_key = record
print(first_key, second_key)  # name role
```

需要键和值时使用 items 方法，例如 `for key, value in record.items()`。

12.3 用星号把内容展开到新容器中

`[*left, *right]` 把两边元素逐项放进新列表；`{**base, **custom}` 把键值对放进新字典，同名键由后面的值覆盖。函数调用时也能用星号拆参数，下一篇会展开说明。

```python
left = [1, 2]
right = [3, 4]
merged = [*left, *right]

base = {"timeout": 3, "debug": False}
custom = {"timeout": 10}
config = {**base, **custom}

print(merged)
print(config)
```

13）遇到错误时，先看哪一步没满足要求

13.1 常见异常对应什么问题

| 操作 | 常见异常 | 更稳妥的选择 |
| --- | --- | --- |
| `items[index]` | `IndexError` | 先检查长度，或用迭代代替下标 |
| `mapping[key]` | `KeyError` | 可缺失时用 `get`，必须存在时保留异常 |
| `text.index(sub)` | `ValueError` | 可缺失时用 `find` 或 `in` |
| `items.remove(value)` | `ValueError` | 可缺失时先判断 `value in items` |
| `int(text)` | `ValueError` | 在输入边界捕获并返回明确错误 |
| 混合不可比较类型排序 | `TypeError` | 先规范数据或提供统一的 `key` |

不要用 `except Exception: pass` 把所有问题藏起来。用户可能输错的内容，在入口捕获并说明原因；程序内部本来就应该成立的条件出了问题，就让错误及时暴露，才能找到真正出错的位置。

13.2 和 Java 放在一起记，哪些相似，哪些别照搬

- Python 的 `list` 更接近动态数组，不等于 Java `LinkedList`。
- Python 的 `dict` 是核心语言结构，类似 `LinkedHashMap` 的保序哈希映射。
- Python 的 `set` 类似 `HashSet`，但集合运算符非常实用。
- `tuple` 不只是“不可变列表”，它常表达固定结构、返回值组合或可哈希复合键。
- Python 字符串不可变，与 Java `String` 相似；大量拼接优先使用 `join()`。
- Python 变量声明没有编译期类型约束，类型提示不会自动做运行时校验。
- 相等用 `==`，身份用 `is`；判断 `None` 使用 `is None`。
- 容器方法是否原地修改、是否返回新对象，必须逐个分清。

14）把知识点连起来：整理接口记录与动手验证

14.1 整理接口访问记录

下面这批记录要做三件事：筛出状态码小于 400 的记录、列出出现过的路径、计算各路径平均耗时。注意小于 400 也包含 3xx 重定向，不能一概叫“成功请求”。先看变量名猜每一步的结果，再对照列表、集合和字典各自负责什么。

```python
records = [
    {"path": "/users", "status": 200, "latency_ms": 18},
    {"path": "/orders", "status": 500, "latency_ms": 92},
    {"path": "/users", "status": 200, "latency_ms": 25},
    {"path": "/orders", "status": 200, "latency_ms": 40},
]

successful = [record for record in records if record["status"] < 400]
paths = {record["path"] for record in records}
latencies = {
    path: [record["latency_ms"] for record in records if record["path"] == path]
    for path in paths
}
averages = {
    path: sum(values) / len(values)
    for path, values in latencies.items()
}

print(len(successful))
print({path: round(value, 1) for path, value in averages.items()})
```

这段先按变量逐步追一次，别跳过中间两个字典：

- `successful` 保留第 1、3、4 条记录，所以长度是 3。它只用来做这个计数，不会自动改变后面遍历的 `records`。
- `paths` 去重后有 `/users` 和 `/orders` 两个路径。集合不保证输出顺序，但这里按路径取数据，先处理谁都不影响结果。
- 外层每拿到一个 `path`，内层推导式就重新检查全部记录。处理 `/users` 时收集 `[18, 25]`，处理 `/orders` 时收集 `[92, 40]`。
- `averages` 再拿到这些列表，分别计算 `(18 + 25) / 2 = 21.5` 和 `(92 + 40) / 2 = 66.0`。

所以第一行输出 `3`，第二行字典里是 `'/users': 21.5` 和 `'/orders': 66.0`，两个键打印的先后顺序不固定。注意：平均耗时目前统计的是全部记录，包含状态码 500 的那条。如果只想统计前面筛选出的记录，后续分组就应基于 `successful`，而不是继续用 `records`。

这段代码里，列表保留记录，集合去掉重复路径，字典把路径和统计结果对应起来。小数据这样写很清楚；记录很多时，每个路径都重新扫描一遍全部记录就不划算了，可以改为一次循环，用 `defaultdict(list)` 分组。先确认结果正确，再看数据量是否值得优化。

空输入也值得手动推一下：`records = []` 时没有路径可遍历，`averages` 会是空字典，根本不会进入除法，因此不会除以零。非空输入里的每个路径都来自记录本身，也至少对应一条耗时。

14.2 安全解析端口列表

输入字符串为 `"8080, 443, bad, 8080, 65536, 80"`。要求：

- 忽略无法转换为整数的项。
- 只保留 `1` 到 `65535`。
- 去重并升序输出。

预期输出：

```text
[80, 443, 8080]
```

参考思路：先 `split(",")`，逐项 `strip()`，在 `try/except ValueError` 中转换，使用集合去重，最后 `sorted()`。

每条输入会经过哪一步，可以先填这张表，再写循环：

| 当前片段 | 转整数后 | 接下来怎么处理 | 已保留端口，按大小展示 |
| --- | --- | --- | --- |
| `"8080"` | `8080` | 在范围内，加入集合 | `[8080]` |
| `" 443"` | `443` | 去掉空白后加入 | `[443, 8080]` |
| `" bad"` | 转换失败 | 捕获 ValueError，跳过本项 | `[443, 8080]` |
| `" 8080"` | `8080` | 集合里已有，不重复保留 | `[443, 8080]` |
| `" 65536"` | `65536` | 能转换，但不在允许范围，跳过 | `[443, 8080]` |
| `" 80"` | `80` | 在范围内，加入集合 | `[80, 443, 8080]` |

这里有两种不同的失败：`bad` 是根本不能转整数，`65536` 是类型没问题、范围不合要求。两层检查都需要，不能只写一个 `int()`。完成后再试空字符串、全是错误值、重复端口和边界 `0、1、65535、65536`，确认空输入返回空列表、两端只保留合法范围。

14.3 按多个条件排序

给定：

```python
employees = [
    {"name": "A", "score": 90, "age": 30},
    {"name": "B", "score": 95, "age": 35},
    {"name": "C", "score": 95, "age": 25},
]
```

要求先按分数降序，再按年龄升序，输出姓名。

预期输出：

```text
['C', 'B', 'A']
```

参考键：`lambda item: (-item["score"], item["age"])`。

14.4 严格合并两列数据

将姓名列表和分数列表合并成字典。长度不一致必须报错，不能静默截断。

预期行为：

```python
names = ["alice", "bob"]
scores = [95]
dict(zip(names, scores, strict=True))
```

会抛出 `ValueError`。

14.5 扁平化二维列表

将 `[[1, 2], [], [3, 4]]` 转换为 `[1, 2, 3, 4]`，分别使用普通循环和双层列表推导式实现。

推导式参考形式：

```python
[item for row in matrix for item in row]
```

14.6 保持顺序去重

将 `["api", "db", "api", "cache", "db"]` 转换为 `["api", "db", "cache"]`。不要使用会打乱顺序的普通集合输出。

预期输出：

```text
['api', 'db', 'cache']
```

15）合上笔记后，试着回答这些问题

不要求逐字复述。能举一个例子、预测输出，再自己写出来，就比只记得方法名更扎实。

- 能解释 `==` 与 `is` 的区别，并坚持用 `is None`。
- 能说清 `str`、`tuple` 不可变，`list`、`dict`、`set` 可变。
- 能区分 `append` 与 `extend`、`sort` 与 `sorted`、`remove` 与 `pop`。
- 能解释浅拷贝为什么仍会共享内层列表。
- 能正确写出切片 `[start:stop:step]`，知道 stop 不包含。
- 知道 `zip()` 默认按最短输入结束，并会在严格场景使用 `strict=True`。
- 能分别写列表、字典、集合推导式，也知道复杂逻辑应回到普通循环。
- 能预测 `in` 在字符串、元组、字典中的不同含义。
- 能避免依赖集合的输出顺序。
- 能运行 `examples/basics_lab.py` 并通过全部断言。
