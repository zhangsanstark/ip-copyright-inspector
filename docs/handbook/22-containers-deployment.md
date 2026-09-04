容器与部署：把代码、环境和运行方式一起说明白

本章只提供部署示意和本地检查，不构建镜像、不启动 Docker 服务、不发布接口。容器配置能帮助复现运行方式，但“容器启动了”不等于鉴权、备份、监控和网络安全都已经准备好。

阅读导航：1 镜像与容器；2 Dockerfile；3 构建与启动；4 端口；5 配置与数据；6 Compose；7 服务器与 worker；8 三道练习；9 上线前检查与资料。

Python runnable 只验证配置、路径和进程边界，不需要 Docker。可执行 `python scripts/check_handbook_examples.py --chapter 22 --show-output`。

1）镜像、容器、卷：三个东西的寿命不同

1.1 镜像是构建好的文件与默认配置

镜像里面可以包含 Python、已安装依赖、项目代码和默认启动命令。构建完成以后，它可以作为创建容器的基础。

同一个镜像可以启动多个容器。修改其中一个运行容器里的文件，不会自动修改原镜像，也不会自动同步到其他容器。

把它和 Java 部署对照：jar 只是应用产物；容器镜像还可以一起描述运行时和系统层依赖。但容器仍与宿主机共享相应内核能力，不是完全独立的虚拟机。

1.2 容器是基于镜像启动的一次运行实例

容器有自己的进程、网络环境和可写层。主进程退出以后，容器的运行状态也会结束；不是 Dockerfile 中写过 CMD 就永远有服务可用。

停止容器与删除容器不同。停止后还可以重新启动；删除容器会移除它自己的可写层，里面没有另行持久化的数据可能随之丢失。

1.3 卷把需要保留的数据放到容器生命周期之外

数据库文件不应只放在临时容器的可写层里。命名卷可以在容器重建后继续挂载使用；bind mount 则把宿主机指定路径直接挂进容器。

两者都不是自动备份。误写、误删、坏数据和宿主机故障仍可能影响它们。持久化回答“重建容器后还在不在”，备份回答“出问题后能不能恢复到以前”。

2）一份对应本仓库的 Dockerfile 示意

2.1 先看完整内容，再逐行解释

以下配置以 Linux Python 镜像为例。若要实际验证，应另行保存为 Dockerfile，并确认 Docker 可用、网络可下载镜像与依赖。本章没有把它写入项目配置，也没有执行构建。

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

RUN mkdir -p /data && chown 10001:10001 /data
USER 10001:10001

ENV DATABASE_URL=sqlite+aiosqlite:////data/comparisons.db
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "ip_copyright_inspector.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

这是帮助理解的基础方案：使用 pip 按 pyproject 范围安装，并没有读取 uv.lock；基础镜像标签也可变化。因此它不能被称为严格固定依赖的生产构建方案。

真正要固定构建结果，应选定并记录基础镜像 digest，按项目锁文件安装运行依赖，并在目标平台构建和测试。不要捏造一个看起来精确、实际没有验证过的 digest。

2.2 FROM 与 WORKDIR：运行环境和相对路径从哪里开始

`FROM python:3.12-slim` 选择基础镜像。这里的 3.12 是例子所选的 Python 系列，不代表最新，也不代表某个固定补丁版本。

`WORKDIR /app` 为后续指令与默认运行命令设置工作目录。它影响相对路径，例如 `./demo.db` 会相对于这个目录解释。

主机上的 `C:\...` 路径不会原样出现在 Linux 容器里。容器路径 `/app`、`/data` 与宿主机路径是两个视角，通过复制或挂载建立联系。

2.3 COPY 与 RUN：构建时做什么

`COPY pyproject.toml ./` 把项目元数据复制到 `/app`；`COPY src ./src` 复制源码。示例没有把 `.git`、本地虚拟环境、数据库或凭据一起复制进去。

`RUN python -m pip install --no-cache-dir .` 在构建时安装当前项目及运行依赖。它不是每次容器启动都重新安装。

这里 `--no-cache-dir` 控制 pip 下载缓存，不等于禁用 Docker 构建缓存，也不意味着所有重复构建都重新下载基础镜像。

如果项目以后增加构建所需的 README、资源文件或其他目录，需要相应调整 COPY；不能假设只复制 src 永远够用。

2.4 USER 与目录权限：不让服务默认以 root 运行

构建时创建 `/data`，把它交给数值用户和组 10001；之后 `USER` 指定运行身份。进程仍可读取已安装代码，但需要把可写数据放到它有权限的目录。

挂载宿主机目录后，原镜像目录权限可能被挂载内容替代。出现只读数据库或 permission denied，先检查挂载路径和权限，不要立即把整个服务改回 root。

