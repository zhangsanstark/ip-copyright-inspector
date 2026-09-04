知识点对照表

这份表按本次提供的知识范围整理，用来反查“详细解释在哪里”。它不表示已经覆盖 Python 和所有生态库的全部 API。语言与核心后端有独立运行例子；外部服务与选装生态的解释、示意和实际验证分开记录。

章节入口见 [总目录](README.md)，运行情况见 [验证记录](verification.md)。表中的节号是正文里的普通编号，不依赖放大的 Markdown 标题。

1）运行、值与输入输出

| 知识点 | 详细位置 | 重点核对 |
| --- | --- | --- |
| Python 文件、交互执行与缩进 | [01](01-runtime-values.md) 第 1 节 | 定义、执行、显示不是同一步 |
| int / float / str / bool / None、type | [01](01-runtime-values.md) 第 3 节 | 类型与可执行操作对应 |
| 变量、引用、id、is、等值 | [01](01-runtime-values.md) 第 2 节 | 改名字与改对象分开 |
| input 与类型转换 | [01](01-runtime-values.md) 第 4 节 | 正常读取是字符串，转换可能失败 |
| print、sep、end、file | [01](01-runtime-values.md) 第 5 节 | 输出格式不改变原值 |
| 百分号格式、format、f-string、精度 | [01](01-runtime-values.md) 第 5 节 | 格式化后的文本不等于数值精度变了 |
| 除法、取整、余数、乘方与浮点误差 | [01](01-runtime-values.md) 第 6 节 | 负数取整方向、合理比较浮点数 |
| if / elif / else、真假与短路 | [01](01-runtime-values.md) 第 7 节 | and/or 可能返回操作数 |
| while / for、break / continue、循环 else | [01](01-runtime-values.md) 第 8 节 | 每轮状态、结束条件 |

2）字符串不是只有几个常用方法

| 知识点 | 详细位置 | 重点核对 |
| --- | --- | --- |
| 引号、三引号、不可变、索引与 Unicode | [02](02-strings.md) 第 1 节 | 方法不原地改字符串，字符不等于字节 |
| find / rfind | [02](02-strings.md) 第 2 节 | 子串、范围、找不到的 -1 |
| index / rindex | [02](02-strings.md) 第 2 节 | 找不到抛异常，与 find 不同 |
| count、空子串与重叠匹配 | [02](02-strings.md) 第 2–3 节 | 不存在、空输入等边界 |
| replace 的旧值、新值、次数 | [02](02-strings.md) 第 4 节 | 普通替换不是正则 |
| split / rsplit、maxsplit | [02](02-strings.md) 第 5 节 | 显式分隔符和默认空白模式不同 |
| splitlines / partition / rpartition | [02](02-strings.md) 第 6 节 | 行边界、固定三项与未匹配情况 |
| join 与组合清洗过程 | [02](02-strings.md) 第 7 节 | 分隔符调用，元素需是字符串 |
| strip / lstrip / rstrip | [02](02-strings.md) 第 8 节 | chars 是字符集合，不是完整前后缀 |
| removeprefix / removesuffix | [02](02-strings.md) 第 8 节 | 精确删除一次前后缀 |
| lower / upper / swapcase | [02](02-strings.md) 第 9 节 | 大小写转换与 Unicode 边界 |
| capitalize / title / casefold | [02](02-strings.md) 第 9 节 | 改哪些字符、何时用于比较 |
| ljust / rjust / center / zfill | [02](02-strings.md) 第 10 节 | 最小宽度、填充、符号位置 |
| expandtabs | [02](02-strings.md) 第 10 节 | 制表位不是固定替换空格数 |
| startswith / endswith | [02](02-strings.md) 第 11 节 | 范围与多个候选前后缀 |
| isalpha / isalnum / isspace | [02](02-strings.md) 第 11 节 | 空字符串与非 ASCII 字符 |
| isdecimal / isdigit / isnumeric | [02](02-strings.md) 第 11 节 | 能判断成数字不代表 int 都能转换 |
| islower / isupper / istitle | [02](02-strings.md) 第 11 节 | 是否存在有大小写的字符 |
| isascii / isidentifier / isprintable | [02](02-strings.md) 第 11 节 | 标识符形式与关键字另行区分 |
| maketrans / translate / encode / decode | [02](02-strings.md) 第 12 节 | 文本映射、文本与字节的边界 |

3）列表、元组、字典、集合与通用操作

