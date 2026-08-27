Python 基础与容器

这份笔记面向已有 Java 后端经验的开发者，目标不是重复背语法，而是建立 Python 的对象模型、容器操作和惯用写法。示例均以 Python 3.11 及以上版本为准。

配套代码在 `examples/basics_lab.py`。在仓库根目录执行：

```powershell
python examples/basics_lab.py
```

建议先预测每段输出，再运行代码。看到结果后，可以暂时注释参考实现，自己重写一遍。

先用人话建立画面

- 变量像便利贴：它贴在对象上，不是装对象的固定类型盒子。
- 列表像可调整顺序的货架：能增、删、换位置。
- 元组像封好的清单：清单位置不能换，但清单里引用的可变物品仍可能变化。
- 字典像通讯录：用姓名这样的键，直接找到对应值。
- 集合像门禁名单：只关心“有没有”，不关心第几个。
- 切片像切蛋糕：从起点切到终点前一刀，所以“包头不包尾”。
- `zip` 像拉链：左右按位置扣在一起，默认短的一边结束，拉链就结束。

这一章的总口诀：字符串不可改，列表随手改；元组位置定，字典按键找；集合只去重，切片不含尾。

运行环境与交互方式

Python 源文件通常以 `.py` 结尾。下面三种方式最常用：

```powershell
python --version
python examples/basics_lab.py
python
```

最后一条命令会进入交互式解释器，适合快速验证一个表达式。退出时可输入 `exit()`。

与 Java 的第一组差异：

| Python | Java 对照 | 要点 |
| --- | --- | --- |
| 变量直接绑定对象 | 变量有编译期声明类型 | Python 变量名本身没有固定类型 |
| 缩进形成代码块 | 大括号形成代码块 | 通常使用 4 个空格，不能随意混用 Tab |
| `None` | `null` | 应使用 `is None` 判断 |
| `True`、`False` | `true`、`false` | Python 布尔值首字母大写 |
| `and`、`or`、`not` | `&&`、`||`、`!` | Python 逻辑运算会短路，并可能返回操作数本身 |
| `//` | 整数除法 | Python 的 `//` 是向下取整，不是向零截断 |

变量、类型与对象

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

Python 变量保存的是对象引用，可以理解为“名字指向对象”，但不要把它简单等同于 Java 的所有引用语义。

```python
a = [1, 2]
b = a
print(id(a) == id(b))  # True

b.append(3)
print(a)               # [1, 2, 3]
```

`id()` 可帮助观察两个名字是否指向同一个对象。`is` 比较身份，`==` 比较值：

```python
x = [1, 2]
y = [1, 2]

print(x == y)  # True，内容相同
print(x is y)  # False，不是同一个列表对象
print(x is None)  # False
```

不要用 `is` 比较普通数字或字符串。某些小整数、短字符串可能被解释器复用，这属于实现细节，不能作为业务逻辑依据。

可变与不可变

理解可变性可以解释大量 Python 行为：

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

这是一个常见坑：多数原地修改列表的方法返回 `None`。不要写 `numbers = numbers.append(3)`，否则 `numbers` 会变成 `None`。

输入、输出与类型转换

`input()` 无论用户输入什么都返回字符串，因此参与数值运算前必须转换。

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

常见转换包括 `int("42")`、`float("3.14")`、`str(42)`、`bool(value)`。需要注意 `bool("False")` 是 `True`，因为任何非空字符串都为真。解析文本布尔值时要显式判断：

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

字符串格式化

旧式 `%s` 格式仍能见到：

```python
name = "Lin"
score = 95.678
print("name=%s, score=%.2f" % (name, score))
```

新代码优先使用 f-string：

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

真值与短路求值

以下值在条件判断中为假：`None`、`False`、数值零、空字符串、空列表、空元组、空字典和空集合。其他对象通常为真。

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

这适合简单默认值，但如果 `0`、空字符串是合法值，就不要用 `value or default` 替代精确的 `None` 判断。

字符串

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

查找方法

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

`find()` 返回的 `-1` 也恰好是合法负下标，所以不要在未判断时直接拿它取字符。

拆分、替换与拼接

```python
raw = "java,python,go"
parts = raw.split(",", maxsplit=1)
print(parts)  # ['java', 'python,go']

text = "one one one"
print(text.replace("one", "1", 2))  # 1 1 one

words = ["clean", "small", "functions"]
print(" ".join(words))  # clean small functions
```

