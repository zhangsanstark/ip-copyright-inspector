02 · 字符串方法：从参数到处理结果

处理一行日志、一个文件名或一份用户输入，通常离不开查找、拆分、清理、判断和拼接。这里把原先速查表里的方法真正拆开，不只列名字。每组都说明输入参数、返回结果、找不到时怎么办，以及原字符串有没有变化。

在仓库根目录运行 `python scripts/check_handbook_examples.py --chapter 02 --show-output`。本章所有完整 Python 块都能独立执行，assert 会核对示例中的结论。

---

1）先弄清字符串是什么

1.1 引号只负责界定内容

单引号和双引号没有“字符类型”和“字符串类型”的区别，都创建 str。三引号允许直接写多行。反斜杠可以引入转义，例如换行 `\n` 和制表符 `\t`；原始字符串前缀 r 会减少反斜杠转义，但并不是任意字符串都能无条件改成原始字符串。

```python
# runnable: hb02_literals
single = 'hello'
double = "hello"
multiline = "first\nsecond"
raw = r"first\nsecond"
assert single == double
assert multiline.splitlines() == ["first", "second"]
assert raw == "first\\nsecond"
assert "\n" not in raw
print(repr(multiline), repr(raw))
```

repr 适合看清不可见字符，print 则按显示规则处理换行。字符串内已经出现反斜杠还是实际换行，看到报错路径时要先分清。

1.2 索引按字符位置，str 不是字节数组

```python
# runnable: hb02_unicode_positions
text = "A中B"
assert len(text) == 3
assert text[1] == "中"
assert text[-1] == "B"
assert len(text.encode("utf-8")) == 5
combined = "e\u0301"
assert len(combined) == 2
assert combined != "é"
print(text, len(text), len(text.encode("utf-8")))  # A中B 3 5
```

Python str 按 Unicode 码点组成序列，UTF-8 字节长度是另一个概念。肉眼像一个字的组合形式也可能包含多个码点，因此 len 不一定是屏幕上“看起来几个字”。本章的下标示例使用简单字符，不能直接拿来计算终端显示宽度。

1.3 方法返回处理结果，不修改原字符串

```python
# runnable: hb02_immutable
original = "  pyThon  "
cleaned = original.strip()
upper = cleaned.upper()
assert original == "  pyThon  "
assert cleaned == "pyThon"
assert upper == "PYTHON"
print(repr(original), repr(cleaned), upper)
try:
    original[0] = "x"
except TypeError:
    pass
else:
    raise AssertionError("str cannot assign an item")
```

说“返回新字符串”主要强调得到一个结果值、原值不变；没有变化时，解释器可能复用对象，不应通过 is 验证它一定重新分配了内存。

---

2）find、rfind、index、rindex：找到位置

2.1 共同参数 sub、start、end

写法是 `text.find(sub, start, end)`，后两个参数可省略。sub 是要找的子串；start 是起始位置；end 是不包含的结束边界。返回的下标相对于完整原字符串，不是截取区域从 0 重新编号。

```python
# runnable: hb02_find_range
text = "banana"
assert text.find("na") == 2
assert text.rfind("na") == 4
assert text.find("na", 3) == 4
assert text.find("na", 0, 4) == 2
assert text.find("na", 0, 3) == -1
print(text.find("na"), text.rfind("na"))  # 2 4
```

`find("na", 0, 3)` 只检查边界前的区域 `"ban"`，没有完整的 `"na"`，所以找不到。rfind 是找最右边那个匹配，返回的仍是正常的正向下标，不是负数下标。

2.2 找不到，返回 -1 还是抛异常

find 和 rfind 找不到返回 -1；index 和 rindex 找不到抛 ValueError。已找到时，两组对应方法给出的下标一样。

```python
# runnable: hb02_search_missing
text = "banana"
assert text.index("na") == 2
assert text.rindex("na") == 4
assert text.find("missing") == -1
assert text.rfind("missing") == -1
for method in [text.index, text.rindex]:
    try:
        method("missing")
    except ValueError:
        pass
    else:
        raise AssertionError("missing text must raise")
position = text.find("missing")
if position != -1:
    found_character = text[position]
else:
    found_character = None
assert found_character is None
print(position)  # -1
```