| 知识点 | 详细位置 | 重点核对 |
| --- | --- | --- |
| list 创建、下标与负索引 | [03](03-lists-tuples-copy.md) 第 1 节 | 有序、重复、越界 |
| append / extend / insert | [03](03-lists-tuples-copy.md) 第 2 节 | 整体添加与逐项展开 |
| pop / remove / del / clear | [03](03-lists-tuples-copy.md) 第 3 节 | 按位置、按值、返回值与删名字 |
| 下标修改、index / count / in / len | [03](03-lists-tuples-copy.md) 第 4 节 | 修改与查找的失败路径 |
| while / for 遍历、边遍历边删 | [03](03-lists-tuples-copy.md) 第 4 节 | 为什么会跳过元素 |
| sort / sorted / key / reverse | [03](03-lists-tuples-copy.md) 第 5 节、[08](08-lambda-sorting-reduce.md) 第 2 节 | 原地修改、稳定性与多条件 |
| reverse / reversed / 反向切片 | [03](03-lists-tuples-copy.md) 第 5 节 | 列表、新结果与迭代器不同 |
| 二维列表、copy / deepcopy、重复引用 | [03](03-lists-tuples-copy.md) 第 6 节 | 外层复制与内层共享 |
| tuple、单元素逗号、index / count / len | [03](03-lists-tuples-copy.md) 第 7 节 | 小括号不自动造元组 |
| 元组内部列表可变 | [03](03-lists-tuples-copy.md) 第 7 节 | 不能换元素不等于内部全冻结 |
| dict 创建、键可哈希、相等键 | [04](04-dicts-sets.md) 第 1 节 | 1、True、1.0 的键行为 |
| 字典插入顺序与按键读取 | [04](04-dicts-sets.md) 第 2 节 | 有顺序，但不是位置下标 |
| 方括号、get、默认值与 None | [04](04-dicts-sets.md) 第 3 节 | 缺键和显式空值分开 |
| 赋值增改、update、合并运算 | [04](04-dicts-sets.md) 第 4 节 | 原地修改或新对象 |
| del / pop / popitem / clear | [04](04-dicts-sets.md) 第 5 节 | 键不存在与最后插入项 |
| keys / values / items、遍历解包 | [04](04-dicts-sets.md) 第 6 节 | 视图不是快照 |
| setdefault / fromkeys / copy | [04](04-dicts-sets.md) 第 7 节 | 默认对象与浅拷贝共享 |
| set 创建、去重、无下标 | [04](04-dicts-sets.md) 第 8 节 | 空集合不是空字典 |
| add / update / remove / discard / pop / clear | [04](04-dicts-sets.md) 第 8 节 | 失败策略与任意元素弹出 |
| 交并差、对称差、子集超集、isdisjoint | [04](04-dicts-sets.md) 第 9 节 | 各种集合关系与更新变体 |
| frozenset | [04](04-dicts-sets.md) 第 10 节 | 不可变集合与哈希 |
| 加号合并、乘号重复、成员判断 | [05](05-slicing-iteration-comprehensions.md) 第 5.8–5.10 节 | 原地与新结果、零/负次数、引用重复、子串与整体成员 |
| len / del | [03](03-lists-tuples-copy.md) 第 3–4 节 | 容器长度、清空对象与解绑名字 |
| max / min 的两种形式、default、key | [05](05-slicing-iteration-comprehensions.md) 第 5.4–5.7 节 | 空输入、并列、混合类型与字典迭代 |

4）切片、zip、推导式与拆包

