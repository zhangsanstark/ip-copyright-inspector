解释器、虚拟环境与依赖：让同一份项目在另一台电脑运行

把代码复制过去，只完成了一半。另一台电脑还需要合适的 Python、对应的第三方包，以及正确的启动位置。把这几项分开检查，环境问题通常就没有那么神秘。

阅读导航：1 四个基本对象；2 pyproject；3 uv 流程；4 venv 与 pip；5 Poetry 流程；6 锁文件；7 排错；8 三道完整练习；9 日常流程与资料。

本章的命令用于说明操作流程，没有替你安装软件、升级环境或推送代码。runnable 代码块只做本地检查，使用 `python scripts/check_handbook_examples.py --chapter 20 --show-output` 可统一运行。

1）先分清四个东西，别把它们都叫“Python 环境”

1.1 Python 解释器：真正执行代码的程序

在 Windows 上它通常是某个目录里的 `python.exe`。机器上可以同时存在多个解释器：系统安装的、工具下载的、项目虚拟环境里的。

在终端输入 `python`，操作系统会根据当前环境寻找一个可执行文件。它未必就是编辑器选中的解释器，也未必就是你刚才安装包时用的那个。

排查时先打印 `sys.executable`，比根据终端前面的名字猜测可靠。

```python
# runnable: hb20_interpreter
import sys
from pathlib import Path

executable = Path(sys.executable)
assert executable.is_file()
assert sys.version_info >= (3, 11)
print("解释器：", executable)
print("版本：", sys.version.split()[0])
print("环境前缀：", sys.prefix)
print("基础前缀：", sys.base_prefix)
print("是否处于通常的 venv：", sys.prefix != sys.base_prefix)
```

`sys.prefix != sys.base_prefix` 是判断通常 venv 环境的一个直接线索，不是识别所有第三方环境管理方式的万能规则。

1.2 虚拟环境：把某个项目的包单独放一份

项目 A 需要某个库的旧版本，项目 B 需要新版本。如果它们都往同一目录安装包，可能互相影响。

虚拟环境给项目准备独立的安装位置和启动入口。它通常复用基础 Python 的一部分文件，并不是为每个项目重新创建一台操作系统。

`.venv` 不应作为源码推送，也不适合从 Windows 复制到 Linux。环境里包含路径和平台相关内容，正确方式是用配置文件在目标机器重新建立。

1.3 包管理器：下载、安装、解析依赖的工具

pip 主要负责安装包；uv 可以进一步管理项目、锁文件、环境与运行；Poetry 也提供项目依赖和打包工作流。

它们不是 Python 语言本身。换管理器不会把 `def` 的语法变掉，但会影响“包装在哪里、版本怎样选、命令使用哪个环境”。

1.4 配置与锁文件：一个写要求，一个写解析结果

`pyproject.toml` 写项目的直接依赖和范围。例如需要 Pydantic 2.x，而不是任意大版本。

锁文件记录一次解析后的具体版本、依赖关系等信息。两个机器按同一套锁定结果创建环境，更容易得到一致行为。

Java 背景可以把 `pyproject.toml` 与项目构建描述文件放在同一层理解。但 Python 的构建后端、安装器、环境工具可能是不同组件，不是一个名字包办全部。

2）把本仓库的 pyproject 逐项拆开

2.1 project 区域描述项目本身

本仓库的发布名称是 `ip-copyright-inspector`，导入名是 `ip_copyright_inspector`。前者用连字符，后者用下划线。这种差别正常存在，不能简单把 pip 名字原样放进 import。

`requires-python = ">=3.11"` 是允许的 Python 版本范围，不是自动宣布任何未来版本和所有平台都已测试通过。实际兼容性仍靠测试确认。

下面是配置片段，用于理解字段；不是让你再建立第二份项目配置。

```toml
[project]
name = "ip-copyright-inspector"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115,<1.0",
    "pydantic>=2.10,<3.0",
    "sqlalchemy[asyncio]>=2.0,<3.0",
]
```

`>=2.10,<3.0` 同时给出下限和上限，不等于固定为 2.10。后续安装如果重新解析，可能选择范围内另一版本。

`sqlalchemy[asyncio]` 中的方括号表示请求这个发行包定义的额外依赖集合，不是导入语法，也不是给 Python 列表传参。

2.2 运行依赖与开发依赖分开