-1 恰好也能作为“最后一个字符”的下标，所以 `text[text.find("missing")]` 可能不报错，却取了完全无关的字符。只关心存在不存在时，直接写 `"na" in text` 更合适。

2.3 空子串不等于没匹配

```python
# runnable: hb02_empty_search
assert "abc".find("") == 0
assert "abc".rfind("") == 3
assert "".find("") == 0
assert "".find("a") == -1
assert "" in "abc"
print("abc".find(""), "abc".rfind(""))  # 0 3
```

空子串可以出现在字符之间和两端；如果业务不接受空搜索词，要提前校验，而不能指望 find 把它当成“找不到”。

---

3）count：统计次数，但不统计重叠匹配

`text.count(sub, start, end)` 的范围参数与查找相似，返回整数，找不到返回 0。每匹配完一次，再继续找后面的部分，因此不会把重叠位置重复算入。

```python
# runnable: hb02_count
assert "banana".count("na") == 2
assert "banana".count("xy") == 0
assert "aaaa".count("aa") == 2
assert "aaaa".count("aa", 1) == 1
assert "abc".count("") == 4
assert "".count("") == 1
print("aaaa".count("aa"))  # 2，不是 3
```

`"aaaa"` 中第一对占下标 0、1，第二对占 2、3；中间下标 1、2 的重叠组合不单独计入。空子串的计数则是长度加一，对应所有缝隙。

---

4）replace：替换的是文本，不是正则表达式

写法 `text.replace(old, new, count)`。old、new 是字符串；count 可省略，省略时替换所有匹配，传 0 则一次不换。Python 3.11 中将第三个参数按位置传入即可。

```python
# runnable: hb02_replace
text = "one one one"
assert text.replace("one", "1", 2) == "1 1 one"
assert text.replace("one", "1") == "1 1 1"
assert text.replace("one", "1", 0) == text
assert text.replace("missing", "x") == text
assert "a.b".replace(".", "-") == "a-b"
assert "abc".replace("", "-") == "-a-b-c-"
assert text == "one one one"
print(text.replace("one", "1", 2))
```

过程是找到第一个 one，换成 1；找到第二个，再换；已经到 count=2，就保留余下原文。`"."` 在这里就是普通句点，不代表“任意字符”；需要模式匹配才考虑正则工具。

想移除内容，可以把 new 写成空字符串。old 为空时则会在各字符间隙插入 new，不要把空旧值误当作无效操作。

---

5）split、rsplit：拆成列表

5.1 指定分隔符时，空项会留下

`split(sep=None, maxsplit=-1)` 返回字符串列表。明确给 sep 时，按这个完整分隔串切分；maxsplit 是最多切几刀，不是最多得到几项。sep 可以有多个字符，但不能是空字符串。

```python
# runnable: hb02_split_explicit
text = "a,,b,"
assert text.split(",") == ["a", "", "b", ""]
assert text.split(",", 1) == ["a", ",b,"]
assert text.split(",", 0) == [text]
assert "a::b::c".split("::") == ["a", "b", "c"]
assert "abc".split(",") == ["abc"]
assert "".split(",") == [""]
try:
    text.split("")
except ValueError:
    pass
else:
    raise AssertionError("empty separator")
print(text.split(","))
```

连续两个逗号之间没有文本，也是一项空字符串；末尾逗号后同样留下一项。解析 CSV 时还可能有带引号的逗号，不能靠 split 就处理完整 CSV 语法，那种情况使用 csv 模块。

5.2 不指定 sep 时，按连续空白拆分

```python
# runnable: hb02_split_whitespace
text = "  a  b\t c\n"
assert text.split() == ["a", "b", "c"]
assert "".split() == []
assert "   ".split() == []
assert " a  b ".split(" ") == ["", "a", "", "b", ""]
assert "  a b ".split(None, 0) == ["a b "]
print(text.split())  # ['a', 'b', 'c']
```