| 知识点 | 详细位置 | 重点核对 |
| --- | --- | --- |
| start / stop / step、包头不包尾 | [05](05-slicing-iteration-comprehensions.md) 第 1–2 节 | 正向、负索引、负步长分别考虑 |
| 省略、越界、反转、末尾截取 | [05](05-slicing-iteration-comprehensions.md) 第 1–2 节 | 反向时省略 stop 与显式 -1 不相同 |
| slice 对象、切片赋值与复制 | [05](05-slicing-iteration-comprehensions.md) 第 2–3 节 | 步长赋值数量约束与浅拷贝 |
| in / not in、迭代器消费 | [05](05-slicing-iteration-comprehensions.md) 第 4 节 | 成员检查也可能推进迭代器 |
| range / enumerate | [05](05-slicing-iteration-comprehensions.md) 第 5 节 | 不含 stop，start 是计数起点 |
| list / tuple / set 互转 | [05](05-slicing-iteration-comprehensions.md) 第 5 节 | 去重、顺序与信息丢失 |
| zip 按位配对、默认最短 | [05](05-slicing-iteration-comprehensions.md) 第 6 节 | 返回可耗尽的迭代器 |
| zip strict / zip_longest / zip 拆列 | [05](05-slicing-iteration-comprehensions.md) 第 6 节 | 长度校验、补值与展开顺序 |
| 列表推导式、筛选、三元替换 | [05](05-slicing-iteration-comprehensions.md) 第 7 节 | 后置 if 筛掉项，前置 if/else 换值 |
| 多 for、依赖外层、推导式作用域 | [05](05-slicing-iteration-comprehensions.md) 第 8 节 | 普通循环逐层展开 |
| 字典与集合推导式、生成器表达式 | [05](05-slicing-iteration-comprehensions.md) 第 9 节 | 重复键、去重和惰性区别 |
| 交换、字典解包、星号与双星号 | [05](05-slicing-iteration-comprehensions.md) 第 10 节、[06](06-functions-arguments.md) 第 4–6 节 | 定义处收集，调用处展开 |

5）函数、作用域与常用高级写法

| 知识点 | 详细位置 | 重点核对 |
| --- | --- | --- |
| 函数是一等对象、函数名与调用 | [06](06-functions-arguments.md) 第 1 节 | 传函数与传函数结果不同 |
| docstring、return、多值元组 | [06](06-functions-arguments.md) 第 1–2 节 | print 不等于返回，默认 None |
| 位置、关键字、默认参数 | [06](06-functions-arguments.md) 第 3 节 | 绑定次序、重复赋值、错误名字 |
| args / kwargs、透明转发 | [06](06-functions-arguments.md) 第 4 节 | 元组、字典、返回值不丢失 |
| 仅限位置、仅限关键字与参数顺序 | [06](06-functions-arguments.md) 第 3–5 节 | 普通位置规则与星号展开的区别 |
| 参数对象共享、id、可变与不可变 | [06](06-functions-arguments.md) 第 7 节 | 不是直接改调用方变量 |
| 可变默认参数、None 与哨兵 | [06](06-functions-arguments.md) 第 7 节 | 定义时求值，空列表不等于未传 |
| 递归、出口与调用栈 | [06](06-functions-arguments.md) 第 8–9 节 | 进入、等待、返回、深度限制 |
| 局部 / 全局 / LEGB | [07](07-scope-closures.md) 第 1–2 节 | 查找与绑定不是同一条规则 |
| global / nonlocal | [07](07-scope-closures.md) 第 2–3 节 | 模块绑定、最近外层函数绑定 |
| 无普通块级作用域、推导式区别 | [07](07-scope-closures.md) 第 4 节 | 分支没执行不等于变量也有值 |
| 闭包、独立实例、共享状态 | [07](07-scope-closures.md) 第 5 节 | 保存需要的绑定，不是外层一直运行 |
| 循环晚期绑定与 i=i 修复 | [07](07-scope-closures.md) 第 6–7 节 | 调用时读取、默认捕获仍可能共享对象 |
| lambda 参数形式与表达式 | [08](08-lambda-sorting-reduce.md) 第 1 节 | 普通 def 先行，不强行压缩复杂逻辑 |
| 多条件排序、元组键、局部降序 | [08](08-lambda-sorting-reduce.md) 第 2 节 | 单项 key 与稳定排序 |
| map 单/多输入、惰性 | [08](08-lambda-sorting-reduce.md) 第 3 节 | 转换结果、短输入与耗尽 |
| filter、真假、None 参数 | [08](08-lambda-sorting-reduce.md) 第 4 节 | 保留原元素，不是转换成 bool |
| reduce 完整参数与每轮返回 | [08](08-lambda-sorting-reduce.md) 第 5–9 节 | 初值、省略、空输入、单项、类型、顺序、漏 return |
| accumulate 与更直接的工具 | [08](08-lambda-sorting-reduce.md) 第 10 节 | 中间状态与最终结果分开 |
| 装饰器手动展开与 @ | [09](09-decorators.md) 第 1–2 节 | 装饰时与业务调用时分开 |
| wraps、函数名、说明、返回值 | [09](09-decorators.md) 第 3 节 | 保留元信息不等于自动修复逻辑 |
| 带参三层、叠加顺序 | [09](09-decorators.md) 第 4–5 节 | 配置、原函数、业务参数各由谁接 |
| 计时、缓存、重试与异常 | [09](09-decorators.md) 第 6–9 节 | finally、共享缓存、异步与幂等边界 |
| iter / next / 可迭代对象 / 迭代器 | [10](10-iterators-generators.md) 第 1–2 节 | 状态位置与一次性消费 |
| yield、return、yield from、表达式 | [10](10-iterators-generators.md) 第 3–5 节 | 逐步暂停恢复、流水线 |
| 内存、提前关闭、send | [10](10-iterators-generators.md) 第 6–8 节 | 按需不等于固定省内存或自动并发 |
| enter / exit、异常抑制 | [11](11-context-managers.md) 第 1–3 节 | 进入失败、退出失败与异常去向 |
| contextmanager、文件、锁与资源管理 | [11](11-context-managers.md) 第 4–8 节、[15](15-threads-processes-gil.md) 第 3 节 | 恰好一次 yield、finally、关闭与事务分开 |