运行 API 需要 FastAPI、数据库库和服务器。执行测试额外需要 pytest 与 TestClient 使用的客户端依赖。

仓库同时保留 `project.optional-dependencies.dev` 和 `dependency-groups.dev`，为了适配不同安装流程。当前测试客户端依赖在配置中写的是 `httpx2`，不要凭旧教程把它私自替换成另一个包。

两处 dev 声明应保持一致。只修改一处，可能出现“uv 能测试，pip 安装后不能测试”的差异。

extra 是可发布的可选依赖集合，例如 `.[dev]`；dependency group 是项目工作流中的依赖分组。名字都叫 dev，也不表示所有工具都会自动把它们视作同一个对象。

2.3 build-system 不是启动服务器

本仓库使用 Hatchling 构建项目包。安装器需要构建 wheel 时，会按 `build-system` 选择构建后端。

`src` 布局表示源码放在 `src/ip_copyright_inspector`。配置需要让构建后端找到这个目录；否则仓库里看得到文件，安装好的包里却可能没有它。

`[tool.pytest.ini_options]` 是 pytest 的配置，不是通用 Python 设置。里面的 `pythonpath = ["src"]` 帮助测试找到源码，但不能推出任何目录执行普通 Python 都会自动添加这个路径。

3）使用 uv：从拉取代码到执行测试

3.1 clone 只复制仓库，不安装依赖

在 GitHub 仓库页面复制实际克隆地址，执行下面的命令。尖括号部分必须替换，不能原样输入；目录已存在时不要重复 clone 到同名目录。

```powershell
git clone <从仓库页面复制的地址>
cd ip-copyright-inspector
```

这一步得到源文件和版本历史，没有自动安装 Python 包。如果 clone 成功但 import 失败，不一定是 Git 的问题。

3.2 先看工具能否使用，再同步依赖

假定机器已经按官方方式安装了 uv，并处于项目根目录：

```powershell
uv --version
uv sync --locked
uv run --locked python -m pytest
```

第一条只查看工具版本。第二条按项目与锁文件准备环境；`--locked` 要求锁文件与项目要求一致，不允许默默更新锁定结果。第三条在项目环境中运行 pytest，并维持同样的锁文件要求。

`uv sync` 默认是精确同步：环境中不属于本次同步结果的包可能被移除。不要在项目 `.venv` 里随手装一堆其他用途的工具，再指望它们永久保留。

dev 依赖组默认参与项目同步；optional extras 默认不会因为“写在 pyproject 里”就全部安装。本仓库通过 dev group 提供测试依赖。

3.3 启动 API 时，每一段参数都有意义

```powershell
uv run --locked uvicorn ip_copyright_inspector.main:app --host 127.0.0.1 --port 8000 --reload
```

`uv run` 负责选项目环境并运行命令；`uvicorn` 是 ASGI 服务器；冒号前是导入模块，冒号后是模块里的应用对象。

`127.0.0.1` 只监听本机回环地址；8000 是端口；`--reload` 用于本地修改后自动重启，不是正式服务运行时必须保留的参数。

启动成功后可访问 `http://127.0.0.1:8000/health` 与 `/docs`。结束前台服务通常按 Ctrl+C；不要把关闭终端窗口当成唯一控制方式。

3.4 uv run 不是只做一层命令转发

默认情况下，uv run 会检查项目的锁定与环境状态，再执行命令。它可能进行锁定或同步工作，具体取决于当前状态和选项。

`--locked`：如果需要更新锁文件就报错。`--frozen`：使用现有锁文件，不检查它是否需要随项目声明更新。`--no-sync`：跳过环境同步。

这三个参数解决的问题不同。为了保持一致而写 `--frozen`，不代表已经证明 pyproject 与锁文件完全一致；为了提速写 `--no-sync`，也不代表环境已经正确。

4）不用 uv 时：venv 与 pip 的明确路线

4.1 创建环境与激活环境是两步

以下是 Windows PowerShell 命令，假定 `py -3.11` 能找到一个已安装的 Python 3.11。也可以替换为机器上确认可用、满足项目要求的解释器。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

第一条创建环境。第二条明确让这个环境的 Python 运行 pip，不依赖终端当前的 `pip` 指向谁。`-e` 是可编辑安装，源码修改通常可以直接反映到后续运行；`.[dev]` 是当前项目加 dev extra。