非 root 只是安全措施之一，不等于容器没有风险。镜像来源、依赖漏洞、网络暴露和宿主机权限同样需要检查。

2.5 ENV、EXPOSE、CMD：默认配置与启动方式

`PYTHONDONTWRITEBYTECODE=1` 避免运行时写 `.pyc`；`PYTHONUNBUFFERED=1` 让标准输出更及时地到达日志收集端。它们不改变业务算法。

`EXPOSE 8000` 记录应用预期使用的端口，不会自动把宿主机端口公开出去。实际发布端口由 docker run 或 Compose 控制。

CMD 的 JSON 数组形式直接指定程序及参数，避免无意增加一层 shell。这里主程序就是 Python 启动的 Uvicorn，停止信号的传递也更清楚。

2.6 .dockerignore 不是 .gitignore 的自动复制品

构建上下文里哪些文件发给构建器，由 `.dockerignore` 控制；Git 忽略规则不会自动替它完成同样的过滤。

可考虑排除 `.git`、`.venv`、缓存、数据库、`.env`、私钥和本地临时文件。需要注意：先把秘密 COPY 进镜像，再在下一层删除，不等于秘密从历史层中消失。

3）build 与 run：两个阶段不要混

3.1 build 得到镜像，并不启动 API

下面命令是假设已经保存了上一节 Dockerfile 之后的操作示意，不是本章已执行的动作。

```powershell
docker build -t ip-copyright-inspector:demo .
```

`-t` 给镜像一个名称与标签。最后的点是构建上下文目录，不是“随便可省略的标点”。COPY 读取的文件来自这个上下文。

构建成功后，可以从同一镜像创建容器。源码修改不会自动进入旧镜像，需要重新构建，或者在明确的本地调试方案中使用 bind mount。

3.2 run 创建并启动一个容器

```powershell
docker run --name inspector-demo --rm -p 127.0.0.1:8000:8000 --mount type=volume,source=inspector-demo-data,target=/data ip-copyright-inspector:demo
```

`--name` 指定容器名；`--rm` 在容器退出后删除这个容器实例；`--mount` 把命名卷挂到 `/data`；最后是镜像名称。

这里没有 `-d`，日志留在前台，便于观察启动。`--rm` 不会把显式指定的命名卷一起当作容器可写层删除；不要因此误以为所有类型的挂载都具有完全相同的删除行为。

同名容器已经存在时会发生冲突。先用 `docker ps -a` 查看，不要为了启动一次演示而无差别删除所有容器。

3.3 日志与停止都是运行管理的一部分

```powershell
docker ps
docker logs inspector-demo
docker stop inspector-demo
```

第一条查看运行容器；第二条查看标准输出与错误日志；第三条请求停止指定容器。带 `--rm` 的演示容器退出后会被删除，因此之后不能再把它当作仍存在的日志对象。

4）端口有三层：监听地址、容器端口、宿主机端口

4.1 为什么容器内监听 0.0.0.0，宿主机却绑定 127.0.0.1

容器内 Uvicorn 的 `--host 0.0.0.0` 表示接受容器网络接口上的连接。只监听容器自己的 127.0.0.1，可能让端口转发无法到达服务。

`-p 127.0.0.1:8000:8000` 里的第一个地址，则限制宿主机在回环地址上发布端口。它的目的不同：保持这个演示只供本机访问。

如果省略宿主机绑定地址，端口可能发布到更广的网络接口。是否可从外部访问还与网络和防火墙有关，但不能默认它仍然只在本机可见。

4.2 8001:8000 不会把容器里的程序改成监听 8001

它表示宿主机 8001 转发到容器 8000。客户端在宿主机访问 8001；容器内部的 Uvicorn 仍监听 8000。

容器里的 `localhost` 通常指容器自身，不是宿主机，也不是另一个数据库容器。Compose 中服务间连接应使用相应服务名称与容器端口，不要机械套宿主机浏览器地址。

```python
# runnable: hb22_port_meaning
from ipaddress import ip_address

mapping = "127.0.0.1:8001:8000"
host_address, host_port, container_port = mapping.split(":")
assert ip_address(host_address).is_loopback
assert int(host_port) == 8001
assert int(container_port) == 8000
assert host_port != container_port
print("宿主机访问 8001，转发到容器 8000")
```

这个拆分代码仅用于该 IPv4 示例，不是通用 Docker 端口语法解析器。IPv6、范围端口和协议后缀需要其他解析规则。

5）环境变量和数据库文件：配置与数据不要塞回源码

5.1 环境变量在进程启动时交给程序

Dockerfile 的 ENV 提供默认值，运行时可用 `-e NAME=value` 覆盖。仓库的 DATABASE_URL 在模块导入时读取，因此应在进程启动前设置。

程序启动后在另一个终端改环境变量，不会神奇地更新已经运行的进程。即使在同一进程改 os.environ，也不代表已创建的数据库引擎自动重建。

