常见错误与调试清单

这份清单把最容易“看起来能写、运行后却不符合预期”的问题集中在一起。建议先预测每段代码的输出，再运行 examples/pitfalls_lab.py。

---

可变默认参数会跨调用共享

默认参数在函数定义时求值一次，不是在每次调用时重新创建。

错误示例：

```python
def collect(value, bucket=[]):
    bucket.append(value)
    return bucket


print(collect("a"))
print(collect("b"))
```

第二次输出不是只含 b，而是继续使用第一次的列表。

推荐写法：

```python
def collect(value: str, bucket: list[str] | None = None) -> list[str]:
    if bucket is None:
        bucket = []
    bucket.append(value)
    return bucket
```

适合直接作为默认值的通常是 None、数字、字符串、布尔值，以及内容也全部不可变的元组。元组本身虽然不可变，里面仍然可以放列表，所以不能只看最外层类型。

---

循环闭包默认采用晚期绑定

lambda 记住的是变量名，不是创建那一刻的数字；真正调用时才去取值。

```python
wrong = [lambda: i for i in range(3)]
print([func() for func in wrong])

fixed = [lambda i=i: i for i in range(3)]
print([func() for func in fixed])
```

第一行得到三个相同的最终值，第二行通过默认参数把每轮值固定下来。另一种更清晰的方案是写工厂函数，让每次调用都创建新的局部作用域。

---

property setter 写回同名属性会递归

错误结构：

```python
class Account:
    @property
    def password(self) -> str:
        return self.password

    @password.setter
    def password(self, value: str) -> None:
        self.password = value
```

getter 和 setter 内部再次访问 password，会再次进入 getter 或 setter，直到抛出 RecursionError。

正确结构使用独立的内部存储名：

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

如果业务不需要校验、延迟计算或兼容旧接口，直接使用公开属性通常更符合 Python 风格。

---

内部函数赋值会创建局部名称

只要函数体内出现赋值，Python 默认把该名称视为局部名称。因此下面代码读取 count 时，局部值还没有建立：

```python
def make_counter():
    count = 0

    def increment():
        count += 1
        return count

    return increment
```

运行 increment 会抛出 UnboundLocalError。修改外层函数变量应写 nonlocal count；重新绑定模块全局变量才使用 global。

---

不要遮蔽内置名称

```python
list = [1, 2, 3]
id = "asset-1"
```

这类赋值在语法上合法，但后续调用 list() 或 id() 会失败。常见高风险名称包括 list、dict、set、str、type、id、len、input、filter 和 sum。

可以使用 values、asset_id、item_type、total_length 等更具体的名称。发现遮蔽问题时，可先重命名变量，再重新启动交互式解释器，避免旧绑定继续存在。

---

分号不是语法错误，但不符合常规风格

Python 允许行尾分号，因此 `return "***";` 通常可以运行。问题不是语法错误，而是把 Java 习惯无意义地带进 Python，增加视觉噪声。普通 Python 代码直接省略分号。

---

append 与 extend 的粒度不同

```python
items = ["a"]
items.append(["b", "c"])
print(items)

items = ["a"]
items.extend(["b", "c"])
print(items)
```

append 把参数当一个元素，extend 遍历参数并逐项加入。对字符串使用 extend 会逐字符加入，通常不是想要的结果。

---

浅拷贝不会递归复制内部对象

```python
original = [[1], [2]]
copied = original.copy()
copied[0].append(99)
print(original)
```

外层列表不同，但内部列表仍被共享。真正需要递归复制时使用 copy.deepcopy；更好的做法往往是减少复杂可变共享结构。

---

等号与 is 的职责不同

等号调用值相等逻辑，is 判断两个引用是否指向同一对象。

```python
a = [1, 2]
b = [1, 2]
print(a == b)
print(a is b)
```

检查 None 使用 `value is None`。普通字符串、数字、列表和业务对象的值比较使用等号，不要依赖解释器的字符串驻留或小整数缓存。

---

字典直接索引与 get 表达不同契约

```python
record = {"name": "demo"}
required = record["name"]
optional = record.get("description")
```

方括号表示键必须存在，缺失就是程序或数据错误，应抛出 KeyError。get 表示键允许缺失。不要为了“避免报错”一律使用 get，否则可能把真正的数据问题拖到更远的位置。

如果 None 也是合法值，可使用哨兵对象区分“缺失”和“值为 None”：

```python
missing = object()
value = record.get("description", missing)
if value is missing:
    print("field is absent")
```

---

异常与返回状态要先定义契约

“限流器应该 raise 还是返回 False”没有统一答案。

- 如果超限是正常分支，调用方预计频繁判断，可返回布尔值或结果对象。
- 如果超限必须立刻中断当前操作，可抛出专门异常，例如 RateLimitExceeded。
- 在 Web API 层，可以把领域异常统一映射为 HTTP 429。
- 不要抛出过于宽泛的 Exception，也不要捕获后静默忽略。

Java 后端常见做法同样适用：领域层表达业务语义，边界层负责协议转换。

---

async def 不会自动让阻塞代码异步

下面代码会阻塞事件循环：

```python
import time


async def wrong():
    time.sleep(1)
```

异步等待应使用 asyncio.sleep。没有异步接口的阻塞函数可用 asyncio.to_thread 临时放入线程，但数据库、HTTP 客户端等应优先选择原生异步库。

CPU 密集计算放进 to_thread 也不会自动绕过默认 CPython 的 GIL。需要真并行时考虑进程池、原生扩展或专门的计算服务。

---

gather 并不等于事务或自动容错

asyncio.gather 负责并发等待多个 awaitable，但多个任务之间没有数据库事务语义。Python 3.11 及以上版本中，默认 gather 会把第一个异常立即抛给等待者，但不会自动取消其他任务；其他任务会继续运行。gather 自身被取消时，未完成任务才会一起取消。需要一个任务失败就取消其余任务时，优先使用 TaskGroup。

结构化并发场景可考虑 asyncio.TaskGroup。无论使用哪种方式，都应设置超时、处理取消，并确保每个任务独立持有不应共享的资源。

---

AsyncSession 不应跨并发任务共享

SQLAlchemy 的 Session 和 AsyncSession 都是有状态事务对象。可以把它类比为带事务状态的 Java EntityManager：每个并发任务一份。通常用依赖注入或 async with 控制生命周期。

如果把同一个 AsyncSession 同时交给多个 gather 任务，可能出现事务状态冲突、隐式 I/O 或难以定位的并发问题。

---

Windows 多进程必须保护入口

Windows 通常使用 spawn 启动子进程，子进程会重新导入主模块。如果进程池创建代码位于模块顶层，可能递归创建进程。

```python
def main() -> None:
    ...


if __name__ == "__main__":
    main()
```

提交多进程示例前，应至少在 Windows 上验证入口保护；库模块本身不应在导入时启动进程或执行耗时任务。

---

调试时先保存完整上下文

推荐顺序：

1. 阅读异常类型、消息和 traceback 最底部的直接原因。
2. 使用 repr 查看不可见字符和真实容器结构。
3. 用 type 和 isinstance 确认运行时类型。
4. 在最小复现中打印输入、边界值和关键分支。
5. 使用 breakpoint 进入调试器，检查局部变量和调用栈。
6. 把已确认的错误写成自动化测试，再修复实现。

日志不要记录密码、令牌、完整个人信息、浏览器会话或组织内部数据。异常日志也可能包含请求体和连接字符串，公开前必须检查。

---

提交前自查

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
