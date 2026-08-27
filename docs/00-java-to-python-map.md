Java 后端转 Python 总览

这份总览先看 Java 中熟悉的写法在 Python 里怎么落地，再进入各专题。不要逐字翻译语法，先弄清 Python 平时怎样组织对象、循环数据和处理异步任务。

---

建议阅读顺序

1. 先读 01-python-basics.md，补齐容器、切片、推导式和迭代协议。
2. 再读 02-functions-pythonic.md，重点掌握参数、闭包、装饰器、生成器和上下文管理器。
3. 继续读 03-object-oriented.md，理解鸭子类型、魔术方法、property 和 MRO。
4. 然后读 04-concurrency.md，区分并发、并行、线程、进程和协程。
5. 最后读 05-backend-engineering.md，并运行仓库中的 API 示例项目。
6. 按 06-practice-roadmap.md 完成分阶段练习，不要只看代码不运行。

---

Java 与 Python 的常用概念映射

| Java 习惯 | Python 对应思路 | 需要改变的认知 |
| --- | --- | --- |
| 编译期静态类型 | 运行时动态类型加可选类型提示 | 类型提示主要服务编辑器、检查器和读者，默认不做运行时强制 |
| new User() | User() | 实例化不写 new，初始化通常进入 `__init__` |
| this | self | self 必须显式写在实例方法第一个参数位置 |
| interface | Protocol、抽象基类或鸭子类型 | 调用方通常关注对象能做什么，而不是它声明实现了什么 |
| getter 与 setter | property | 只在确实需要校验、兼容或计算属性时使用，不必机械封装 |
| try-with-resources | with 上下文管理器 | 成功进入 with 后，即使中途异常也会执行退出逻辑 |
| Stream | 推导式、生成器、itertools | 推导式偏可读转换，生成器偏惰性流水线 |
| Optional | T 或 None | None 是值，类型提示常写成 str 或 None |
| record 或 DTO | dataclass、TypedDict、Pydantic 模型 | dataclass 偏内部数据结构，Pydantic 偏边界校验和序列化 |
| 注解加 AOP | 装饰器 | 装饰发生在函数定义完成时，本质是函数包装和重新绑定 |
| ExecutorService | concurrent.futures | 线程池和进程池有统一的 Future 风格接口 |
| CompletableFuture 或 Reactor | asyncio Task 和协程 | await 是显式挂起点，不能把阻塞调用直接塞进事件循环 |
| Maven 或 Gradle | pyproject.toml 配合 uv 或 Poetry | 依赖、项目元数据、构建和工具配置可集中在一个文件中 |
| JUnit | pytest | 常用普通 assert，fixture 负责准备与清理测试环境 |

---

必须修正的几个简化说法

字典不是“完全无序”。现代 Python 的 dict 保留插入顺序，但读取数据仍应依赖键，不应把业务正确性建立在偶然位置上。需要按位置访问时，应显式转换或设计为序列。

join 不只接受 list 和 tuple。它接受由字符串组成的任意可迭代对象；只要其中出现非字符串元素，就会抛出 TypeError。数字拼接前应先转换为字符串。

global 处理的是名称绑定。函数内如果要让全局名称重新指向另一个对象，需要声明 global；如果只是调用全局列表的 append，通常不需要 global，但共享可变状态仍然不推荐。

Python 没有普通 if、for、while 块级作用域，但 Python 3 的推导式有自己的局部作用域。函数、类和模块也各自形成不同的命名空间。

位置实参通常必须写在关键字实参之前，但参数系统比“四种参数”更完整。函数定义还可以使用斜杠声明仅限位置参数，使用星号声明仅限关键字参数。详细规则放在函数专题中。

id 返回对象在当前生命周期内的身份标识，不应当作永久业务编号。判断 None 等单例使用 is，比较业务值使用等号。

生成器能显著降低峰值内存，但“节省 90%”不是语言保证。真实收益取决于数据规模、流水线是否保持惰性，以及结果是否最终又被完整收集进列表。

asyncio 能支撑大量 I/O 并发，但“十万连接”不是无条件保证。上限还受文件描述符、内存、连接状态、框架、数据库连接池、超时策略和操作系统配置影响。

默认 CPython 构建通常仍启用 GIL，因此纯 Python 的 CPU 密集代码不会因为增加线程就线性加速。Python 3.13 起存在可选的 free-threaded 构建，可禁用 GIL，但第三方扩展兼容性和运行开销仍需按实际环境验证。

---

从 Java 思维切换时最常见的错误

- 把每个字段都写成 property，导致代码只有样板而没有约束价值。
- 把类型提示当成运行时校验，忘记在 API 边界使用 Pydantic 或显式校验。
- 用可变对象作为默认参数，导致多次调用共享同一个列表或字典。
- 在循环里创建 lambda 或闭包，却没有固定当轮变量，最终全部引用最后一个值。
- 在 async def 中直接执行阻塞数据库驱动、requests 或 time.sleep，卡住整个事件循环。
- 认为有 GIL 就不需要锁；多步读改写操作仍然会有竞态条件。
- 复用同一个 SQLAlchemy AsyncSession 给多个并发任务；会混淆事务状态且不是并发安全用法。
- 过度依赖继承层次，忽略组合、协议和小型可测试函数。
- 捕获 Exception 后什么都不做，导致问题被静默吞掉。
- 使用 list、dict、id、type 等名称作为变量，遮蔽内置对象。

---

推荐的练习方式

每个专题按同一循环练习：先预测输出，再运行代码，然后故意制造错误，最后写一个小改动证明自己理解了原因。

示例流程：

1. 阅读一个概念和最小示例。
2. 不运行，先写出预期输出或异常类型。
3. 运行 examples 下的对应脚本。
4. 修改输入，使代码进入另一个分支。
5. 给关键函数补一个测试。
6. 用自己的话写三行结论，记录“规则、反例、适用场景”。

---

新电脑上的推荐运行方式

如果已经安装 uv：

```powershell
git clone https://github.com/zhangsanstark/ip-copyright-inspector.git
Set-Location ip-copyright-inspector
uv sync --locked
uv run pytest
uv run uvicorn ip_copyright_inspector.main:app --reload
```

如果只有 Python 3.11 或更高版本：

```powershell
git clone https://github.com/zhangsanstark/ip-copyright-inspector.git
Set-Location ip-copyright-inspector
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn ip_copyright_inspector.main:app --reload
```

运行单个标准库练习不需要安装项目依赖：

```powershell
python examples\basics_lab.py
python examples\functions_lab.py
python examples\oop_lab.py
python examples\concurrency_lab.py
```

---

版本与边界说明

仓库示例以 Python 3.11 及以上版本为目标。IP 文本相似度示例只演示 Python 和后端工程实践，输出是技术相似度指标，不是版权归属或侵权结论。
