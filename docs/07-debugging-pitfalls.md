常见错误与调试清单

这里专门收集“代码能写出来，结果却和想的不一样”的问题。每次先猜输出，再看解释，最后运行 `examples/pitfalls_lab.py` 验证。比起背一遍规则，弄清“我刚才为什么猜错”更容易记住。

查找顺序：1—6 看默认值、闭包、property 和命名；7—10 看容器、拷贝和比较；11 看异常怎么用；12—15 看异步、Session 和进程；16—17 是排错顺序和提交前检查。

---

1）第二次调用多了旧数据：先查可变默认参数

1.1 错在哪：默认列表不是每次都新建

看到 `bucket=[]`，很容易以为每次调用都拿到一个空列表。实际这个列表在定义函数时就创建好了，之后省略 `bucket` 的调用会反复用它。

错误示例：

```python
def collect(value, bucket=[]):
    bucket.append(value)
    return bucket


print(collect("a"))
print(collect("b"))
```

第一次是 `['a']`，第二次是 `['a', 'b']`。第二次没有传入新列表，函数就继续往上次那一个里添加。

1.2 怎么改：用 None 表示“这次需要新建”

```python
def collect(value: str, bucket: list[str] | None = None) -> list[str]:
    if bucket is None:
        bucket = []
    bucket.append(value)
    return bucket
```

这样每次省略参数，都会进入 `if` 新建列表；主动传了列表，就往指定列表里加。默认值通常可以直接用 `None`、数字、字符串、布尔值，以及内容也全部不可变的元组。别只看外层是元组就放心：里面如果装着列表，那个列表依然能被修改。

---

2）三个函数都返回最后一个数字：闭包取值太晚了

循环创建 lambda 时，它并没有给当时的 `i` 拍张快照。它记住的是“到时去找 i”，真正调用时才取值；等循环结束，`i` 已经变成最后一个值了。这叫“晚期绑定”。

```python
wrong = [lambda: i for i in range(3)]
print([func() for func in wrong])

fixed = [lambda i=i: i for i in range(3)]
print([func() for func in fixed])
```

第一组输出 `[2, 2, 2]`；第二组输出 `[0, 1, 2]`。`i=i` 左边是当前 lambda 的参数名，右边会在创建它时读取当前循环值，所以每个函数留下的是各自那一轮的数字。

如果 `i=i` 看着绕，可以换成工厂函数：每轮调用工厂，让它用自己的局部变量创建函数。核心不是一定要用 lambda，而是别让所有函数到最后还去找同一个循环变量。

---

3）property 一赋值就递归：对外名字和存储名字混用了

3.1 错在哪：setter 里面又请 setter 处理一次

先看这个错误结构。`self.password = value` 本身就是进入 setter 的入口：

```python
class Account:
    @property
    def password(self) -> str:
        return self.password

    @password.setter
    def password(self, value: str) -> None:
        self.password = value
```

setter 内部还是这句赋值，就会再次进入 setter，接着又进入一次，最后抛出 `RecursionError`。getter 里的 `return self.password` 也一样：想读值，却又调用自己读一遍。

3.2 怎么改：password 处理规则，_password 保存数据

```python
class Account:
    def __init__(self, password: str) -> None:
        self.password = password

    @property
    def password(self) -> str:
        return "******"

    @password.setter
    def password(self, value: str) -> None:
        if len(value) < 8:
            raise ValueError("password must contain at least 8 characters")
        self._password = value
```

这里外面读取 `password` 得到掩码，写入 `password` 经过长度检查，真正的赋值落在 `_password`，所以不会再绕回 setter。下划线只是内部命名约定，掩码也只是显示规则，不等于密码已被加密或安全保存。

如果不需要校验、延迟计算或兼容旧接口，直接使用公开属性就好，不用给每个字段都套 property。

---

4）明明外面有 count，里面却报 UnboundLocalError

`count += 1` 不是只读 count，它还要把结果重新赋给 count。函数里出现这种赋值，又没有 `nonlocal` 或 `global` 声明，Python 就默认把 count 当作这个函数自己的局部变量。问题是：右边先要读它，局部值却还没创建。

```python
def make_counter():
    count = 0

    def increment():
        count += 1
        return count

    return increment
```

先执行 `counter = make_counter()`，再调用返回的 `counter()`，就会进入 increment 并抛出 `UnboundLocalError`；只定义函数不会报错。要修改外层函数那份 count，就在 `increment` 开头写 `nonlocal count`。如果要重新绑定的是模块级全局变量，才用 `global`。可以这样区分：外层函数里已有的变量，用 nonlocal；模块全局的，用 global。