split() 会把一串连续空白当作分隔，并忽略两端空白；split(" ") 只认普通空格，而且保留空项。二者不能随便互换。`split(None, 0)` 是特殊边界：不继续切分，只跳过开头空白，剩余尾部仍保留。

5.3 rsplit：从右边数切分次数

```python
# runnable: hb02_rsplit
text = "name=value=tail"
assert text.split("=", 1) == ["name", "value=tail"]
assert text.rsplit("=", 1) == ["name=value", "tail"]
assert text.rsplit("=") == ["name", "value", "tail"]
assert text.rsplit("missing", 1) == [text]
print(text.rsplit("=", 1))
```

rsplit 不是把结果列表反转。它仍按原顺序返回，只是在次数有限时，优先使用最右边的分隔符。拆最后一段后缀或最后一个字段时尤其好用。

---

6）splitlines、partition、rpartition：不是所有拆分都用 split

6.1 splitlines 识别行边界

`splitlines(keepends=False)` 按行分隔符拆分。默认不保留换行，keepends=True 则把各行结尾也留下；可以处理 `\n`、`\r\n` 等行边界。

```python
# runnable: hb02_splitlines
text = "first\r\nsecond\n"
assert text.splitlines() == ["first", "second"]
assert text.splitlines(True) == ["first\r\n", "second\n"]
assert "".splitlines() == []
assert "a\n".splitlines() == ["a"]
assert "a\n".split("\n") == ["a", ""]
assert "a\n\nb".splitlines() == ["a", "", "b"]
print(text.splitlines())
```

末尾一个换行不额外制造空行，但两个行边界之间确实有一行空内容时，会保留那一行。它是处理多行文本的工具，不等于所有环境里都只按单一字符 `\n` 切。

6.2 partition 固定返回三项

`text.partition(sep)` 只围绕第一次出现的 sep 拆成 `(前面, 分隔符, 后面)`；rpartition 则找最后一次。两者都保留分隔符本身，返回的是三元素元组，不是列表。

```python
# runnable: hb02_partition
assert "key=a=b".partition("=") == ("key", "=", "a=b")
assert "key=a=b".rpartition("=") == ("key=a", "=", "b")
assert "key".partition("=") == ("key", "", "")
assert "key".rpartition("=") == ("", "", "key")
assert "".partition("=") == ("", "", "")
for method in ["abc".partition, "abc".rpartition]:
    try:
        method("")
    except ValueError:
        pass
    else:
        raise AssertionError("empty separator")
key, separator, value = "mode=fast".partition("=")
assert separator == "=" and key == "mode" and value == "fast"
print(key, value)  # mode fast
```

没找到时两者放原文的位置不同，但中间分隔符都为空。解析 `key=value` 时可以检查 separator，而不用先查找下标、再手动写两段切片。value 自己为空也不代表没找到分隔符，比如 `"key="`。

---

7）join：用分隔符连接字符串元素

7.1 是分隔符调用 join，不是列表调用

`separator.join(iterable)` 接收可迭代对象，要求其中每个元素都是字符串。列表、元组、生成器都可以；返回单个字符串。没有元素就返回空字符串，只有一个元素就没有任何间隔需要插入。

```python
# runnable: hb02_join
assert " | ".join(["java", "python", "go"]) == "java | python | go"
assert "-".join(("a", "b")) == "a-b"
assert ",".join(str(n) for n in [1, 2, 3]) == "1,2,3"
assert "-".join([]) == ""
assert "-".join(["a"]) == "a"
assert "-".join("abc") == "a-b-c"
try:
    ",".join([1, 2])
except TypeError:
    pass
else:
    raise AssertionError("join must receive strings")
print(" | ".join(["java", "python", "go"]))
```

传整个字符串进去，会逐字符连接，因为字符串本身也可迭代。把数字直接交给 join 不会自动调用 str；要明确转换。大量片段通常先收集再 join，比不断猜字符串拼接的代价更好维护。

