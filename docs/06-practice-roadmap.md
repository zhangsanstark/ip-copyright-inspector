可执行练习路线

目标是从“代码看懂”前进到“能独立解释、修改、测试和排错”。每一步都尽量留下可验证输出，不把运行成功当成理解完成。

准备环境

- 安装 Python 3.11 或更高版本，确认 `python --version`。
- 安装 uv，确认 `uv --version`。
- 在仓库根目录运行 `uv sync`。
- 运行 `uv run pytest`，把基线测试结果保存到自己的终端记录。
- 运行 `uv run uvicorn ip_copyright_inspector.main:app --reload`。
- 打开 `/docs`，执行一次健康检查和一次文本比较。

验收标准：能解释 `.venv`、`pyproject.toml`、锁文件和 `uv run` 各自负责什么；能指出应用对象的模块路径。

记忆口诀：先同步，再测试，后启动；环境不对，代码白猜。

第一组：纯函数与集合

先只读 `similarity.py`，手算下面两组二元字符片段：

```text
abcd
abce
```

写出左右集合、交集、并集和最终分数，再运行：

```powershell
uv run python -c "from ip_copyright_inspector.similarity import compare_texts; print(compare_texts('abcd', 'abce', ngram_size=2))"
```

扩展练习：

- 比较 `知识产权保护` 与 `知识 产权保护`，解释为什么结果为 1。
- 比较 `aaaa` 与 `aa`，观察集合去重带来的信息损失。
- 把 `n` 从 1 调到 4，记录短文本分数如何变化。
- 为标点、全角英文和大小写各加一个测试。
- 实现一个保留空白的归一化选项，并说明它会怎样改变已有测试。

验收标准：能不用代码说清 Jaccard 公式；能说明该算法为何不等于语义相似度，更不等于法律结论。

记忆口诀：切片成集合，交集除并集；它只算重合，不负责裁决。

第二组：类型提示

给 `similarity.py` 中每个公共函数写出输入和输出类型，并回答：

- `set[str]` 与 `list[str]` 的语义差异是什么？
- 为什么结果使用不可变的 `dataclass`，而不是无结构的 `dict`？
- `str | None` 和“参数有默认值”是不是同一个概念？
- `Any` 与 `object` 对静态检查器的影响有何不同？

代码练习：定义一个 `SimilarityStrategy` 协议，要求实现 `compare(left: str, right: str) -> float`；再写一个类包装当前 Jaccard 函数。不要先修改 API，只写单元测试证明结构化鸭子类型可用。

验收标准：故意传入错误类型时，能解释为什么注解本身不会在运行时拦截，以及哪一层应该校验外部数据。

记忆口诀：类型提示管提醒，运行校验管进门。

第三组：Pydantic 2 边界校验

在 Python REPL 中分别执行：

```python
from ip_copyright_inspector.schemas import CompareRequest

print(CompareRequest.model_validate(
    {"left_text": " 甲 ", "right_text": "乙"}
).model_dump())
print(CompareRequest.model_json_schema())
```

然后构造五个失败请求：缺字段、纯空白、文本过长、`ngram_size=0`、额外字段。捕获 `ValidationError` 并打印 `errors()`。

扩展练习：

- 增加可选 `request_id`，使用 UUID 类型并观察 OpenAPI Schema。
- 将 `ngram_size` 改成 strict integer，验证字符串 `"3"` 是否还能通过。
- 写一个跨字段 `model_validator`，禁止左右文本完全相同；随后思考这条规则是否真的合理。
- 对比 `model_validate()`、`model_validate_json()` 和 `model_construct()`，指出最后一个为何危险。

验收标准：能区分 `Field` 约束、字段验证器和模型验证器的适用范围；验证器所有正常路径都返回值。

记忆口诀：简单边界交给 `Field`，复杂规则交给验证器，成功别忘返回值。

第四组：FastAPI 请求与响应

启动服务后，用 Swagger UI 和 PowerShell 各发送一次请求：

```powershell
$payload = @{
    left_text = "角色使用红色披风和圆形徽章"
    right_text = "红色披风角色佩戴星形徽章"
    ngram_size = 2
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/api/v1/comparisons" `
    -ContentType "application/json" `
    -Body $payload
```

观察状态码、响应字段和固定免责声明。再把 `ngram_size` 改为 9，阅读 422 响应的字段位置。

扩展练习：

- 增加 `GET /api/v1/comparisons/{record_id}`，查不到时返回 404。
- 为路由加入 `summary`、响应示例和明确的错误响应文档。
- 使用 FastAPI 依赖覆盖，为测试注入临时数据库会话。
- 给 `/docs` 是否在生产开放做一个配置开关。
- 让请求体超限在入口层尽早失败，比较应用字段限制与反向代理请求体限制的职责。

验收标准：能解释 400、404、422、500、503 在此服务中的不同语义；不会把所有异常都捕获成 200 加错误字符串。

记忆口诀：路由负责接线，状态码负责说真话。

第五组：异步与阻塞

在路由中分别实验 `await asyncio.sleep(1)` 与 `time.sleep(1)`，同时发出多个请求并观察区别。实验结束后恢复代码。

思考题：

- `async def` 为什么不会让 CPU 密集循环自动使用多核？
- 数据库驱动为什么也必须是异步版本？
- 哪些函数只是普通计算，不应该为了外观写成 `async def`？
- 同一个 `AsyncSession` 为什么不能交给多个 `asyncio.gather()` 子任务并发使用？

