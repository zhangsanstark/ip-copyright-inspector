04 · 字典与集合：按键取值，按成员判断

列表擅长按顺序放数据，字典擅长“拿这个键找对应值”，集合擅长“这一项有没有”和“两组数据有什么关系”。这章按创建、读取、修改、遍历、组合的顺序讲，重点是默认值是否写入、共享在哪里、集合运算是否改原对象。

在仓库根目录运行 `python scripts/check_handbook_examples.py --chapter 04 --show-output`。代码块彼此独立，不需要真实数据库或网络。

---

1）字典先看键，再看值

1.1 三种常见创建方式

```python
# runnable: hb04_dict_creation
literal = {"id": 7, "name": "Ada"}
keywords = dict(id=7, name="Ada")
pairs = dict([("id", 7), ("name", "Ada")])
assert literal == keywords == pairs
assert dict() == {}
assert dict([("name", "old"), ("name", "new")]) == {"name": "new"}
print(literal)
```

键和值用冒号连接，多个键值对用逗号分开。dict 接收键值对序列时，每项要能拆成两部分。相同键出现多次，后面的值覆盖前面的值，不会自动积累为列表。

关键字创建方式的键来自参数名，因此写法受到标识符规则约束。带横线、空格等键通常直接用字面量，例如 `{"content-type": "text/plain"}`。

1.2 为什么列表不能当键

字典通过哈希查找定位键。键需要可哈希：哈希值在生命周期内不能随意变化，相等的键应得到相同哈希值。字符串、整数和只含可哈希元素的元组很常见；列表、字典、普通集合不支持直接作为键。

```python
# runnable: hb04_hashable_keys
mapping = {("user", 7): "Ada"}
assert mapping[("user", 7)] == "Ada"
for key in [[1, 2], {"a": 1}, {1, 2}, (1, [])]:
    try:
        {key: "value"}
    except TypeError:
        pass
    else:
        raise AssertionError("unhashable key accepted")
assert hash(("user", 7)) == hash(("user", 7))
print(mapping)
```

“不可变”是理解常见内置类型的线索，不是对任意自定义类型的完整判定方式。也不能因为两个键哈希相同就认定它们相等，字典还会结合相等比较处理碰撞。

1.3 1、True、1.0 为什么可能是同一个键

```python
# runnable: hb04_equal_numeric_keys
mapping = {1: "integer"}
mapping[True] = "boolean"
mapping[1.0] = "float"
assert len(mapping) == 1
assert mapping[1] == "float"
assert 1 == True == 1.0
assert hash(1) == hash(True) == hash(1.0)
print(len(mapping), mapping[1])  # 1 float
```

字典不是“类型不同就一定两项”。这些数值相等且哈希相同，会命中同一个键位置。如果业务需要区分类型，要明确设计键，例如 `("int", 1)` 和 `("bool", True)`。

---

2）插入顺序：可以依赖遍历顺序，但不能当位置下标

现代 Python 字典按插入顺序遍历。修改已有键的值不改变位置；删除后重新插入，才进入新的插入位置。相等比较则主要比较键值内容，不要求插入顺序一致。

```python
# runnable: hb04_order
settings = {"first": 1, "second": 2}
settings["first"] = 10
assert list(settings) == ["first", "second"]
del settings["first"]
settings["first"] = 100
assert list(settings) == ["second", "first"]
assert settings == {"first": 100, "second": 2}
assert list(reversed(settings)) == ["first", "second"]
try:
    settings[0]
except KeyError:
    pass
else:
    raise AssertionError("0 is a key, not a position")
print(list(settings))
```

`settings[0]` 找键 0，不是第一个值。需要第几项时，应考虑列表，或者明确把字典转换成项目需要的序列形式。

---

3）读取：方括号、get 和缺失哨兵

3.1 必须有与允许没有

方括号 `mapping[key]` 缺键时抛 KeyError。`mapping.get(key, default=None)` 缺键时返回默认值，不会插入默认值，也不会替换已存在的 None、0 或空字符串。