7.2 从一段原始输入追到最终结果

```python
# runnable: hb02_clean_pipeline
raw = "  Java, Python,,Go  "
parts = raw.split(",")
cleaned = []
for part in parts:
    value = part.strip().lower()
    if value:
        cleaned.append(value)
result = " | ".join(cleaned)
assert parts == ["  Java", " Python", "", "Go  "]
assert cleaned == ["java", "python", "go"]
assert result == "java | python | go"
assert raw == "  Java, Python,,Go  "
print(parts, cleaned, result, sep="\n")
```

每轮先清理这一项的两端空白，再转小写，最后判断是否为空。空项是否丢弃是这里显式写出的业务规则，不是 split 或 join 替你猜的。

---

8）strip、lstrip、rstrip 与精确前后缀

8.1 不传参数，清理两端空白

strip 两端都处理，lstrip 只处理左边，rstrip 只处理右边。它们不删除字符串中间的空白，也不会修改原文本。

```python
# runnable: hb02_strip_whitespace
text = " \t a b \n"
assert text.strip() == "a b"
assert text.lstrip() == "a b \n"
assert text.rstrip() == " \t a b"
assert "".strip() == ""
assert " \t\n".strip() == ""
assert "a b".strip() == "a b"
print(repr(text.strip()))  # 'a b'
```

8.2 chars 是字符集合，不是一段完整文本

`strip(chars)` 从两端不停去掉属于 chars 的字符，碰到一个不属于的就停。lstrip、rstrip 也支持这个参数，只是处理方向不同。

```python
# runnable: hb02_strip_characters
text = "abbaXabba"
assert text.strip("ab") == "X"
assert text.lstrip("ab") == "Xabba"
assert text.rstrip("ab") == "abbaX"
assert "abc".strip("") == "abc"
assert "report.csv".rstrip(".csv") == "report"
assert "civic.csv".rstrip(".csv") == "civi"
print(text.strip("ab"))  # X
```

最后一个反例尤其重要：你本想只删 `.csv`，但 rstrip 会继续删掉文件主体末尾的 c，直到碰到 i 才停。结果碰巧正确一次，不代表用法正确。

8.3 removeprefix、removesuffix 按完整前后缀删除一次

```python
# runnable: hb02_exact_affixes
assert "Bearer token".removeprefix("Bearer ") == "token"
assert "civic.csv".removesuffix(".csv") == "civic"
assert "preprevalue".removeprefix("pre") == "prevalue"
assert "report.txt".removesuffix(".csv") == "report.txt"
assert "abc".removesuffix("") == "abc"
assert "".removeprefix("x") == ""
print("civic.csv".removesuffix(".csv"))
```

没有匹配就保持原值，不抛异常，也不是全局 replace。方法名就是在强调“只有前面/后面的这一段”。

---

9）大小写：六个方法各自改哪里

9.1 lower、upper、swapcase

lower 把有大小写的字符转小写，upper 转大写，swapcase 把大小写互换。它们没有“次数”或“起点”参数，数字和许多没有大小写的文字会保持原样。

```python
# runnable: hb02_case_conversion
text = "PyThon123中文"
assert text.lower() == "python123中文"
assert text.upper() == "PYTHON123中文"
assert text.swapcase() == "pYtHON123中文"
assert "".lower() == ""
assert "123".upper() == "123"
assert text == "PyThon123中文"
print(text.lower(), text.upper(), text.swapcase())
```

大小写转换不保证字符数不变。例如某些 Unicode 字符的大写可能展开为多个字符，所以不能先记录旧下标，再无条件拿它访问转换后的文本。

9.2 capitalize 与 title

capitalize 处理开头字符，并把其余字符转成小写；它不会帮你跳过开头空格。title 按单词边界做标题式大小写，但不是按人的语言理解专有名词。

