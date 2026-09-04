Python 后端资料索引

以下仅收录项目或标准组织维护的一手文档。页面状态核对日期为 2026-08-27。具体版本行为仍应以项目锁文件和对应版本文档为准。

1）Python 类型与异步

- [Python typing 标准库文档](https://docs.python.org/3.11/library/typing.html)：类型注解的运行时地位、`Any`、`Protocol`、联合类型等。
- [Python asyncio 标准库文档](https://docs.python.org/3.11/library/asyncio.html)：事件循环、协程、task 和同步原语。
- [Python Unicode 规范化函数](https://docs.python.org/3.11/library/unicodedata.html#unicodedata.normalize)：示例相似度算法所用的 NFKC 归一化。

2）Pydantic 2

- [Pydantic 模型](https://docs.pydantic.dev/latest/concepts/models/)：`BaseModel`、数据转换、`model_validate()`、`model_dump()`、额外字段策略和 JSON Schema。
- [Pydantic 字段](https://docs.pydantic.dev/latest/concepts/fields/)：`Field` 的约束与元数据。
- [Pydantic 验证器](https://docs.pydantic.dev/latest/concepts/validators/)：字段和模型验证器、执行顺序与错误处理。
- [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)：需要关闭默认转换时的严格校验方式。
- [Pydantic 1 到 2 迁移指南](https://docs.pydantic.dev/latest/migration/)：方法重命名和行为变化。

3）FastAPI

- [FastAPI 请求体](https://fastapi.tiangolo.com/tutorial/body/)：Pydantic 请求模型、校验、JSON Schema 和自动文档。
- [FastAPI 字段约束](https://fastapi.tiangolo.com/tutorial/body-fields/)：通过 Pydantic `Field` 声明约束和元数据。
- [FastAPI 响应模型](https://fastapi.tiangolo.com/tutorial/response-model/)：响应校验、序列化、字段过滤与 OpenAPI。
- [FastAPI 依赖](https://fastapi.tiangolo.com/tutorial/dependencies/)：`Depends` 依赖图和 OpenAPI 集成。
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)：应用启动与退出期间的资源管理。
- [FastAPI async/await](https://fastapi.tiangolo.com/async/)：同步与异步路由选择、并发和阻塞 I/O。
- [FastAPI 错误处理](https://fastapi.tiangolo.com/tutorial/handling-errors/)：请求校验异常、自定义异常处理器和错误响应边界。
- [FastAPI 测试](https://fastapi.tiangolo.com/tutorial/testing/)：`TestClient` 与普通 pytest 测试写法。
- [Starlette TestClient](https://www.starlette.io/testclient/)：当前 TestClient 的上下文管理、lifespan 与 HTTPX2 依赖说明。
- [FastAPI 文档地址配置](https://fastapi.tiangolo.com/tutorial/metadata/#docs-urls)：OpenAPI、Swagger UI 与 ReDoc 默认入口及配置。

4）SQLAlchemy 2 异步 ORM

- [SQLAlchemy 2.0 asyncio 扩展](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)：异步引擎、连接、会话、并发 task 与隐式 I/O。
- [SQLAlchemy 2.0 ORM 快速开始](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)：`Mapped`、`mapped_column`、声明式映射和 `select()`。
- [SQLAlchemy Session 基础](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)：事务、会话生命周期，以及 Session/AsyncSession 的并发边界。
- [SQLAlchemy SQLite 方言](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#aiosqlite)：`sqlite+aiosqlite` 异步方言说明。
- [Alembic 官方教程](https://alembic.sqlalchemy.org/en/latest/tutorial.html)：生产数据库结构迁移的基础流程。

5）项目与依赖管理

- [uv 项目指南](https://docs.astral.sh/uv/guides/projects/)：`pyproject.toml`、项目环境、运行命令与构建。
- [uv 锁定与同步](https://docs.astral.sh/uv/concepts/projects/sync/)：`uv.lock`、`uv sync`、`uv run`、开发依赖组和 frozen/locked 行为。
- [uv Docker 集成](https://docs.astral.sh/uv/guides/integration/docker/)：容器构建缓存、锁文件和项目安装。
- [Poetry 基础用法](https://python-poetry.org/docs/basic-usage/)：`pyproject.toml`、虚拟环境、`poetry install`、`poetry run` 和锁文件。
- [Poetry 依赖组](https://python-poetry.org/docs/managing-dependencies/#dependency-groups)：主依赖与开发、测试等分组。
- [PEP 735](https://peps.python.org/pep-0735/)：`[dependency-groups]` 的标准格式与设计边界。

6）测试

- [pytest 入门](https://docs.pytest.org/en/stable/getting-started.html)：测试发现、普通断言和失败输出。
- [pytest fixture](https://docs.pytest.org/en/stable/explanation/fixtures.html)：可复用测试上下文、作用域和清理。
- [pytest 参数化](https://docs.pytest.org/en/stable/how-to/parametrize.html)：`pytest.mark.parametrize` 的官方用法。
- [pytest 临时目录](https://docs.pytest.org/en/stable/how-to/tmp_path.html)：`tmp_path` 与测试文件隔离。

7）运行与部署

- [Uvicorn 设置](https://www.uvicorn.org/settings/)：应用导入字符串、host、port、reload 和 worker 配置。
- [Uvicorn 部署](https://www.uvicorn.org/deployment/)：开发与生产运行模式、进程管理和代理部署注意事项。
- [Uvicorn Docker 指南](https://www.uvicorn.org/deployment/docker/)：缓存友好镜像、单 worker 容器和非 root 用户建议。
- [Docker 构建镜像](https://docs.docker.com/get-started/docker-concepts/building-images/)：Dockerfile、镜像层与构建缓存基础。
- [Docker 多阶段构建](https://docs.docker.com/build/building/multi-stage/)：减小运行镜像和分离构建环境。
- [ASGI 规范](https://asgi.readthedocs.io/en/latest/specs/main.html)：应用、服务器、scope、receive 和 send 的接口边界。

8）相似度方法

- [SciPy Jaccard 距离文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.jaccard.html)：Jaccard 距离定义和布尔向量形式。仓库代码直接实现集合相似度，没有依赖 SciPy。

9）资料使用原则

- 先按仓库锁定版本阅读对应版本文档，再参考 latest 页面。
- 教程片段用于理解，不直接替代安全、容量、隐私和迁移设计。
- 相似度指标只能作为技术筛查信号，不能从公式直接推出侵权、权属或许可结论。