---

5）list() 突然不能调用：名字被自己的变量占用了

```python
list = [1, 2, 3]
id = "asset-1"
```

这两行语法没错，但 `list` 现在指向列表对象，`id` 现在指向字符串。接下来写 `list()` 或 `id()`，Python 找到的不再是原来的内置函数，而是你刚放进去的值，于是调用失败。

起变量名时尤其避开 `list`、`dict`、`set`、`str`、`type`、`id`、`len`、`input`、`filter` 和 `sum`。

改成 `values`、`asset_id`、`item_type`、`total_length`，既不占用内置名字，也能看出数据用途。如果是在交互式解释器里踩坑，改完代码后还要清理旧绑定，重新启动解释器是最直接的办法。

---

6）行尾分号能运行，但通常直接省略

Java 写惯了，顺手留下 `return "***";` 很正常。Python 允许行尾分号，这通常不是报错原因；只是普通代码不需要它。每行写一条语句、去掉末尾分号即可，不必把它误记成“Python 绝对不能有分号”。

---

7）想加两个元素，却加进了一个列表：append 和 extend 用反了

```python
items = ["a"]
items.append(["b", "c"])
print(items)

items = ["a"]
items.extend(["b", "c"])
print(items)
```

第一次输出 `['a', ['b', 'c']]`：`append` 把整个参数当成一个元素放进去。第二次输出 `['a', 'b', 'c']`：`extend` 先遍历参数，再把里面的元素一个个加入。

选哪个就问自己一句：要“放进去一个东西”，还是“把里面的东西倒进去”？字符串也能被遍历，所以 `extend("bc")` 会加入 `"b"`、`"c"` 两个字符，不会加入完整的 `"bc"`。

---

8）已经 copy 了，原数据还在变：里面的小列表没复制

```python
original = [[1], [2]]
copied = original.copy()
copied[0].append(99)
print(original)
```

输出是 `[[1, 99], [2]]`。`original.copy()` 新建的是外层列表，里面仍指向原来的两个小列表。`copied[0].append(99)` 改的是共享的小列表，所以从 `original` 看也变了。

如果需要连内部对象一起递归复制，可以考虑 `copy.deepcopy`；但不要一遇到共享就全量深拷贝。先确认哪些数据必须独立，减少到处共同修改嵌套容器，通常更容易维护。

---

9）内容明明一样，is 却是 False：它比较的是对象身份

`==` 问“值相不相等”，`is` 问“是不是同一个对象”。像 Java 中区分值比较和引用比较一样，先确定自己要问哪一个问题。

```python
a = [1, 2]
b = [1, 2]
print(a == b)
print(a is b)
```

输出依次是 `True`、`False`：两个列表内容一样，但分别创建，不是同一个对象。

检查空值用 `value is None`。比较字符串、数字、列表或业务对象的值，用 `==`。有些短字符串或小整数用 `is` 也碰巧得到 True，那可能是解释器复用了对象，不能把这种现象当作业务规则。

---

10）取字典值：必须有就用方括号，允许缺失再用 get

```python
record = {"name": "demo"}
required = record["name"]
optional = record.get("description")
```

`record["name"]` 表示“这条记录应该有 name，没有就让 `KeyError` 提醒我”；`record.get("description")` 表示“描述可以没有，没有时先给我 None”。

别为了“不报错”把方括号全改成 get。必填字段丢了却继续往下走，可能很久之后才出现一个不相关的 None 错误，反而更难找原因。

如果字段本来就允许保存 None，还想区分“没这个键”和“有键但值为 None”，可以创建一个专门表示缺失的对象。这种专用标记叫“哨兵”：

```python
missing = object()
value = record.get("description", missing)
if value is missing:
    print("field is absent")
```

---

11）限流时该 raise 还是返回 False：先看调用方怎么处理

两种都能合理使用，不是 raise 一定更专业，也不是 False 一定更安全。关键是超限后，这段流程应该继续判断，还是立刻停下。

- 如果超限是正常分支，调用方预计频繁判断，可返回布尔值或结果对象。
- 如果超限必须立刻中断当前操作，可抛出专门异常，例如 RateLimitExceeded。
- 在 Web API 层，可以把领域异常统一映射为 HTTP 429。
- 不要抛出过于宽泛的 Exception，也不要捕获后静默忽略。