```python
# runnable: hb04_get
user = {"nickname": None, "visits": 0}
assert user["nickname"] is None
assert user.get("nickname", "guest") is None
assert user.get("visits", 99) == 0
assert user.get("role", "reader") == "reader"
assert "role" not in user
assert user.get("missing") is None
try:
    user["missing"]
except KeyError:
    pass
else:
    raise AssertionError("missing key")
print(user)
```

读完这段应能回答：为什么 get 没写入 role？因为它的任务只是读取；“读不到给一个替代值”不是“帮我建立数据”。

3.2 需要区分缺键与值就是 None

```python
# runnable: hb04_missing_sentinel
missing = object()
user = {"nickname": None}
nickname = user.get("nickname", missing)
role = user.get("role", missing)
assert nickname is None
assert nickname is not missing
assert role is missing
assert "nickname" in user
assert "role" not in user
print(nickname, role is missing)  # None True
```

object() 在这里创建一个独特标记，只有没找到键时才拿到它。这个标记常叫哨兵值。也可以先写 `if key in mapping`；选择哪种更清楚，不必为了用术语而复杂化。

---

4）增改：直接赋值、update、合并

4.1 同一个赋值语句，缺键新增、有键覆盖

```python
# runnable: hb04_assign_update
settings = {"timeout": 3}
settings["retries"] = 2
settings["timeout"] = 5
assert settings == {"timeout": 5, "retries": 2}
returned = settings.update({"timeout": 8, "debug": False})
assert returned is None
assert settings == {"timeout": 8, "retries": 2, "debug": False}
settings.update([("retries", 4)], region="local")
assert settings["retries"] == 4
assert settings["region"] == "local"
print(settings)
```

update 接收映射或键值对序列，也可接关键字字段；它修改原字典并返回 None。它不是深层合并，嵌套字典命中同名键时会整体覆盖。

4.2 | 建新字典，|= 修改原字典

```python
# runnable: hb04_dict_union
base = {"timeout": 3, "nested": {"x": 1}}
custom = {"timeout": 9}
merged = base | custom
assert merged["timeout"] == 9
assert base["timeout"] == 3
assert merged["nested"] is base["nested"]
alias = base
base |= custom
assert alias["timeout"] == 9
assert base is alias
assert {**base, "timeout": 12}["timeout"] == 12
print(merged)
```

右侧同名键获胜。新建外层不代表深拷贝，未替换的嵌套值仍可能共享。普通 dict 的 `|` 两边使用字典；update、`|=` 可接收的输入形式更宽，不要把所有写法当成完全相同的接口。

---

5）删除：pop、popitem、del、clear

5.1 pop(key, default) 按键删除并取回值

```python
# runnable: hb04_pop
settings = {"debug": False, "timeout": 3}
removed = settings.pop("debug")
assert removed is False
assert "debug" not in settings
assert settings.pop("missing", "fallback") == "fallback"
assert "missing" not in settings
try:
    settings.pop("missing")
except KeyError:
    pass
else:
    raise AssertionError("missing key without default")
print(settings)
```

pop 的默认值只负责缺键时给出返回结果，不会新增该键。与 get 的区别是命中时会真正删除。

5.2 popitem 弹出最后插入的一对键值

```python
# runnable: hb04_popitem_clear
mapping = {"a": 1, "b": 2}
assert mapping.popitem() == ("b", 2)
assert mapping == {"a": 1}
del mapping["a"]
assert mapping == {}
try:
    mapping.popitem()
except KeyError:
    pass
else:
    raise AssertionError("empty dict")
mapping["x"] = 1
alias = mapping
assert mapping.clear() is None
assert alias == {}
print(alias)
```

不要把 dict.popitem 与 set.pop 混淆：现代字典按最后插入顺序弹出键值对；集合没有这种最后插入的约定。del 删除键没有返回值，clear 清空原对象，另一个引用也会看到变化。

---

6）keys、values、items：遍历出来的是什么

6.1 默认遍历键，items 每轮给一对

