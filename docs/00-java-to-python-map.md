Java 后端转 Python 总览

有 Java 后端经验，很多概念其实已经熟悉了：对象、集合、接口、线程池、数据库事务。这里主要理清两件事：同一件事在 Python 里怎么写，以及哪些地方不能直接照搬 Java 的习惯。

这篇可以当入口用：1–2 看阅读顺序和 Java 对照，3–4 看容易理解错的地方，5–7 看动手方式、运行命令和版本范围。

---

1）从哪里开始看

1. [基础与容器](01-python-basics.md)：先把字符串、列表、字典、切片这些高频操作用顺。
2. [函数与常用写法](02-functions-pythonic.md)：接着看参数怎么传、变量在哪里找，再看闭包、装饰器和生成器。
3. [面向对象](03-object-oriented.md)：弄清 self、property、魔术方法和多重继承。
4. [并发](04-concurrency.md)：分清线程、进程、协程分别适合什么任务。
5. [后端工程](05-backend-engineering.md)：把请求校验、接口、数据库和测试串起来。
6. [动手路线](06-practice-roadmap.md)：按小任务改代码、运行、补测试。

遇到异常时翻 [常见问题](07-debugging-pitfalls.md)；想快速回想一个概念时翻 [记忆卡](08-memory-cards.md)。不必每次从第一篇重新看。

---

2）把熟悉的 Java 写法对照过来

下面是理解用的对照，不是一一对应的替换表。比如装饰器能做部分 AOP 的事，但它不等于 Java 的整套注解机制。

| Java 中熟悉的写法 | Python 中常见的写法 | 容易忽略的区别 |
| --- | --- | --- |
| 编译期静态类型 | 运行时动态类型加可选类型提示 | 类型提示主要服务编辑器、检查器和读者，默认不做运行时强制 |
| new User() | User() | 实例化不写 new，初始化通常进入 `__init__` |
| this | self | self 必须显式写在实例方法第一个参数位置 |
| interface | Protocol、抽象基类或鸭子类型 | 调用方通常关注对象能做什么，而不是它声明实现了什么 |
| getter 与 setter | property | 只在确实需要校验、兼容或计算属性时使用，不必机械封装 |
| try-with-resources | with 上下文管理器 | 成功进入 with 后，即使中途异常也会执行退出逻辑 |
| Stream | 推导式、生成器、itertools | 推导式偏可读转换，生成器偏惰性流水线 |
| Optional | `T \| None` | 比如 `str \| None` 表示可能得到字符串，也可能得到 None；它不是 Optional 包装对象 |
| record 或 DTO | dataclass、TypedDict、Pydantic 模型 | dataclass 偏内部数据结构，Pydantic 偏边界校验和序列化 |
| 注解加 AOP | 装饰器 | 装饰发生在函数定义完成时，本质是函数包装和重新绑定 |
| ExecutorService | concurrent.futures | 线程池和进程池有统一的 Future 风格接口 |
| CompletableFuture 或 Reactor | asyncio Task 和协程 | await 是显式挂起点，不能把阻塞调用直接塞进事件循环 |
| Maven 或 Gradle | pyproject.toml 配合 uv 或 Poetry | 依赖、项目元数据、构建和工具配置可集中在一个文件中 |
| JUnit | pytest | 常用普通 assert，fixture 负责准备与清理测试环境 |

---

3）几句话很容易记偏，顺手理清

3.1 字典有顺序，但不是靠位置取值

现代 Python 的 dict 会保留插入顺序。例如先放入 `name`，再放入 `age`，遍历时也是这个顺序。但 `user[0]` 查的是“键 0”，不是“第一个值”。想按名字查数据，用字典；想按第几个查数据，通常用列表。

3.2 join 关心的是元素类型，不是外层一定要是列表

`",".join(["a", "b"])` 得到 `"a,b"`，换成元组或生成器也可以，只要里面都是字符串。`",".join([1, 2])` 会报 TypeError，因为 join 不会替你把数字转成字符串；可以写 `",".join(str(x) for x in [1, 2])`。

3.3 global 管函数里的赋值，不等于“改全局数据都要写”

假设模块里有 `items = []`。函数中执行 `items.append(1)`，是在修改已有列表，通常不需要 global；执行 `items = [1]`，则默认会新建一个局部变量。如果希望赋值操作更新的是模块里的 items，就声明 `global items`。注意 `items += [1]` 虽然可能原地修改列表，但也包含赋值，同样需要这项声明。实际写业务代码时，优先通过参数传入、通过返回值交回，少依赖共享全局状态。

3.4 if 不隔开变量，推导式却有自己的范围

普通 if、for、while 不会像 Java 的花括号那样单独划出变量范围。在 if 里创建的变量，只要那一支真的执行了，后面就还能访问。Python 3 的推导式是个要单独记的地方：`[x * 2 for x in range(3)]` 里面的 x 不会作为循环变量留到外面。函数、类和模块也有各自的命名空间，具体查找规则看函数专题。