```python
# runnable: hb02_capitalize_title
assert "pYTHON bACKEND".capitalize() == "Python backend"
assert " pYTHON".capitalize() == " python"
assert "pYTHON bACKEND".title() == "Python Backend"
assert "they're ready".title() == "They'Re Ready"
assert "".capitalize() == ""
assert "".title() == ""
print("pYTHON bACKEND".capitalize(), "pYTHON bACKEND".title())
```

apostrophe 这样的分隔会影响 title 的单词识别，因此它会给出 `They'Re`。它适合机械文本格式转换，不适合不加检查地改写用户姓名或正式名称。

9.3 casefold 用于更彻底的大小写无关比较

```python
# runnable: hb02_casefold
left, right = "straße", "STRASSE"
assert left.lower() != right.lower()
assert left.casefold() == right.casefold() == "strasse"
assert "ß".upper() == "SS"
assert len("ß".upper()) == 2
assert "".casefold() == ""
print(left.casefold())  # strasse
```

casefold 不是“让显示更好看”，而是为忽略大小写的比较做更强的转换。它也不等于 Unicode 规范化；重音字符的组合形式需要另外考虑 unicodedata.normalize。

---

10）ljust、rjust、center、zfill：不足时填充，不会截断

10.1 宽度是结果至少多长

`ljust(width, fillchar=" ")` 靠左，`rjust` 靠右，`center` 居中；fillchar 必须是一个字符。width 小于原长度时不截断，返回原来的内容值。

```python
# runnable: hb02_padding
assert "py".ljust(5, ".") == "py..."
assert "42".rjust(5, "0") == "00042"
assert "py".center(6, "-") == "--py--"
assert "python".ljust(3) == "python"
assert "".rjust(3, "_") == "___"
try:
    "py".ljust(6, "ab")
except TypeError:
    pass
else:
    raise AssertionError("fillchar must have length one")
print("py".center(6, "-"))
```

这里的宽度仍按字符串长度，不是终端里的显示列数。一个汉字可能占两列，组合字符也可能显示成一列，排终端表格时不能只靠 len 和 ljust 推断视觉宽度。

10.2 zfill 知道正负号应该留在前面

```python
# runnable: hb02_zfill
assert "42".zfill(5) == "00042"
assert "-42".zfill(6) == "-00042"
assert "+42".zfill(6) == "+00042"
assert "-42".rjust(6, "0") == "000-42"
assert "123456".zfill(3) == "123456"
assert "".zfill(3) == "000"
print("-42".zfill(6))  # -00042
```

zfill 的 width 包含符号长度。它只是字符串填充，不会先验证你提供的内容是否真是数值；例如给非数字文本也能补零。

10.3 expandtabs 把制表符展开到下一个制表位

```python
# runnable: hb02_expandtabs
assert "a\tb".expandtabs(4) == "a   b"
assert "ab\tc".expandtabs(4) == "ab  c"
assert "a\tb".expandtabs(0) == "ab"
assert "a\nb\tc".expandtabs(4) == "a\nb   c"
print(repr("ab\tc".expandtabs(4)))  # 'ab  c'
```

tabsize 默认是 8。不是每个制表符都换成固定 8 个空格，而是补到下一个制表位；当前已经写了几个字符，决定还需要几个空格。换行会重新开始计算列位置。

---

11）判断方法：返回 bool，但每个问题都不一样

11.1 startswith、endswith 支持一个或多个候选

写法 `text.startswith(prefix, start, end)`，范围参数可选；endswith 同理。prefix/suffix 可以是一个字符串，也可以是字符串元组，元组表示任意一个匹配即可，不是多个条件同时满足。

```python
# runnable: hb02_affix_tests
assert "report.py".startswith("report")
assert "report.py".endswith((".py", ".pyi"))
assert "xxpython".startswith("py", 2)
assert "python.txt".endswith("on", 0, 6)
assert "abc".startswith("")
assert "".endswith("")
assert not "report.PY".endswith(".py")
print("report.py".endswith((".py", ".pyi")))  # True
```

