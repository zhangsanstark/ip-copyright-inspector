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

6.5 分组追加：先准备列表，再放元素

往 `groups["backend"]` 里追加时，第一次可能还没有这个键。`setdefault()` 会在缺键时放入默认值，并返回对应的值；已有键时就直接返回旧值。分组代码多时，也可以用 `collections.defaultdict` 简化：

```python
groups: dict[str, list[int]] = {}
groups.setdefault("backend", []).append(1)
groups.setdefault("backend", []).append(2)
print(groups)  # {'backend': [1, 2]}
```

字典记忆口诀：方括号是“必须有”，没有就报错；`get` 是“可以没有”，给默认值继续走；遍历键值对就用 `items()`。

小练习：把 `["a", "bb", "ccc"]` 转成 `{"a": 1, "bb": 2, "ccc": 3}`。预期可用一行字典推导式完成。

7）集合：去重、查成员、比较两组数据

7.1 添加和删除

只关心标签有没有重复、不关心“第几个标签”时，就适合用集合。相同元素只保留一份，可以增删，但不能用下标取值，也不要依赖打印出来的顺序。

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

若需要不可变集合，可使用 `frozenset`，它在元素可哈希时自身也可哈希，可作为字典键。

集合记忆口诀：集合没有下标；`add` 加一个，`update` 加一批；`discard` 找不到也安静，`remove` 找不到会报错。

8）切片：从哪里开始，到哪里停，每次走几步

8.1 基本写法与负步长

字符串、列表、元组都能切片。读 `[start:stop:step]` 时，按顺序念成“从 start 开始，在 stop 前停，每次走 step 步”。因此 `[1:4]` 取下标 `1、2、3`，不取 `4`，也就是常说的“包头不包尾”。

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

如果只是同时拿到序号和内容，写 `for index, value in enumerate(items)` 就够了。只有确实需要自己控制下标，或借同一下标访问多个序列时，再考虑 `range(len(items))`。

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

10.3 用 zip(*pairs) 把一组组数据重新拆成列

```python
pairs = [("alice", 95), ("bob", 88)]
names, scores = zip(*pairs)
print(names)   # ('alice', 'bob')
print(scores)  # (95, 88)
```

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

11.2 两种 if：一个决定留不留，一个决定变成什么

`for` 后面的 `if` 是筛选：不满足条件的元素不进入结果。前面的 `A if 条件 else B` 是逐项选结果：每个元素都会得到 A 或 B，不会因为分支而少一项。

```python
labels = ["even" if number % 2 == 0 else "odd" for number in range(5)]
print(labels)  # ['even', 'odd', 'even', 'odd', 'even']
```

11.3 多个 for：左边是外层，右边是内层

下面先固定一个 `x`，把所有 `y` 走完，再换下一个 `x`。读法和展开成嵌套循环一样：

```python
pairs = [(x, y) for x in range(2) for y in range(3)]
print(pairs)
```

预期输出为 `[(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]`。

11.4 字典与集合推导式

想得到字典，就把最前面的结果写成 `键: 值`：

```python
names = ["alice", "bob"]
scores = [95, 88]
score_by_name = {name: score for name, score in zip(names, scores)}
passed = {name: score for name, score in score_by_name.items() if score >= 90}
print(passed)  # {'alice': 95}
```

若推导过程中出现重复键，后出现的值覆盖先前值。

集合推导式自动去重：

```python
remainders = {number % 3 for number in range(10)}
print(sorted(remainders))  # [0, 1, 2]
```

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

这段代码里，列表保留记录，集合去掉重复路径，字典把路径和统计结果对应起来。小数据这样写很清楚；记录很多时，每个路径都重新扫描一遍全部记录就不划算了，可以改为一次循环，用 `defaultdict(list)` 分组。先确认结果正确，再看数据量是否值得优化。

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
