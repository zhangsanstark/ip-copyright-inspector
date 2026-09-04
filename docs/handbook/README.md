Python 实用手册

这份手册面向有 Java 后端经验、希望把 Python 代码真正读顺并能独立写出来的读者。正文不压缩成术语清单：从一小段容易理解的代码开始，拆开参数、执行过程、返回结果，再讨论容易出错的情况。

全书使用普通字号，以 `1）` 和 `1.1` 区分知识点，不使用放大的标题。每章单独成文件，可以顺着读，也可以按问题查。旧的专题笔记仍保留在上一级目录，适合回看；本目录是更详细的正文。

1）基础篇：先把值、容器和循环读明白

- [01 运行、变量与基本类型](01-runtime-values.md)：从输入输出走到引用、真假、运算和循环，解释哪些 Java 习惯需要调整。
- [02 字符串](02-strings.md)：查找、替换、拆分、拼接、清理、大小写、对齐、判断、编码，逐组说明参数和边界。
- [03 列表、元组与复制](03-lists-tuples-copy.md)：全部常用增删改查、排序、二维数据、浅深拷贝与共享引用。
- [04 字典与集合](04-dicts-sets.md)：键与插入顺序、视图、缺失值、合并、集合运算和默认对象共享。
- [05 切片、遍历与推导式](05-slicing-iteration-comprehensions.md)：正负步长、zip 长度问题、拆包、普通循环与简写逐项对照。

2）函数篇：看清参数、状态与执行时机

- [06 函数、参数与递归](06-functions-arguments.md)：函数对象和调用、return、各类参数、对象共享、默认值、递归进入和返回。
- [07 作用域与闭包](07-scope-closures.md)：LEGB、global、nonlocal、循环晚期绑定、独立状态和可变对象捕获。
- [08 lambda、排序与高阶函数](08-lambda-sorting-reduce.md)：map/filter/reduce 从普通 for 走起，逐轮追踪累计值、空输入与错误返回。
- [09 装饰器](09-decorators.md)：不用 @ 先手动包装，再讲三层配置、多层顺序、wraps、计时、缓存与重试。
- [10 迭代器与生成器](10-iterators-generators.md)：next、yield、耗尽、暂停恢复、流水线、资源关闭、批处理与 send 选读。
- [11 上下文管理器](11-context-managers.md)：with 进入退出、异常去向、contextmanager、文件、ExitStack 和事务边界。

3）对象篇：把属性访问和方法查找拆开

- [12 对象与类状态](12-objects-class-state.md)：创建、初始化、self、类变量、实例变量、类方法、静态方法和名称修饰。
- [13 协议、魔术方法与 property](13-protocols-magic-property.md)：显示、相等、哈希、可调用对象、索引与切片、校验和无限递归。
- [14 继承、MRO 与组合](14-inheritance-mro-composition.md)：菱形调用链、C3 手算、super、协作初始化、Mixin 与组合取舍。

4）并发篇：不仅看能否同时跑，也看失败如何收尾

- [15 线程、进程与 GIL](15-threads-processes-gil.md)：竞争条件、锁、线程池、进程池、Windows 入口、IPC 和异常收集。
- [16 asyncio](16-asyncio.md)：协程、Task、await、gather、TaskGroup、取消、超时、并发限制与积压控制。

5）后端篇：从数据进入到服务运行

- [17 类型提示与 Pydantic](17-typing-pydantic.md)：提示和运行校验分工、字段规则、转换、验证器、嵌套与错误信息。
- [18 FastAPI 请求过程](18-fastapi-request-lifecycle.md)：路径、查询、请求体、响应、依赖、生命周期、同步异步边界和真实项目请求。
- [19 SQLAlchemy 异步与事务](19-sqlalchemy-transactions.md)：模型、引擎、会话、完整 CRUD、flush/commit/rollback、参数绑定和并发会话。
- [20 环境与依赖管理](20-packaging-uv-poetry.md)：解释器、venv、pip、pyproject、锁文件、uv、Poetry 与换一台电脑后的复现。
- [21 pytest 与排错](21-pytest-debugging.md)：断言、参数化、异常、fixture、mock、临时文件、故障测试与缩小问题范围。
- [22 容器与部署](22-containers-deployment.md)：Dockerfile 逐行、构建与启动、端口、卷、Compose、Uvicorn/Gunicorn 和部署前提。