`.env` 只是常见配置文件格式，不是 Python 自动读取的语言特性。是否加载它，取决于启动工具和代码。不要把本地 `.env` 推到公开仓库。

5.2 相对 SQLite URL 与绝对路径的斜杠不同

`sqlite+aiosqlite:///./demo.db` 使用相对文件路径。Linux 容器中 `sqlite+aiosqlite:////data/demo.db` 指向绝对路径 `/data/demo.db`。

```python
# runnable: hb22_database_url
from sqlalchemy.engine import make_url

relative = make_url("sqlite+aiosqlite:///./demo.db")
absolute = make_url("sqlite+aiosqlite:////data/demo.db")
assert relative.database == "./demo.db"
assert absolute.database == "/data/demo.db"
assert absolute.drivername == "sqlite+aiosqlite"
print("相对：", relative.database, "绝对：", absolute.database)
```

先确认程序实际写入 `/data`，再确认卷确实挂到 `/data`。只建立一个命名卷，却让数据库仍写在 `/app`，不会自动得到你期待的持久化。

6）Compose：把一组启动参数写成可重复检查的配置

6.1 一个服务也可以使用 Compose

下面是 `compose.yaml` 示意，需要保存对应文件后才可使用。它沿用前面的 Dockerfile，仍只是本地单实例实验，不是完整生产部署。

```yaml
services:
  api:
    build: .
    init: true
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      DATABASE_URL: "sqlite+aiosqlite:////data/comparisons.db"
    volumes:
      - inspector-data:/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).close()"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 10s

volumes:
  inspector-data:
```

`services.api` 描述一个服务；`build` 说明镜像如何构建；`ports` 描述发布关系；`environment` 传入配置；服务里的 volumes 负责挂载，最下面的 volumes 声明命名卷。

healthcheck 在容器内部访问自己的健康接口，不依赖宿主机端口。当前 `/health` 只返回应用健康信息，不能因此断言数据库所有读写路径都正常。

6.2 先解析配置，再启动

```powershell
docker compose config
docker compose up --build
docker compose ps
docker compose logs api
docker compose down
```

`config` 检查并展开配置；`up --build` 根据配置构建并启动；`ps` 查看状态；`logs` 看指定服务日志；`down` 停止并移除这组容器和相应网络。

普通 down 通常保留命名卷。追加 `--volumes` 会涉及卷删除，可能把数据库数据一起删除；因此这里不把它放进日常复制命令。

健康状态被标为 unhealthy，并不等于 Docker 一定自动重启容器。健康检查、重启策略和外部编排的处理规则是不同机制，需要分别配置与验证。

6.3 Compose 数据持久化不解决多副本数据库架构

把多个 API 容器都指向同一个 SQLite 文件，并不会自动得到适合高写入并发的数据库集群。卷共享、锁和文件系统语义都需要考虑。

要扩展到独立数据库服务，还要配置驱动、连接地址、凭据、迁移、连接池和恢复方案。不是把 `sqlite` 字符串换成另一个数据库名就完成了。

7）Uvicorn、Gunicorn 与 worker：到底是谁在运行应用

7.1 Uvicorn 是 ASGI 服务器，FastAPI 是应用框架

客户端发来 HTTP 请求，由服务器接收并按 ASGI 协议交给应用。FastAPI 负责路由、依赖与模型处理。两者不是彼此的别名。

Uvicorn 可以直接运行，也支持多个 worker 进程。Windows 本地一般可以直接使用 Uvicorn；并不需要为了写一个接口先安装 Gunicorn。

`--reload` 与 `--workers` 不应组合成“既自动重载又正式多进程”的万能启动方式。重载用于本地修改迭代，多进程数量应按真实资源与负载验证。

7.2 Gunicorn 的平台与 worker 类型需要明确

Gunicorn 是面向 UNIX 的服务器与进程管理方案，不应把原生 Windows 当作它的常规运行平台。需要这条路线时可在适合的 Linux 环境验证。

FastAPI 是 ASGI 应用，不能不看版本和 worker 类型就照搬传统 WSGI 启动命令。Gunicorn 不同版本的 ASGI 支持有变化，应查当前选定版本文档。

下面展示独立 `uvicorn-worker` 包的用法。前提是已在对应 Linux 环境安装并锁定兼容的 Gunicorn 与 uvicorn-worker；仓库当前没有把它们作为运行依赖，因此这不是直接可用的项目命令。

```text
gunicorn ip_copyright_inspector.main:app -w 2 -k uvicorn_worker.UvicornWorker --bind 0.0.0.0:8000
```

Uvicorn 文档已说明旧的 `uvicorn.workers` 模块被弃用，独立包的导入路径是 `uvicorn_worker`。看到旧教程时先核对版本，不要同时安装一堆 worker 类再靠试错选一个。