```python
# runnable: hb04_iteration
scores = {"Ada": 95, "Lin": 88}
assert list(scores) == ["Ada", "Lin"]
assert list(scores.keys()) == ["Ada", "Lin"]
assert list(scores.values()) == [95, 88]
assert list(scores.items()) == [("Ada", 95), ("Lin", 88)]
result = []
for item in scores.items():
    name, score = item
    result.append(f"{name}={score}")
assert result == ["Ada=95", "Lin=88"]
assert "Ada" in scores
assert 95 not in scores
assert 95 in scores.values()
print(result)
```

`for name, score in scores.items()` 是上面拆包过程的简写。`in dict` 只查键，不查值；想查值要显式选择 values。

6.2 视图不是快照

```python
# runnable: hb04_views
scores = {"Ada": 95}
view = scores.keys()
snapshot = list(scores)
scores["Lin"] = 88
assert list(view) == ["Ada", "Lin"]
assert snapshot == ["Ada"]
assert scores.keys() & {"Ada", "Bob"} == {"Ada"}
assert ("Ada", 95) in scores.items()
print(list(view), snapshot)
```

keys、values、items 是动态视图，原字典改变后它们反映新内容。转成 list 才固定当时的元素集合，但里面的可变对象仍可能共享，不等于深拷贝。键视图支持集合式操作；不要把所有视图都当作普通 set 使用，值视图尤其不保证唯一。

6.3 需要删除时，先收集再删

```python
# runnable: hb04_safe_delete
scores = {"Ada": 95, "Lin": 40, "Bob": 50}
to_delete = []
for name, score in scores.items():
    if score < 60:
        to_delete.append(name)
assert to_delete == ["Lin", "Bob"]
for name in to_delete:
    del scores[name]
assert scores == {"Ada": 95}
print(scores)
```

遍历原字典时增删键可能报 RuntimeError，也可能让遍历逻辑漏项。这个两阶段写法把“决定删谁”和“真正删除”分开，边界更清楚。

---

7）setdefault、fromkeys、copy：默认和复制最容易藏共享

7.1 setdefault 缺键时才写入默认值

```python
# runnable: hb04_setdefault
groups = {}
first = groups.setdefault("backend", [])
assert first == [] and first is groups["backend"]
first.append(1)
second = groups.setdefault("backend", [])
assert second is first
second.append(2)
assert groups == {"backend": [1, 2]}
assert groups.setdefault("frontend") is None
assert "frontend" in groups
print(groups)
```

第一轮缺键：插入空列表，返回它，再追加 1。第二轮已有键：返回旧列表，再追加 2。省略默认值时默认插入 None；旧值本来是 None 时也不会自动替你换成列表。

调用参数表达式会先求值，所以 `setdefault(key, expensive())` 即使键存在，也会先调用 expensive。要避免昂贵的默认构造，显式 if 分支或合适的 defaultdict 更清楚。

7.2 fromkeys 构造相同初值，但不是每键自动复制

```python
# runnable: hb04_fromkeys
assert dict.fromkeys(["a", "b", "a"]) == {"a": None, "b": None}
shared = dict.fromkeys(["a", "b"], [])
shared["a"].append(1)
assert shared == {"a": [1], "b": [1]}
assert shared["a"] is shared["b"]
separate = {key: [] for key in ["a", "b"]}
separate["a"].append(1)
assert separate == {"a": [1], "b": []}
print(shared, separate)
```

fromkeys 的第二个参数是同一份默认对象；不是“每遇到一个键就重新执行一次默认表达式”。可变值需要逐键创建。

7.3 copy 只复制字典外层

```python
# runnable: hb04_dict_copy
source = {"tags": ["api"]}
copied = source.copy()
assert copied is not source
assert copied["tags"] is source["tags"]
copied["tags"].append("db")
assert source["tags"] == ["api", "db"]
copied["tags"] = ["new"]
assert source["tags"] == ["api", "db"]
print(source, copied)
```