默认区分大小写，也不接受正则表达式。想忽略大小写，可以先按明确规则转换。不要用用户提供的后缀猜测文件内容类型，它只在比较文件名文本。

11.2 isalpha、isalnum、isspace

isalpha 要求每个字符都是字母；isalnum 允许字母和数字类字符；isspace 要求全是空白。三者都要求至少一个字符，因此空字符串返回 False。

```python
# runnable: hb02_basic_character_tests
assert "Python".isalpha()
assert "中文".isalpha()
assert not "abc_".isalpha()
assert "abc123".isalnum()
assert not "abc-123".isalnum()
assert " \t\n".isspace()
for method in ["".isalpha, "".isalnum, "".isspace]:
    assert method() is False
assert not " a ".isspace()
print("中文".isalpha(), " \t\n".isspace())  # True True
```

“字母”不只指英文 A 到 Z，所以 isalpha 不能直接当作“只允许英文字母”的校验。下划线也不是字母，虽然它可以出现在变量名里。

11.3 isdecimal、isdigit、isnumeric，数字范围逐渐变宽

isdecimal 针对十进制数字字符；isdigit 还接受一些其他数字字符，例如上标；isnumeric 的范围更宽，例如某些分数符号。它们不是“这段文本能否直接转 float”的判断。

```python
# runnable: hb02_numeric_character_tests
assert "123".isdecimal() and "123".isdigit() and "123".isnumeric()
assert "１２３".isdecimal()
assert "²".isdigit() and not "²".isdecimal()
assert "⅕".isnumeric() and not "⅕".isdigit()
assert not "-12".isdigit()
assert not "3.14".isdigit()
assert not "".isnumeric()
try:
    int("²")
except ValueError:
    pass
else:
    raise AssertionError("superscript is not integer text")
ascii_digits = "123".isascii() and "123".isdecimal()
assert ascii_digits
assert not ("１２３".isascii() and "１２３".isdecimal())
print(ascii_digits)  # True
```

允许负数、小数点、指数形式时，规则又不同。需要数值就尝试相应的 int/float 转换并处理异常；需要严格的 ASCII 数字串，则明确组合 isascii 和 isdecimal。

11.4 islower、isupper、istitle 看有大小写的字符

```python
# runnable: hb02_case_tests
assert "abc123!".islower()
assert "ABC123!".isupper()
assert not "123".islower()
assert not "中文".isupper()
assert "Python Backend".istitle()
assert not "PYTHON Backend".istitle()
assert not "".istitle()
assert not "".islower()
print("abc123!".islower())  # True
```

数字、标点可以出现在全小写字符串里；它们不参与大小写判定，但至少要有一个有大小写的字符。全数字并不同时算全大写和全小写。

11.5 isascii、isidentifier、isprintable

isascii 检查是否全在 ASCII 范围，空串也为 True。isidentifier 检查形状是否能作为标识符，但不会排除关键字；isprintable 检查字符是否可打印，普通空格允许，换行不允许，空串也为 True。

```python
# runnable: hb02_other_tests
import keyword

assert "abc123".isascii()
assert "".isascii()
assert not "中".isascii()
assert "user_name".isidentifier()
assert not "2users".isidentifier()
assert "class".isidentifier()
assert keyword.iskeyword("class")
assert "hello world".isprintable()
assert not "hello\nworld".isprintable()
assert "".isprintable()
print("user_name".isidentifier())  # True
```

可打印不等于可以直接放进 HTML、SQL 或 shell；这些安全边界有各自的编码与参数规则。这里只判断字符串字符属性。

---

12）translate、maketrans 与 encode：补齐常见文本转换工具

12.1 一次按字符表替换或删除

`str.maketrans(mapping)` 创建转换表，键可用单字符字符串或字符码点，值可用字符串、码点或 None。`text.translate(table)` 依表处理每个字符，None 表示删除；未列入的字符保持原样。