`split()` 会丢掉分隔符。`join()` 是分隔字符串的方法，而不是列表的方法，这一点与 Java 的 `String.join()` 方向相近。待拼接元素必须都是字符串：

```python
numbers = [1, 2, 3]
print(",".join(map(str, numbers)))  # 1,2,3
```

大小写、清理与对齐

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

`strip(chars)` 的参数是“要从两端移除的字符集合”，不是完整前后缀：

```python
print("abbaXabba".strip("ab"))  # X
```

若要删除固定前后缀，Python 3.9 及以上可用 `removeprefix()` 和 `removesuffix()`：

```python
print("Bearer token".removeprefix("Bearer "))  # token
print("report.csv".removesuffix(".csv"))       # report
```

判断方法

```python
print("python.py".startswith("py"))     # True
print("python.py".endswith((".py", ".pyi")))  # True
print("Python".isalpha())                # True
print("123".isdigit())                   # True
print("abc123".isalnum())                # True
print(" \t\n".isspace())                 # True
```

实际后端代码里，用户输入校验通常不能只靠这些方法。例如 `"²".isdigit()` 也可能为真，而 `int("²")` 不一定接受。需要严格的 ASCII 数字时可组合范围判断或正则表达式。

字符串常用方法速查

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

列表

列表是有序、可变容器，可以存放不同类型。不过在真实项目中，一个列表通常保存语义相同的元素，更利于类型提示和维护。

```python
users = ["alice", "bob"]
mixed = [1, "two", True, None]
```

增加元素

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

删除元素

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

修改、查找与遍历

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

列表复制与嵌套陷阱

`copy()` 或 `[:]` 只做浅拷贝。外层是新对象，内层对象仍共享：

```python
original = [[1], [2]]
shallow = original.copy()
shallow[0].append(99)
print(original)  # [[1, 99], [2]]
```

完全独立复制嵌套结构可使用标准库 `copy.deepcopy()`：

```python
from copy import deepcopy

original = [[1], [2]]
independent = deepcopy(original)
independent[0].append(99)
print(original)  # [[1], [2]]
```

另一个经典坑是用乘法创建嵌套列表：

```python
wrong = [[0] * 3] * 2
wrong[0][0] = 9
print(wrong)  # [[9, 0, 0], [9, 0, 0]]

right = [[0] * 3 for _ in range(2)]
right[0][0] = 9
print(right)  # [[9, 0, 0], [0, 0, 0]]
```

排序与反转

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

排序是稳定的，相同键值的元素保持原相对顺序：

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

元组

元组是有序、不可变序列。单元素元组的关键是逗号，而不是小括号：

```python
not_a_tuple = (10)
one_item = (10,)
also_tuple = 10,

print(type(not_a_tuple))  # <class 'int'>
print(type(one_item))     # <class 'tuple'>
```

元组支持下标、切片、`index()`、`count()` 和 `len()`。它不可替换元素，但若元素本身是可变对象，该对象仍能修改：

```python
record = ("team", ["alice"])
record[1].append("bob")
print(record)  # ('team', ['alice', 'bob'])
```

只有所有元素都可哈希的元组才能作为字典键或集合元素。包含列表的元组不可哈希。

元组常用于返回多个值和结构化拆包：

```python
point = (10, 20)
x, y = point
print(x, y)

first, *middle, last = [1, 2, 3, 4, 5]
print(first, middle, last)  # 1 [2, 3, 4] 5
```

元组记忆口诀：单元素看逗号，不看括号；元组自己不能换，里面的可变对象仍能变。

字典

字典保存键值映射。Python 3.7 及以后语言层面保证迭代顺序为插入顺序，但应按键访问数据，不要把业务正确性建立在“第几个键”上。

```python
user = {"id": 1, "name": "Ada"}
user["role"] = "admin"  # 新增
user["name"] = "Lin"    # 修改
```

键必须可哈希，常见键类型是字符串、数字或只包含可哈希元素的元组。列表、字典、集合不能直接作为键。

查找时，方括号和 `get()` 的语义不同：

```python
user = {"name": "Ada", "nickname": None}
print(user["name"])              # Ada
print(user.get("missing"))        # None
print(user.get("missing", "N/A")) # N/A
```

`user["missing"]` 会抛 `KeyError`。`get()` 找不到时返回默认值，但要注意：当键存在且值就是 `None` 时，`get()` 同样返回 `None`。需要区分时使用 `key in mapping`。

增删改与合并：

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

遍历字典：