6）对象与并发

| 知识点 | 详细位置 | 重点核对 |
| --- | --- | --- |
| 无 new 关键字、创建与 init、self | [12](12-objects-class-state.md) 第 1–2 节 | 创建方法仍有 `__new__`，初始化不返回新对象 |
| 类变量与实例变量 | [12](12-objects-class-state.md) 第 3 节 | 同名遮蔽与共享可变对象 |
| 实例/类/静态方法、同名重载 | [12](12-objects-class-state.md) 第 4 节 | Python 不是 Java 式签名重载 |
| 单下划线、双下划线名称修饰 | [12](12-objects-class-state.md) 第 5 节 | 约定不等于安全权限 |
| 万物皆对象、类与函数可传递 | [12](12-objects-class-state.md) 第 6 节、[06](06-functions-arguments.md) 第 1 节 | 类本身也是运行时对象 |
| 鸭子类型与 Protocol | [13](13-protocols-magic-property.md) 第 1 节 | 能力契约不等于只看方法名 |
| str / repr | [13](13-protocols-magic-property.md) 第 2 节 | 返回字符串与容器调试显示 |
| eq / hash | [13](13-protocols-magic-property.md) 第 3 节 | NotImplemented、哈希契约与可变对象 |
| call / len / getitem / slice | [13](13-protocols-magic-property.md) 第 4–5 节 | 对象调用、长度、整数和切片键 |
| property / setter、内部 _x | [13](13-protocols-magic-property.md) 第 6 节 | 初始化走校验、错误更新不污染状态、递归原因 |
| 多重继承、C3 MRO、super | [14](14-inheritance-mro-composition.md) 第 1–4 节 | 完整菱形过程、手工合并、协作传参 |
| Mixin 与组合 | [14](14-inheritance-mro-composition.md) 第 5–6 节 | 父类顺序与接口取舍 |
| GIL、CPU/I/O 密集选型 | [15](15-threads-processes-gil.md) 第 1–2 节 | 默认 CPython、扩展释放 GIL、可选自由线程环境 |
| 竞争条件、锁、线程池 | [15](15-threads-processes-gil.md) 第 3–4 节 | 复合动作不自动安全、结果与异常必须收集 |
| 多进程 Pool、入口保护、独立内存 | [15](15-threads-processes-gil.md) 第 5 节 | Windows spawn 与可传输任务 |
| Queue / Pipe / Redis 等 IPC 选择 | [15](15-threads-processes-gil.md) 第 6 节 | 本地消息实例与外部服务前提分开 |
| async / await / run / Task | [16](16-asyncio.md) 第 1–2 节 | 创建协程不等于调度执行 |
| gather / TaskGroup | [16](16-asyncio.md) 第 3–4 节 | 结果顺序、兄弟任务失败与取消不同 |
| 取消、超时与清理 | [16](16-asyncio.md) 第 5 节 | 不是立即强杀，也不是数据库回滚 |
| Semaphore / Queue / to_thread | [16](16-asyncio.md) 第 6–7 节 | 活跃数量、任务积压、阻塞 I/O 边界 |

7）工程化、生态与项目