```python
# runnable: hb02_translate
table = str.maketrans({"-": None, "a": "A", "b": "BB"})
result = "a-b-c".translate(table)
assert result == "ABBc"
assert "xyz".translate(table) == "xyz"
assert "".translate(table) == ""
pair_table = str.maketrans("ab", "AB", "-")
assert "a-b-c".translate(pair_table) == "ABc"
print(result)  # ABBc
```

第二种 maketrans 写法里，第一个字符串与第二个字符串长度必须相同，逐字符对应；第三个字符串可选，列出要删除的字符。translate 是逐字符转换，不是任意长子串查找替换。

12.2 encode 从文本变字节，decode 再变回来

```python
# runnable: hb02_encode
text = "中文"
data = text.encode("utf-8")
assert isinstance(data, bytes)
assert len(data) == 6
assert data.decode("utf-8") == text
try:
    text.encode("ascii")
except UnicodeEncodeError:
    pass
else:
    raise AssertionError("ascii cannot encode this text")
assert text.encode("ascii", errors="replace") == b"??"
print(len(text), len(data))  # 2 6
```

encode 的常用参数是 encoding 和 errors。默认严格处理无法编码的内容；ignore 或 replace 会丢失信息，不能为了“别报错”就随便打开。读取字节时要知道原编码，而不是试着解成一个不报错的字符串就算成功。

---

13）三道组合题，附参考答案

13.1 解析一条配置

题目：解析 `" timeout = 30 "`，返回键与值；只按第一个等号分开，允许值里继续有等号。没有等号或键为空时拒绝。

```python
# runnable: hb02_exercise_config
def parse_setting(text):
    key, separator, value = text.partition("=")
    key = key.strip()
    if not separator or not key:
        raise ValueError("expected non-empty key=value")
    return key, value.strip()

assert parse_setting(" timeout = 30 ") == ("timeout", "30")
assert parse_setting("token=a=b") == ("token", "a=b")
assert parse_setting("name=") == ("name", "")
for bad in ["name", "=x"]:
    try:
        parse_setting(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(bad)
print(parse_setting(" timeout = 30 "))
```

参考思路：partition 保证三项，先判断分隔符是否存在，再清理键值。空值和没有分隔符不能混为一谈。

13.2 生成固定宽度编号

题目：给整数编号加前缀，7 变成 `ITEM-0007`，12345 不截断。说明为什么 zfill 不会替你把任意文本变成合法整数。

```python
# runnable: hb02_exercise_identifier
def item_code(number):
    if type(number) is not int or number < 0:
        raise ValueError("expected non-negative integer")
    return "ITEM-" + str(number).zfill(4)

assert item_code(7) == "ITEM-0007"
assert item_code(12345) == "ITEM-12345"
assert item_code(0) == "ITEM-0000"
print(item_code(7))
```

先校验再格式化。宽度是最少长度，不是固定裁切长度；如果业务最多只允许四位，应另写范围检查。

13.3 清理标签但保留原有先后

题目：把 `" Python,java, PYTHON ,,Go "` 变成 `"python | java | go"`。空项丢弃，大小写无关去重，以首次出现顺序为准。

```python
# runnable: hb02_exercise_tags
def normalize_tags(raw):
    result = []
    seen = set()
    for part in raw.split(","):
        tag = part.strip().casefold()
        if tag and tag not in seen:
            seen.add(tag)
            result.append(tag)
    return " | ".join(result)

assert normalize_tags(" Python,java, PYTHON ,,Go ") == "python | java | go"
assert normalize_tags("") == ""
assert normalize_tags(" , , ") == ""
print(normalize_tags(" Python,java, PYTHON ,,Go "))
```

set 只负责快速判断有没有见过，list 负责保留首次出现的顺序。直接把集合 join 起来，顺序就不是这里约定的顺序了。

---

14）查阅位置

完整参数和 Unicode 分类边界见 [Python 3.11 字符串方法](https://docs.python.org/3.11/library/stdtypes.html#string-methods)。码点、编码与规范化概念见 [Unicode 指南](https://docs.python.org/3.11/howto/unicode.html)。本章例子都是字面文本处理，不把文本判断方法当成完整业务校验。