6）工具与实战篇：把零散知识用起来

- [23 标准库](23-standard-library.md)：defaultdict、deque、Counter、itertools 与完整日志聚合例子。
- [24 四个完整小项目](24-practice-projects.md)：人员记录管理、CustomQueue、Account、RequestLimiter，含需求、实现、边界测试和扩展答案。
- [25 生态工具](25-ecosystem.md)：NumPy/Pandas、相似度方法、迁移、向量检索、任务队列与推理服务，区分小例子和服务前提。

原始范围逐项对应到哪里，见 [知识点对照表](coverage.md)。本次实际运行了什么、哪些部分没有实测，见 [验证记录](verification.md)。

7）怎样读，不容易又变成只记几个名词

每遇到例子，先遮住 assert 后面的期望值，自己猜结果。遇到 reduce、递归、闭包、生成器或异步，额外写下中间值与执行顺序；只猜最终数字还不够。

再改一个条件：列表变空、参数省略、输入重复、函数抛错、循环提前退出。能解释改动后为什么变化，比反复抄同一段更有帮助。

练习答案都在本章附近。先根据题意写一版，再核对；答案不是唯一写法，重点是约定、边界与返回结果是否一致。

部分章提前用到后面才细讲的语法，会说明用途或标为选读。基础篇遇到类、async 等不必停下来全弄懂，按导航到对应章补齐即可。

8）在本地运行整章例子

语言示例以 Python 3.11+ 为基础。后端相关例子需要本项目依赖；先在仓库根目录执行：

```powershell
uv sync --locked
uv run python scripts/check_handbook_examples.py --chapter 08 --show-output
```

没有 uv 时，先创建虚拟环境并安装项目依赖：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe scripts/check_handbook_examples.py --chapter 08 --show-output
```

纯语言与标准库章节可直接用已安装的 Python；17、18、19、21 等后端章节使用项目环境更稳妥。pip 这条安装命令按依赖范围解析，不等同于读取 uv.lock 的锁定安装。

只列出例子、不执行：

```powershell
uv run python scripts/check_handbook_examples.py --chapter 08 --list
```

按顺序运行多章，或全书：

```powershell
uv run python scripts/check_handbook_examples.py --chapter 06 07 08
uv run python scripts/check_handbook_examples.py
```

每块在独立 Python 子进程和临时工作目录运行，脚本会将仓库 src 加入模块路径。默认单块执行超时 40 秒，可用 `--timeout 60` 调整，之后另有最多 5 秒的进程清理等待窗口。成功或失败后都会收掉本次示例遗留的普通子进程，不适合用来启动常驻服务。Windows 进程示例已写入口保护，不要只复制函数体丢掉入口。

这个工具不是安全沙箱。只运行你信任的仓库代码；独立目录主要用于隔开状态和测试文件，不能限制代码的全部系统权限。

9）把例子变成可以随手修改的 .py 文件

例如只导出第 8 章，不运行它们：

```powershell
uv run python scripts/check_handbook_examples.py --chapter 08 --export .practice/08
uv run python .practice/08/hb08_reduce_first.py
```

在编辑器里打开 `.practice/08`，改数据、加 print、写自己的解法即可。导出器不会覆盖已有同名脚本；重复导出时换一个新目录，避免覆盖你已经改过的内容。

`.practice/` 已加入 Git 忽略，不会随普通提交把临时练习带上去。想保留自己的正式版本时，另存到明确的源码位置后再提交。

完整例子用 `# runnable:` 标记；不完整上下文片段用 `# fragment:`；需要选装包或外部服务的内容用 `# optional:`。后两类不会被自动运行或导出为已验证练习。Dockerfile、shell 与配置块也不会自动执行。

10）换另一台电脑后如何取得内容

首次克隆：

```powershell
git clone https://github.com/zhangsanstark/ip-copyright-inspector.git
cd ip-copyright-inspector
uv sync --locked
```

已有仓库时先 `git status` 看本地是否有修改，再按自己的分支状态更新；本地 main 没有未处理改动时可执行 `git pull --ff-only`。有修改先提交或妥善保存，不要用强制重置丢掉本地内容。

整个仓库是公开资料，不上传真实账号、令牌、私有数据或内部代码。项目中的相似度数字只表示技术比较结果，不是自动判断权利归属或合法性的依据。