7.3 worker 数量也会放大内存与连接数量

每个 worker 是独立进程，普通 Python 全局字典不是跨 worker 共享的数据库。一个进程里写入缓存，另一个进程不会自动看见。

每个进程也可能各自建立数据库引擎和连接池。假设一个进程最多使用 5 个连接，4 个进程的上限预算就可能达到 20，还没算额外任务和其他服务。

多 worker 不是越多越快。CPU、内存、数据库连接和 SQLite 写锁可能先成为瓶颈。应通过压测与监控选择，而不是死背“核数乘二再加一”。

8）三道练习，答案不需要启动容器

8.1 练习一：确认子进程拿到配置，但父进程不被改写

要求：给一个新 Python 进程传 `HB22_MODE=container-demo`，验证它读到了值；父进程原有环境保持不变。

```python
# runnable: hb22_answer_environment
import os
import subprocess
import sys

before = os.environ.get("HB22_MODE")
environment = os.environ | {"HB22_MODE": "container-demo"}
result = subprocess.run(
    [sys.executable, "-c", "import os; print(os.environ['HB22_MODE'])"],
    env=environment, capture_output=True, text=True, check=True,
)
assert result.stdout.strip() == "container-demo"
assert os.environ.get("HB22_MODE") == before
print("配置属于启动的进程环境，不会反向修改父进程")
```

这与容器运行时传环境变量的基本方向一致：启动方给新进程提供配置。它没有模拟容器隔离，只核对环境传递本身。

8.2 练习二：算出连接预算，拒绝只看单进程配置

要求：3 个 worker，每个基础池 4、最多额外 2，计算所有 worker 的最大连接预算为 18。再计算扩到 5 个 worker 的结果。

```python
# runnable: hb22_answer_connection_budget
def connection_budget(workers: int, pool_size: int, max_overflow: int) -> int:
    if workers < 1 or pool_size < 1 or max_overflow < 0:
        raise ValueError("此简化预算要求正 worker、正池大小、非负额外连接")
    return workers * (pool_size + max_overflow)

assert connection_budget(3, 4, 2) == 18
assert connection_budget(5, 4, 2) == 30
print("增加 worker 也会增加连接预算")
```

这是针对“每个进程都有相同有界连接池”的简化估算，不代表本仓库 SQLite 配置自动使用这些数值。真实系统还需考虑池实现、其他进程和数据库最大连接数。

8.3 练习三：区分持久化目录与应用目录

要求：三个候选数据库路径中，只有 `/data/comparisons.db` 位于规定的数据目录下。用路径结构核对，不用字符串是否包含 `data` 来猜。

```python
# runnable: hb22_answer_data_path
from pathlib import PurePosixPath

data_root = PurePosixPath("/data")
paths = [
    PurePosixPath("/data/comparisons.db"),
    PurePosixPath("/app/comparisons.db"),
    PurePosixPath("/database-backup/comparisons.db"),
]
matches = [path for path in paths if path.is_relative_to(data_root)]
assert matches == [PurePosixPath("/data/comparisons.db")]
print(matches)
```

PurePosixPath 只检查这里给定的普通路径结构，不访问容器，也不解析符号链接。安全限制真实文件访问时，还要考虑规范化、链接与最终实际路径，不能拿这个小练习充当沙箱。

9）部署前仍然需要的核对与资料

9.1 当前仓库还不是完整对外服务方案

正式对外提供服务前，还要决定鉴权、请求大小与频率限制、TLS、反向代理信任范围、数据库迁移、备份恢复、日志脱敏、监控和资源上限。

相似度分数仍然只是技术指标。换成 Docker、加上反向代理或多 worker，不会让它自动成为侵权、权属或其他法律结论。

不要把数据库密码写进 Dockerfile 的 ENV 或构建参数，也不要把私钥复制进镜像。凭据应通过合适的运行时秘密管理方式提供，并限制读取权限。

9.2 官方资料

[Dockerfile 指令](https://docs.docker.com/reference/dockerfile/)、[镜像构建建议](https://docs.docker.com/build/building/best-practices/)、[发布端口](https://docs.docker.com/get-started/docker-concepts/running-containers/publishing-ports/) 对应构建与网络边界。

[Compose 服务](https://docs.docker.com/reference/compose-file/services/)、[Compose 卷](https://docs.docker.com/reference/compose-file/volumes/)、[Compose 网络](https://docs.docker.com/compose/how-tos/networking/) 对应启动配置与持久化。

[Uvicorn 部署](https://www.uvicorn.org/deployment/)、[Gunicorn 项目](https://github.com/benoitc/gunicorn)、[uvicorn-worker](https://github.com/Kludex/uvicorn-worker) 对应服务器和 worker 选择；示意配置未在 Docker 环境中执行验证。