同样按层分析：先通过共享引用修改内部列表，会影响原字典；后来只替换副本某个键对应的引用，不影响原键指向。第 03 章的复制规则在这里仍然成立。

---

8）集合：不重复、不按下标取值

8.1 创建、查成员、大小

```python
# runnable: hb04_set_creation
tags = {"api", "db", "api"}
assert tags == {"api", "db"}
assert len(tags) == 2
assert "api" in tags and "cache" not in tags
assert set("banana") == {"b", "a", "n"}
assert set() == set([])
assert type({}) is dict
try:
    tags[0]
except TypeError:
    pass
else:
    raise AssertionError("set has no positional index")
print(sorted(tags))
```

`{}` 是空字典，空集合用 set()。集合成员需要可哈希；同样的数值相等规则也可能让 1、True、1.0 合并为一个成员。打印顺序不应作为业务逻辑依据，例子里排序只是方便核对。

8.2 add 与 update

```python
# runnable: hb04_set_add_update
tags = {"api"}
assert tags.add("db") is None
assert tags == {"api", "db"}
tags.add("db")
assert len(tags) == 2
assert tags.update(["cache", "db"], {"orm"}) is None
assert tags == {"api", "db", "cache", "orm"}
letters = set()
letters.update("ab")
assert letters == {"a", "b"}
letters.add("cd")
assert "cd" in letters
print(sorted(tags))
```

add 把整个对象作为一项；update 逐项取出一个或多个可迭代对象中的内容。add 一个列表会因不可哈希报错，但 update 一个列表会尝试添加列表里的每个元素。

8.3 remove、discard、pop、clear

```python
# runnable: hb04_set_delete
tags = {"api", "db"}
assert tags.discard("missing") is None
assert tags.remove("api") is None
assert tags == {"db"}
try:
    tags.remove("missing")
except KeyError:
    pass
else:
    raise AssertionError("remove must report missing element")
assert tags.pop() == "db"
try:
    tags.pop()
except KeyError:
    pass
else:
    raise AssertionError("empty set")
tags.update(["a", "b"])
assert tags.clear() is None
assert not tags
print(tags)
```

remove 找不到报错，discard 找不到也完成；pop 删除并返回任意一个成员，不是最后加入者。这里只剩 db 时才能精确断言 pop 的具体值。多元素集合应检查返回值属于旧集合和集合大小变化，而不是猜它先弹谁。

---

9）集合关系：共有、合并、独有和包含

9.1 不改原集合的四种运算

```python
# runnable: hb04_set_algebra
left = {"read", "write"}
right = {"read", "audit"}
assert left | right == {"read", "write", "audit"}
assert left & right == {"read"}
assert left - right == {"write"}
assert right - left == {"audit"}
assert left ^ right == {"write", "audit"}
assert left.union(right) == left | right
assert left.intersection(right) == left & right
assert left.difference(right) == left - right
assert left.symmetric_difference(right) == left ^ right
assert left == {"read", "write"}
print(sorted(left ^ right))
```

并集保留双方所有成员；交集保留共有成员；差集保留左边有、右边没有的；对称差集保留只属于其中一方的。差集换左右可能变，其他三个这里换左右不变。

集合运算符通常要求集合操作数；对应方法可接受一般可迭代输入。union、intersection、difference 可以接多组输入；symmetric_difference 比较两边。

```python
# runnable: hb04_set_methods_iterables
base = {1, 2, 3}
assert base.union([4], (5,)) == {1, 2, 3, 4, 5}
assert base.intersection([2, 3], [3, 4]) == {3}
assert base.difference([1], [2]) == {3}
assert base.symmetric_difference([3, 4]) == {1, 2, 4}
assert base & set() == set()
assert base | set() == base
print(sorted(base.difference([1], [2])))
```

9.2 子集、超集和互不相交

```python
# runnable: hb04_set_relations
needed = {"read"}
owned = {"read", "write"}
assert needed <= owned
assert needed < owned
assert owned >= needed
assert owned > needed
assert needed.issubset(owned)
assert owned.issuperset(needed)
assert owned.isdisjoint({"audit"})
assert not owned.isdisjoint({"read"})
assert needed <= needed
assert not needed < needed
assert set() <= owned
print(needed <= owned)
```