这和 Java 后端分层很像：负责限流的代码说明“已超限”，Web 接口层再决定把它转成 HTTP 429。先把这个约定写清楚，调用方才知道该判断返回值，还是捕获专门异常。

---

12）加了 async 还是卡住：里面仍在调用阻塞函数

`async def` 只是让函数成为协程函数，不会改写里面每个调用的行为。下面的 `time.sleep` 仍然让当前线程原地等一秒；同一事件循环中的其他任务也只能跟着等：

```python
import time


async def wrong():
    time.sleep(1)
```

模拟异步等待用 `await asyncio.sleep(...)`，让当前协程等待时，其他任务有机会推进。没有异步接口的旧阻塞函数，可以先用 `asyncio.to_thread` 放到线程；数据库、HTTP 客户端等调用链则优先使用原生异步库。

CPU 密集计算放进 to_thread 也不会自动绕过默认 CPython 的 GIL。需要真并行时考虑进程池、原生扩展或专门的计算服务。

---

13）gather 报错了，其他任务为什么还在跑

13.1 gather 一起等待，不保证“一败全停”

`asyncio.gather` 负责并发等待多个可等待对象，不等于数据库事务。本文的 Python 3.11+ 环境中，默认 gather 遇到第一个异常，就把它抛给等待者；其他任务不会因此自动取消，仍会继续运行。

要区分两件事：“某个子任务失败”和“gather 自己被取消”。后者会把取消传给尚未完成的子任务，前者默认不会把其他任务一起停掉。

13.2 需要一起收尾时，考虑 TaskGroup

如果几个任务共同组成一次操作，通常希望一个任务以非取消异常失败时，取消其余任务并等它们收尾，可以用 `asyncio.TaskGroup`。它帮你管理任务之间的失败和取消，但不负责撤销已经提交的数据库写入。

无论选哪一种，都要考虑超时、取消和资源归还；每个任务也要独立持有不该共享的 Session 等对象。

---

14）多个任务共用一个 AsyncSession：事务状态容易互相干扰

SQLAlchemy 的 Session / AsyncSession 不是一个无状态工具箱，它记着当前事务正在做什么。可以类比 Java 里带事务状态的 EntityManager：一个任务准备提交，另一个任务还想继续操作，同一份状态就容易冲突。

所以不要把同一个 AsyncSession 同时传给多个 gather 任务。每个并发任务用自己的一份，通常通过依赖注入或 `async with` 管理创建和关闭。共享会话可能带来事务状态冲突、隐式 I/O 和难以定位的并发错误。

---

15）Windows 进程反复启动：把入口放进 main guard

Windows 通常使用 spawn 启动子进程，子进程会重新导入主模块。模块一导入就创建进程池，子进程也会再建池，启动就可能一层层重复。下面的保护块让主流程只在“直接运行这个文件”时执行，而不是每次导入都执行：

```python
def main() -> None:
    ...


if __name__ == "__main__":
    main()
```

提交多进程示例前，应至少在 Windows 上验证入口保护；库模块本身不应在导入时启动进程或执行耗时任务。

---

16）报错时按这个顺序查，别先凭感觉改代码

先保留完整报错，别只截最后半句话。然后逐步缩小范围：

16.1 从 traceback 最底部看异常类型、消息和直接原因，再往上找是哪一层把数据传错。

16.2 用 `repr` 看字符串里的空格、换行和容器嵌套，避免“打印起来差不多”骗过自己。

16.3 用 `type`、`isinstance` 确认真实类型，别只凭变量名猜。

16.4 把问题缩成能单独运行的最小例子，保留关键输入、边界值和分支。

16.5 仍不清楚时，用 `breakpoint` 停下来检查局部变量和调用栈。

16.6 确认原因后，先写一个能复现错误的自动化测试，再修复实现，最后让测试证明修复有效。

日志不要记录密码、令牌、完整个人信息、浏览器会话或组织内部数据。异常日志也可能包含请求体和连接字符串，公开前必须检查。

---

17）提交前，快速扫一遍这些问题

- 是否使用了可变默认参数。
- 是否在循环中创建了引用循环变量的闭包。
- property 内部存储是否使用独立名称。
- 是否遮蔽了内置名称。
- 是否误用 is 比较业务值。
- 是否把阻塞函数放进事件循环。
- 是否在并发任务间共享 Session 或可变对象。
- Windows 多进程是否保护入口。
- 异常处理是否保留了足够上下文且没有泄露敏感数据。
- 新增 Markdown 是否通过 scripts/check_note_format.py。