```python
scores = {"alice": 95, "bob": 88}

for key in scores:
    print(key)

for value in scores.values():
    print(value)

for key, value in scores.items():
    print(key, value)
```

`keys()`、`values()`、`items()` 返回动态视图，不是固定快照。字典改变后，视图也会反映变化。如果需要快照，显式转换为 `list()`。

`setdefault()` 可在键缺失时写入默认值，但聚合场景更推荐 `collections.defaultdict`：

```python
groups: dict[str, list[int]] = {}
groups.setdefault("backend", []).append(1)
groups.setdefault("backend", []).append(2)
print(groups)  # {'backend': [1, 2]}
```

字典记忆口诀：方括号是“必须有”，没有就报错；`get` 是“可以没有”，给默认值继续走；遍历键值对就用 `items()`。

小练习：把 `["a", "bb", "ccc"]` 转成 `{"a": 1, "bb": 2, "ccc": 3}`。预期可用一行字典推导式完成。

集合

集合是无重复元素的可变容器，不支持下标。输出顺序不应依赖。

```python
tags = {"python", "backend", "python"}
print(len(tags))  # 2

tags.add("api")
tags.update(["async", "orm"])
tags.discard("missing")  # 不存在也不报错
```

`remove(value)` 在元素不存在时抛 `KeyError`，`discard(value)` 不抛异常。`pop()` 删除并返回某个任意元素，不是“最后一个”。

集合运算很适合权限、标签和去重：

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

切片

字符串、列表、元组都支持 `[start:stop:step]`。规则是包头不包尾：包含 `start`，不包含 `stop`。

```python
values = [0, 1, 2, 3, 4, 5]
print(values[1:4])    # [1, 2, 3]
print(values[:3])     # [0, 1, 2]
print(values[3:])     # [3, 4, 5]
print(values[::2])    # [0, 2, 4]
print(values[-2:])    # [4, 5]
print(values[::-1])   # [5, 4, 3, 2, 1, 0]
```

步长为负时方向反转：

```python
text = "abcdef"
print(text[4:1:-1])  # edc
```

容易误解的一点是，负步长下仍然不包含 `stop`。可用 `slice(start, stop, step)` 显式创建切片对象：

```python
part = slice(1, 5, 2)
print("abcdef"[part])  # bd
```

列表切片通常创建浅拷贝。列表还支持切片赋值，替换区间长度不必相同：

```python
items = [0, 1, 2, 3]
items[1:3] = [8, 9, 10]
print(items)  # [0, 8, 9, 10, 3]
```

切片记忆口诀：起点算，终点不算，步长决定方向；`[::-1]` 从尾走到头。

小练习：从 `list(range(10))` 取出 `8、6、4、2`。预期切片是从下标 8 开始、向左每次走 2，并在下标 0 之前停止。

公共序列操作

```python
print([1, 2] + [3, 4])  # [1, 2, 3, 4]
print(("a",) * 3)       # ('a', 'a', 'a')
print(len("python"))
print(max([3, 1, 5]))
print(min([3, 1, 5]))
```

`in` 的含义由容器决定：

```python
print("py" in "python")          # True，字符串按子串判断
print("aa" in ("a", "b"))       # False，元组按完整元素判断
print("name" in {"name": "Ada"}) # True，字典按键判断
print("write" not in {"read"})   # True，not in 表示“不属于”
```

通常性能上，列表或元组的成员判断是线性查找，字典和集合的平均成员判断接近常数时间。

`range()` 惰性表示整数序列，不包含终点：

```python
print(list(range(5)))          # [0, 1, 2, 3, 4]
print(list(range(2, 8, 2)))    # [2, 4, 6]
print(list(range(5, 0, -1)))   # [5, 4, 3, 2, 1]
```

需要索引和值时使用 `enumerate()`，不要模仿 Java 写 `for i in range(len(items))`，除非确实需要用下标访问多个序列。

容器转换

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

zip 并行打包

`zip()` 将多个可迭代对象按位置打包为元组，返回惰性迭代器：

```python
names = ["alice", "bob"]
scores = [95, 88]
pairs = list(zip(names, scores))
print(pairs)  # [('alice', 95), ('bob', 88)]
print(dict(zip(names, scores)))
```

默认情况下，长度不一致时以最短输入为准，这就是“木桶效应”：

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

反向解包也很常用：

```python
pairs = [("alice", 95), ("bob", 88)]
names, scores = zip(*pairs)
print(names)   # ('alice', 'bob')
print(scores)  # (95, 88)
```