`<=` 允许相等，`<` 要求真子集，即至少少一个成员；不是按集合大小或字母顺序排序。大小相同的两个不同集合，可能谁也不包含谁。isdisjoint 问是否完全没有共同成员。

9.3 带 update 的变体修改原对象

```python
# runnable: hb04_set_inplace
values = {1, 2, 3}
alias = values
assert values.intersection_update({2, 3, 4}) is None
assert alias == {2, 3}
assert values.difference_update({2}) is None
assert values == {3}
assert values.symmetric_difference_update({3, 4}) is None
assert values == {4}
values |= {5}
values &= {4, 5, 6}
values -= {4}
values ^= {5, 6}
assert values == {6}
assert alias is values
copied = values.copy()
assert copied == values and copied is not values
print(values)
```

原地方法返回 None，`|=`、`&=`、`-=`、`^=` 则是对应的赋值语句形式。别把返回新集合的 difference 和原地修改的 difference_update 写混。

---

10）frozenset：集合内容固定后，可以作为键

```python
# runnable: hb04_frozenset
permissions = frozenset(["read", "write"])
assert permissions == {"write", "read"}
cache = {permissions: "allowed"}
assert cache[frozenset(["write", "read"])] == "allowed"
extended = permissions | {"audit"}
assert extended == {"read", "write", "audit"}
assert permissions == {"read", "write"}
assert not hasattr(permissions, "add")
print(sorted(permissions))
```

frozenset 没有 add、remove、update 等原地修改方法。元素依然要可哈希。它适合把“这组成员本身”作为字典键，而不想让成员顺序影响键是否相等。

---

11）练习与参考答案

11.1 统计状态码次数

题目：输入 `[200, 500, 200, 404]`，得到 `{200: 2, 500: 1, 404: 1}`。不使用 Counter，先把字典累计写熟。

```python
# runnable: hb04_exercise_counts
counts = {}
for status in [200, 500, 200, 404]:
    previous = counts.get(status, 0)
    counts[status] = previous + 1
assert counts == {200: 2, 500: 1, 404: 1}
print(counts)
```

get 读取旧值或临时给 0，后面的赋值才真正写入。不能只调用 get 就以为字典里已经有计数。

11.2 给每条记录分组

题目：把 `[("api", 10), ("db", 20), ("api", 30)]` 按名称汇总为列表。

```python
# runnable: hb04_exercise_groups
groups = {}
for name, duration in [("api", 10), ("db", 20), ("api", 30)]:
    if name not in groups:
        groups[name] = []
    groups[name].append(duration)
assert groups == {"api": [10, 30], "db": [20]}
assert groups["api"] is not groups["db"]
print(groups)
```

别用 `dict.fromkeys(names, [])` 提前创建共享列表。每个键在首次出现时独立创建即可。

11.3 列出缺少的权限

题目：需要 read、write，实际有 read、audit；给出缺少和多出的权限，并判断能否放行。

```python
# runnable: hb04_exercise_permissions
required = {"read", "write"}
owned = {"read", "audit"}
missing = required - owned
extra = owned - required
allowed = not missing
assert missing == {"write"}
assert extra == {"audit"}
assert allowed is False
assert allowed == (required <= owned)
print(sorted(missing), sorted(extra), allowed)
```

集合只能帮你比较权限标签；真实授权还取决于这些权限是否来自可信来源。本题只讨论数据运算，不把用户自报的集合当成授权依据。

---

12）查阅位置

字典的键、插入顺序、动态视图见 [Python 3.11 映射类型](https://docs.python.org/3.11/library/stdtypes.html#mapping-types-dict)。集合完整方法与运算见 [集合类型](https://docs.python.org/3.11/library/stdtypes.html#set-types-set-frozenset)。defaultdict、Counter 等专用容器在本手册第 23 章继续展开。