这条 pip 安装命令读取 pyproject 中的版本范围，不读取 `uv.lock`。它可以完成安装，但不能声称与 uv 锁定环境完全一致。

4.2 激活只是方便，不是使用虚拟环境的硬性条件

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest
deactivate
```

激活脚本主要调整当前终端的环境，让短命令 `python` 优先指向 `.venv`。关闭这个终端后，不会自动改变所有其他终端和编辑器。

如果 PowerShell 不允许执行激活脚本，不必先降低整台机器的脚本安全策略。直接使用上一节的完整解释器路径，就能在不激活的情况下运行。

Linux/macOS 的虚拟环境可执行目录通常是 `.venv/bin`，不是 `.venv/Scripts`。跨系统照抄路径时，要先确认平台。

4.3 python -m 比裸命令更容易核对归属

`python -m pytest` 表示“用这个 Python 找到并执行 pytest 模块”。裸 `pytest` 则可能由 PATH 找到另一个环境生成的启动脚本。

如果出现“pip 说已安装，import 仍失败”，优先比较 `python -m pip --version` 与 `python -c "import sys; print(sys.executable)"` 的路径，而不是重复安装五次。

5）使用 Poetry：另一条完整路线，不要混着猜

5.1 先确认选中的解释器

Poetry 版本之间有命令与配置差异，先运行 `poetry --version`。本节说明常见项目流程，不宣称机器已经安装了某个最新版本。

```powershell
poetry --version
poetry env info
poetry install --extras dev
poetry run python -m pytest
```

`poetry env info` 用于查看环境；`poetry install` 根据项目配置准备依赖与项目自身；这里明确选择 dev extra；`poetry run` 让命令在它管理的环境里执行。

如果没有 `poetry.lock`，首次安装通常需要解析并生成 Poetry 自己的锁文件。这个结果不是把 `uv.lock` 自动翻译后得到的保证。

5.2 一个仓库可以支持多种工具，但应有主要锁定路线

本仓库已有 uv 锁定路线。为了临时试用另一个工具而随意新增第二套锁文件，会增加两套结果不一致的可能性。

团队式协作最重要的是明确：谁负责生成锁文件、以哪套结果作为测试基准、何时允许升级。不要让每个人安装“当前能解析的最新版”，再把差异归因于机器玄学。

如果决定统一切换工具，应同时检查配置、锁文件、持续集成和启动文档，不是只把命令里的 uv 换成 poetry。

5.3 Poetry 的环境也不是自动被编辑器选中

命令行测试通过，编辑器仍报找不到包，可能是编辑器选择了系统解释器。先通过 `poetry run python -c "import sys; print(sys.executable)"` 得到实际路径，再在编辑器里选择同一解释器。

不要因为红色波浪线就立即改导入名或复制第三方库到源码目录。先确认它是静态检查环境问题，还是真正运行错误。

6）锁文件管什么，不管什么

6.1 它固定依赖解析，不固定宇宙里的所有条件

锁文件能帮助固定包版本及其关系，但操作系统、CPU 架构、Python 版本、数据库版本和外部服务配置仍可能不同。

某些包在不同平台选择不同发行文件，某些依赖有平台条件。可靠复现需要锁文件、适用解释器和测试共同配合。

6.2 升级是有意识地改变依赖，不是修复所有问题的第一步

先确认当前问题是否能复现，再决定要不要升级相关依赖。升级后查看锁文件变化，执行测试，保留可以回退的版本记录。

`uv lock --upgrade` 会请求重新考虑较新版本，作用范围与“运行一下测试”完全不同。日常执行命令时不要随手附加 upgrade。

删除锁文件再安装可能让错误暂时消失，但也可能只是换了一批版本。没有记录变化和验证结果，就难以知道究竟修好了什么。

7）常见故障，按证据检查

7.1 ModuleNotFoundError：先问哪一个解释器

检查 `sys.executable`；检查对应环境是否安装了包；检查发行名称与导入名称是否不同；检查当前目录是否存在同名 `.py` 文件遮蔽第三方包。

例如把自己的脚本命名为 `pydantic.py`，可能挡住真正的 pydantic 包。这样的错误不是联网重新下载能解决的。

7.2 版本不兼容：先看错误来自哪条要求

“需要 Python >=3.11”与“两个库要求不兼容的某个依赖版本”是不同问题。前者先换合适解释器；后者需要检查依赖范围与解析结果。

不要直接删除上限来消除解析错误。上限可能是为了避开尚未验证的大版本变化，去掉它会扩大风险。

7.3 下载失败：网络失败不等于包不存在

超时、证书、代理、私有源权限、平台没有合适 wheel，可能出现不同错误。先保留最早的具体报错，再处理对应原因。

不要关闭 TLS 校验来“永远解决证书问题”。这会改变下载信任边界。代理和证书应按环境要求配置，令牌不要写进公开仓库。

8）三道练习，答案只读取和计算

8.1 练习一：查清正在运行的包来自哪里

要求：同时打印 Pydantic 的实际安装版本与导入文件路径，并验证它提供 v2 的模型接口。不要在答案里硬编码“最新版本号”。

```python
# runnable: hb20_answer_package_origin
from importlib.metadata import version
from pathlib import Path
import pydantic