3.5 参数不止“四种”，还可以限制调用方式

普通调用先写位置参数，再写关键字参数，例如 `create_user(1, name="Ada")`。函数定义里的 `/` 和 `*` 还能规定：哪些参数只能按位置传，哪些必须写参数名。先用顺普通写法，再到函数专题看这些限制，不需要一次记完所有组合。

3.6 比较值用 ==，确认是不是同一个对象用 is

两个列表都装着 `[1, 2]`，它们的值可以相等，却未必是同一个列表。`==` 比内容，`is` 比对象身份，检查空值常写 `value is None`。`id()` 可以辅助观察对象身份，但它只在对象当前生命周期内有意义，不适合作为永久业务编号。

3.7 生成器省在“不提前装下全部结果”

如果要逐条处理一百万行数据，生成器可以取一条、处理一条，不必先建一个装着全部结果的大列表。但最后若又调用 `list(generator)`，所有结果还是会被收集起来。因此它可能大幅降低内存占用，却没有“固定节省 90%”这个保证。

3.8 asyncio 擅长等 I/O，不会凭空增加机器容量

一个请求等网络回复时，事件循环可以去推进其他任务，所以大量等待型任务适合 asyncio。但“十万连接”不是写上 async 就能达到：内存、文件描述符、数据库连接池、超时策略、框架和系统配置都可能成为限制。

3.9 讲 GIL 时，要带上解释器和任务类型

在通常启用 GIL 的 CPython 中，给纯 Python 计算增加线程，不能指望它随线程数成比例加速。Python 3.13 起还有可选的 free-threaded 构建，可以禁用 GIL；第三方扩展是否兼容、实际运行是否更快，要按环境验证。先记住常见环境下的选型，再根据实际测量调整，不把一句口诀套到所有 Python 环境。

---

4）这些习惯不要直接照搬

- 给每个字段都写 property。没有校验或计算需求时，直接访问属性往往更清楚。
- 把类型提示当成运行时校验，忘记在 API 边界使用 Pydantic 或显式校验。
- 用可变对象作为默认参数，导致多次调用共享同一个列表或字典。
- 在循环里创建 lambda 或闭包，却没有固定当轮变量，最终全部引用最后一个值。
- 在 async def 中直接执行阻塞数据库驱动、requests 或 time.sleep，卡住整个事件循环。
- 认为有 GIL 就不需要锁；多步读改写操作仍然会有竞态条件。
- 复用同一个 SQLAlchemy AsyncSession 给多个并发任务；会混淆事务状态且不是并发安全用法。
- 为了复用一点逻辑就加一层继承。先看看普通函数、组合或协议能不能把事情说清楚。
- 捕获 Exception 后什么都不做，导致问题被静默吞掉。
- 使用 list、dict、id、type 等名称作为变量，遮蔽内置对象。

---

5）看懂之后，怎样确认自己真的会用

看例子时觉得“这很简单”，和自己能写出来，是两回事。最有效的小检查是：先猜结果，再运行；结果不一样，就追到那一行看看变量到底发生了什么变化。

每次挑一个小点就够了：

1. 阅读一个概念和最小示例。
2. 不运行，先写出预期输出或异常类型。
3. 运行 examples 下的对应脚本。
4. 修改输入，使代码进入另一个分支。
5. 给关键函数补一个测试。
6. 用自己的话写三行：它怎么用、哪里容易错、什么时候会用到。

比如看完 append 和 extend，不急着往下翻。分别加入 `[3, 4]` 和 `"ab"`，先猜列表长度，再打印结果。能解释清楚为什么一个加了 1 个元素、另一个加了 2 个元素，这个差别就不容易混了。

---

6）换一台电脑，怎样运行这些例子

6.1 已经安装 uv

下面会克隆仓库、按锁文件安装依赖，然后运行测试并启动接口：

```powershell
git clone https://github.com/zhangsanstark/ip-copyright-inspector.git
Set-Location ip-copyright-inspector
uv sync --locked
uv run pytest
uv run uvicorn ip_copyright_inspector.main:app --reload
```

6.2 只有 Python 3.11 或更高版本

用 Python 自带的 venv 创建独立环境，再用 pip 安装项目依赖：

```powershell
git clone https://github.com/zhangsanstark/ip-copyright-inspector.git
Set-Location ip-copyright-inspector
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn ip_copyright_inspector.main:app --reload
```

6.3 只想运行一个基础例子

这些脚本只用标准库，不必先安装后端依赖。在仓库根目录执行：

```powershell
python examples\basics_lab.py
python examples\functions_lab.py
python examples\oop_lab.py
python examples\concurrency_lab.py
```

---

7）示例的版本和使用范围

仓库示例以 Python 3.11 及以上版本为目标。IP 文本相似度示例只演示 Python 和后端工程实践，输出是技术相似度指标，不是版权归属或侵权结论。