`zip` 记忆口诀：像拉链，按位扣；默认看最短，严格对齐加 `strict=True`；前面加星号可以反向拆列。

推导式

列表推导式可将映射和筛选写在一处：

```python
squares = [number * number for number in range(6)]
even_squares = [number * number for number in range(6) if number % 2 == 0]

print(squares)       # [0, 1, 4, 9, 16, 25]
print(even_squares)  # [0, 4, 16]
```

带 `if` 的筛选放在 `for` 后面，会减少结果数量。三元替换放在表达式位置，不减少数量：

```python
labels = ["even" if number % 2 == 0 else "odd" for number in range(5)]
print(labels)  # ['even', 'odd', 'even', 'odd', 'even']
```

多个 `for` 从左到右理解，等价于嵌套循环：

```python
pairs = [(x, y) for x in range(2) for y in range(3)]
print(pairs)
```

预期输出为 `[(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]`。

字典推导式：

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

赋值与拆包

Python 支持同时赋值，右侧先整体求值，再绑定左侧，因此交换无需临时变量：

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

直接迭代或拆包字典时，得到的是键，不是值：

```python
record = {"name": "Ada", "role": "admin"}
first_key, second_key = record
print(first_key, second_key)  # name role
```

需要键和值时使用 items 方法，例如 `for key, value in record.items()`。

在调用和容器字面量中也可拆包：

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

常见异常与防御性写法

| 操作 | 常见异常 | 更稳妥的选择 |
| --- | --- | --- |
| `items[index]` | `IndexError` | 先检查长度，或用迭代代替下标 |
| `mapping[key]` | `KeyError` | 可缺失时用 `get`，必须存在时保留异常 |
| `text.index(sub)` | `ValueError` | 可缺失时用 `find` 或 `in` |
| `items.remove(value)` | `ValueError` | 可缺失时先判断 `value in items` |
| `int(text)` | `ValueError` | 在输入边界捕获并返回明确错误 |
| 混合不可比较类型排序 | `TypeError` | 先规范数据或提供统一的 `key` |

不要用宽泛的 `except Exception: pass` 吞掉错误。对输入边界做转换和校验，对内部不变量让异常尽早暴露。

Java 后端迁移提示

- Python 的 `list` 更接近动态数组，不等于 Java `LinkedList`。
- Python 的 `dict` 是核心语言结构，类似 `LinkedHashMap` 的保序哈希映射。
- Python 的 `set` 类似 `HashSet`，但集合运算符非常实用。
- `tuple` 不只是“不可变列表”，它常表达固定结构、返回值组合或可哈希复合键。
- Python 字符串不可变，与 Java `String` 相似；大量拼接优先使用 `join()`。
- Python 变量声明没有编译期类型约束，类型提示不会自动做运行时校验。
- 相等用 `==`，身份用 `is`；判断 `None` 使用 `is None`。
- 容器方法是否原地修改、是否返回新对象，必须逐个分清。

综合示例：整理接口访问记录

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

这段代码同时使用了列表、集合、字典和推导式。数据量大时不应为每个路径反复扫描全部记录，可在一次循环中使用 `defaultdict(list)` 聚合；先写正确，再根据规模优化。

练习

练习一：安全解析端口列表

输入字符串为 `"8080, 443, bad, 8080, 65536, 80"`。要求：

- 忽略无法转换为整数的项。
- 只保留 `1` 到 `65535`。
- 去重并升序输出。

预期输出：

```text
[80, 443, 8080]
```

参考思路：先 `split(",")`，逐项 `strip()`，在 `try/except ValueError` 中转换，使用集合去重，最后 `sorted()`。

练习二：按多个条件排序

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

练习三：严格合并两列数据

将姓名列表和分数列表合并成字典。长度不一致必须报错，不能静默截断。

预期行为：

```python
names = ["alice", "bob"]
scores = [95]
dict(zip(names, scores, strict=True))
```

会抛出 `ValueError`。

练习四：扁平化二维列表

将 `[[1, 2], [], [3, 4]]` 转换为 `[1, 2, 3, 4]`，分别使用普通循环和双层列表推导式实现。

推导式参考形式：

```python
[item for row in matrix for item in row]
```

练习五：保持顺序去重

将 `["api", "db", "api", "cache", "db"]` 转换为 `["api", "db", "cache"]`。不要使用会打乱顺序的普通集合输出。

预期输出：

```text
['api', 'db', 'cache']
```

自检清单

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