验收标准：能在代码审查中指出隐藏的阻塞调用；知道并发、并行、异步不是同义词。

记忆口诀：遇到 I/O 才 `await`，CPU 重活不会自动变快。

第六组：SQLAlchemy 2 异步 ORM

先删除练习环境中新生成的数据库文件，再重启服务，观察表被重新创建。只对本地练习数据库执行，不要操作任何共享或生产数据库。

扩展练习：

- 用 `select(ComparisonRecord)` 查询最近十条记录。
- 为 `created_at` 和 `score` 设计索引，并用查询场景说明理由。
- 把 `flush()` 和 `commit()` 前后的对象状态、`record.id` 打印出来，再单独调用一次 `refresh()`，观察它是“重新查询”而不是“专门生成主键”。
- 人为制造违反检查约束的写入，确认异常路径回滚后会话还能继续使用。
- 用临时 SQLite 数据库写一次真正的仓储集成测试。
- 引入 Alembic，生成第一份迁移，再增加一个可空列并生成第二份迁移。

验收标准：每个请求一个会话；事务成功才提交；失败明确回滚；原始文本仍不落库。

记忆口诀：一请求一会话，成功提交，失败回滚。

第七组：pytest 测试设计

从当前测试开始，把用例按下列层次扩展：

- 纯函数单元测试：不访问文件、网络或数据库。
- Schema 契约测试：覆盖有效输入、边界和失败输入。
- 路由测试：验证状态码、响应结构和依赖覆盖。
- 数据库集成测试：使用独立临时库验证事务与映射。

练习清单：

- 用 `@pytest.mark.parametrize` 合并重复边界用例。
- 用 `pytest.approx` 比较非精确浮点数。
- 使用 `tmp_path` 为每个测试创建隔离文件。
- 写一个先失败的测试，再实现功能让它通过，体验红、绿、重构循环。
- 故意让一个断言失败，阅读 pytest 如何展示差异，然后修复。

验收标准：测试可重复、互不依赖顺序，不使用真实生产地址，也不共享开发数据库。

记忆口诀：测试要独立，边界要覆盖，失败要能看懂。

第八组：uv、Poetry 与依赖可复现

uv 路线：

```powershell
uv lock
uv sync --locked
uv run pytest
uv tree
```

Poetry 路线：

```powershell
poetry install
poetry run pytest
poetry show --tree
```

在一个团队仓库内选择其中一条路线作为事实来源。练习读取 `pyproject.toml`，区分：

- `[project].dependencies` 是应用运行依赖。
- 开发组里的 pytest 只用于开发和测试。
- 版本范围表达兼容边界。
- 锁文件保存解析出的具体版本。
- 构建后端负责把 `src` 包装成可安装项目。

验收标准：换一台电脑只凭仓库内容能重建环境；不会把本机 `.venv` 提交；不会手工复制 site-packages。

记忆口诀：范围给选择，锁文件给答案，虚拟环境不进仓库。

第九组：Uvicorn 与 Docker

先用不同参数启动 Uvicorn：

```powershell
uv run uvicorn ip_copyright_inspector.main:app --host 127.0.0.1 --port 8001
uv run uvicorn ip_copyright_inspector.main:app --reload
```

解释 `127.0.0.1`、`0.0.0.0`、端口、reload 和 worker 的职责。确认开发用 reload，不把它带进生产命令。

容器练习建议：

- 写一个多阶段或缓存友好的 Dockerfile。
- 使用固定 Python 基础镜像版本，不依赖漂移的隐式环境。
- 以非 root 用户启动应用。
- 只复制锁文件和项目必需内容，使用 `.dockerignore` 排除 `.venv`、数据库和缓存。
- 添加 `/health` 健康检查，但区分存活与就绪。
- 通过环境变量注入 `DATABASE_URL`，不要把口令写入镜像层。

验收标准：能说明镜像、容器和进程的区别；能说明为什么单个容器中启动更多 worker 不等于整个系统已经高可用。

记忆口诀：镜像是模板，容器是实例，进程才真正跑代码。

第十组：把筛查原型推向可信服务

按风险优先级补齐：

- 身份认证和基于资源的授权。
- 请求大小、并发量和频率限制。
- 超时、取消传播和下游失败策略。
- Alembic 迁移与部署顺序。
- 结构化日志、请求关联 ID、指标和追踪。
- 敏感内容分级、加密、保留周期和删除流程。
- 阈值离线评估、误报漏报分析和人工复核队列。
- 依赖漏洞扫描、最小容器权限和密钥轮换。

算法实验可以增加 token Jaccard、编辑距离、TF-IDF 余弦相似度或向量模型，但每增加一种算法都要补充：确定的预处理、版本记录、标注数据、指标、阈值来源、回归测试和明确的非法律结论说明。

综合验收任务

独立完成一个小改动：“比较接口接受可选的算法版本名，并把版本写入记录与响应”。完成时应包含：

- Pydantic 输入与输出字段。
- 纯函数参数及默认行为。
- SQLAlchemy 字段和迁移。
- FastAPI 路由映射。
- 单元测试、Schema 测试和数据库集成测试。
- OpenAPI 示例与兼容性说明。
- 一条只描述技术筛查意义的免责声明。

最后做一次口头复盘：从 JSON 进入，到 Pydantic 校验、纯函数计算、SQLAlchemy 事务、响应序列化，再到 Uvicorn 发回 HTTP，每一步分别由哪个文件、哪个对象负责。能顺畅讲清这条链路，说明工程结构已经真正串起来了。