| 知识点 | 详细位置 | 范围说明 |
| --- | --- | --- |
| 类型提示、容器与可空类型、函数类型 | [17](17-typing-pydantic.md) 第 1–3 节 | 包含泛型关联、Protocol、TypedDict 等，不把静态提示冒充运行校验 |
| Pydantic BaseModel / Field / v2 验证 | [17](17-typing-pydantic.md) 第 4–8 节 | 默认值、严格模式、字段/模型验证、序列化与错误 |
| FastAPI、Swagger、响应模型 | [18](18-fastapi-request-lifecycle.md) 第 1–4 节 | 请求路径、查询、JSON、422、输出校验 |
| Depends、lifespan、异步边界 | [18](18-fastapi-request-lifecycle.md) 第 5–7 节 | 含真实项目的隔离 TestClient 实验 |
| SQLAlchemy 2.0 async ORM | [19](19-sqlalchemy-transactions.md) 第 1–4 节 | 模型、会话、CRUD、结果读取 |
| flush / commit / rollback、并发会话 | [19](19-sqlalchemy-transactions.md) 第 5–8 节 | 隔离 SQLite 实验，不冒充所有数据库的压力验证 |
| Poetry / uv / pyproject / venv / lock | [20](20-packaging-uv-poetry.md) | 完整操作路线与命令含义，不自动更换管理工具 |
| pytest / fixture / mock / 排错 | [21](21-pytest-debugging.md) | 真实测试运行与故障分支验证 |
| Uvicorn / Gunicorn / Docker / Compose | [22](22-containers-deployment.md) | 配置解释与部署示意，不声称已构建或发布服务 |
| defaultdict / deque / Counter | [23](23-standard-library.md) | 参数、返回、变更行为与组合实例 |
| itertools / concurrent.futures | [23](23-standard-library.md)、[15](15-threads-processes-gil.md) | 迭代工具与线程/进程池分别展开 |
| NumPy / Pandas | [25](25-ecosystem.md) | 数据处理用途与选装示例，性能按数据与实现测量 |
| simhash / datasketch | [25](25-ecosystem.md) | 近似比较的输入、输出与适用边界 |
| Tortoise-ORM / Alembic | [25](25-ecosystem.md) | ORM 替代路线和结构迁移，不混用模型与会话体系 |
| Milvus / ChromaDB | [25](25-ecosystem.md) | 向量检索流程与外部组件前提 |
| Celery / Triton | [25](25-ecosystem.md) | 队列与推理服务职责，外部服务不自动启动 |
| 人员记录管理 | [24](24-practice-projects.md) 第 1 节 | CRUD、数据保护与测试 |
| CustomQueue | [24](24-practice-projects.md) 第 2 节 | 队列规则、索引、切片与边界 |
| Account | [24](24-practice-projects.md) 第 3 节 | 属性校验与显示遮罩示范，不是生产密码存储 |
| RequestLimiter | [24](24-practice-projects.md) 第 4 节 | 时间窗口、可注入时钟与边界测试 |

8）原来容易记偏的几句话，已按实际行为重新解释

- “字典无序”改为：保留插入顺序，但按键访问，不是按位置下标。
- “参数按引用传递”改为：名字接收对象引用；修改共享对象与重新绑定局部名字要分开。
- “所有位置参数和关键字参数绝不能穿插”补充：普通位置实参顺序受限，星号展开还有独立规则。
- “闭包必须被 return”改为：返回是常见保存方式，也可注册或存入容器；关键是引用并保留外层绑定。
- “i=i 把值锁死”补充：它创建默认参数，调用方仍可能覆盖；保存可变对象也不是深拷贝。
- “reduce 的函数只能定义两个参数”改为：每轮传两个位置实参，回调要能接住它们。
- “生成器固定省 90% 内存”改为：看输入、下游是否收集和实际测量，不保证固定比例。
- “多线程对 CPU 永远无效”补充：默认 GIL 环境、释放 GIL 的扩展和自由线程构建必须区分。
- “单线程 asyncio 固定能撑十万并发”改为：资源、协议、任务行为与系统限制共同决定容量。
- “Pydantic 自动返回 422”改为：Pydantic 抛验证错误，FastAPI 的请求处理层按其规则生成响应。
- “Python 行尾分号是语法错误”纠正：分号可以合法出现，通常省略以符合常见风格。
- “setter 遮住密码就安全”纠正：展示遮罩与真正的密码存储安全不是一件事。
- “限流必须抛异常”改为：返回 False 或抛异常取决于接口约定；调用方必须按约定处理。
- “with 都会关闭连接”补充：管理对象决定退出语义，事务退出与连接关闭有时分属不同层。
- “类变量就是 Java static 的全部行为”补充：Python 还有实例同名属性遮蔽与动态查找规则。

对照表用于发现缺口，不代替正文。后续新增或深化某个知识点时，应同时更新这里的位置与实际验证记录。