installed_version = version("pydantic")
module_file = Path(pydantic.__file__)
assert installed_version.split(".")[0] == "2"
assert module_file.is_file()
assert hasattr(pydantic.BaseModel, "model_validate")
print("安装版本：", installed_version)
print("导入文件：", module_file)
```

如果版本看起来正确，路径却指向自己的 `pydantic.py`，应优先排查同名遮蔽。版本元数据和当前导入来源是两个需要一起观察的证据。

8.2 练习二：读 TOML，不要用字符串切割猜配置

要求：从给定配置中取出运行依赖和 dev extra，验证它们是两个列表。答案使用 Python 3.11 起提供的 `tomllib`。

```python
# runnable: hb20_answer_toml
import tomllib

text = '''
[project]
name = "text-checker"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.10,<3.0"]

[project.optional-dependencies]
dev = ["pytest>=8.3,<10.0"]
'''
config = tomllib.loads(text)
runtime_dependencies = config["project"]["dependencies"]
development_dependencies = config["project"]["optional-dependencies"]["dev"]
assert runtime_dependencies == ["pydantic>=2.10,<3.0"]
assert development_dependencies == ["pytest>=8.3,<10.0"]
assert config["project"]["requires-python"] == ">=3.11"
print(runtime_dependencies, development_dependencies)
```

tomllib 负责解析 TOML 结构，不负责解析版本范围是否相容。这两个任务不要混为一谈。

8.3 练习三：导入名和发行名不是同一个字段

要求：证明项目可以通过下划线名称导入，并实际调用计算函数。答案不依赖当前工作目录里恰好有一个同名文件。

```python
# runnable: hb20_answer_project_import
from pathlib import Path
import ip_copyright_inspector
from ip_copyright_inspector.similarity import compare_texts

result = compare_texts("abcd", "abce", ngram_size=2)
assert result.score == 0.5
module_path = Path(ip_copyright_inspector.__file__)
assert module_path.is_file()
assert module_path.name == "__init__.py"
print("项目导入位置：", module_path)
print("实际计算结果：", result.score)
```

如果脱离仓库根目录运行这个脚本失败，而 pytest 成功，应核对是否只靠 pytest 的 `pythonpath` 配置找到了 src。完成项目安装或通过项目工具运行，比临时在每个脚本里改 `sys.path` 更清楚。

9）日常维护顺序与资料

9.1 在另一台电脑更新已有目录

先执行 `git status` 看本地是否有未提交修改；确认不会冲突后再拉取更新；按锁文件同步环境；运行测试；最后启动服务。

```powershell
git status
git pull --ff-only
uv sync --locked
uv run --locked python -m pytest
```

`--ff-only` 表示只接受可以直接快进的更新；有分叉时停止，不自动制造一次合并。它不是删除本地修改的命令，也不会替你处理冲突。

如果第一步发现自己的改动，先保存并决定如何合并，不要为了拉取成功直接重置整个目录。

9.2 官方资料

[Python venv](https://docs.python.org/3/library/venv.html)、[Python 包装项目指南](https://packaging.python.org/en/latest/tutorials/packaging-projects/)、[pyproject 规范说明](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) 对应解释器环境与项目元数据。

[uv 项目同步](https://docs.astral.sh/uv/concepts/projects/sync/)、[uv 依赖管理](https://docs.astral.sh/uv/concepts/projects/dependencies/)、[Poetry 基础流程](https://python-poetry.org/docs/basic-usage/) 对应锁定、依赖范围和运行命令；工具选项以实际安装版本为准。
