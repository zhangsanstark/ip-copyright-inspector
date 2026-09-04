pytest 与排错：让“我觉得没问题”变成可以重复核对的结果

测试不是把程序运行一遍，然后看到没有红字就结束。它要提前写清楚：给什么输入，应该得到什么结果，出现什么情况算失败。这样改完代码以后，同一组问题还能再问一遍。

阅读导航：1 assert；2 测试组织；3 参数化与异常；4 fixture；5 替换依赖；6 本仓库测试；7 排错过程；8 三道完整练习；9 命令与资料。

本章的临时测试会写入临时目录，执行完清理，不改仓库 tests。运行 `python scripts/check_handbook_examples.py --chapter 21 --show-output` 可以一次核对全部 runnable 示例。

1）先把一个断言写准确

1.1 assert 检查的是一个条件，不是输出长得像不像

`assert actual == expected` 表示这个条件必须为真。为假会抛 AssertionError，测试因此失败。

`print(actual)` 只能让人看见一个值，不会自动记住“这个值应该是 0.5”。当测试数量增加，只靠眼睛看输出很容易漏掉变化。

```python
# runnable: hb21_basic_assertions
from ip_copyright_inspector.similarity import compare_texts

result = compare_texts("abcd", "abce", ngram_size=2)
assert result.intersection_count == 2
assert result.union_count == 4
assert result.score == 0.5
assert result.score == result.intersection_count / result.union_count
print("同时核对中间计数与最终分数")
```

最后一条断言与前面两条作用不同。只验证公式，可能让交集与并集都算错却仍然通过；只验证一个分数，又可能漏掉分子分母的解释不正确。根据风险选择有意义的观察点。

1.2 assert 不适合承担面向用户的输入校验

Python 的优化运行模式可以移除 assert。公开函数需要拒绝非法输入时，应明确 `raise ValueError(...)`，而不是把必须执行的校验只写成断言。

测试里的断言是核对工具；业务里的异常是运行规则。两者恰好都能在失败时中断，但用途不同。

1.3 浮点数要根据目标选择比较方法

`0.1 + 0.2` 不一定与字面量 `0.3` 完全相等。测试数值算法时，可以用 `pytest.approx` 声明允许的误差。

```python
# runnable: hb21_approx
import pytest

value = 0.1 + 0.2
assert value != 0.3
assert value == pytest.approx(0.3)
assert [0.1 + 0.2, 0.5] == pytest.approx([0.3, 0.5])
assert 0.30000001 == pytest.approx(0.3, abs=0.000001)
print("近似比较处理数值误差，不是放过任意错误")
```

误差范围应由业务精度决定。把容差调得很大直到测试变绿，并不意味着实现正确。金额等场景还要先考虑数据表示，不能只在最后用 approx 掩盖问题。

2）pytest 怎样发现并运行测试

2.1 文件名与函数名要符合约定

常见测试文件名是 `test_*.py`，函数名是 `test_*`。运行 pytest 后，它收集符合规则的测试，再逐项执行。

仓库配置指定了 `testpaths = ["tests"]`，因此根目录执行 `python -m pytest` 时，会优先按这个配置查找测试。

普通函数不会仅仅因为出现在测试文件里就执行。辅助函数如 `comparison_payload()` 可以用来创建输入，但需要由测试调用。

2.2 一条测试最好说明一个明确行为

`test_invalid_ngram_is_rejected` 比 `test_1` 更容易让失败报告表达意思。名字不是形式要求，而是以后定位问题时能看到的第一句话。

测试也可以有多个断言，只要它们围绕同一个行为。例如创建接口成功时，同时核对状态码、响应编号、数据库记录，是同一条“创建成功”的完整验证。

不要把所有模块从头到尾串在一个巨型测试里。前面一步失败，后面几十个行为都没有机会核对，报告也难以定位。

3）参数化与异常：把边界值写成一组问题

3.1 parametrize 让同一条规则接受不同输入

同一个算法需要检查窗口大小 1、2、3、4，不必复制四份函数。`@pytest.mark.parametrize` 会把输入表拆成独立测试项。

每一行参数对应一次调用。失败报告会指出是哪一组值失败，不是等整个循环跑完只告诉你“有问题”。

3.2 raises 明确表示“这里应该失败”

`with pytest.raises(ValueError):` 包裹预期会抛异常的操作。如果没有抛、或者抛了错误的异常类型，测试会失败。

异常发生以后，with 内后续语句不会继续运行。检查捕获到的异常对象时，应放在 with 外。

```python
# runnable: hb21_expected_error
import pytest
from ip_copyright_inspector.similarity import character_ngrams

with pytest.raises(ValueError) as captured:
    character_ngrams("abcd", 0)
assert "1" in str(captured.value)
assert "8" in str(captured.value)
assert character_ngrams("abcd", 2) == {"ab", "bc", "cd"}
print("非法窗口明确失败；合法窗口仍正常计算")
```

`match=` 按正则表达式匹配异常文字，不是单纯字面量比较。要匹配包含括号、点号等字符的完整文字，需考虑正则转义；也可以直接比较 `str(captured.value)`。

4）fixture：把每次测试需要的准备和清理放到一起

4.1 参数名字会触发 fixture 注入

测试写成 `def test_file(tmp_path):`，不是调用者忘了传参数。pytest 会识别 fixture 名称，为这次测试准备一个临时目录 Path。

自定义 fixture 可以准备数据、创建对象、建立临时数据库连接，再把结果交给测试。默认 function 作用域通常意味着每条测试重新准备一份，减少相互污染。

扩大到 module 或 session 作用域可以减少昂贵初始化，但共享可变状态也会让测试顺序影响结果。先保证独立，再考虑提速。

4.2 yield 把“交给测试用”和“用完清理”连起来

fixture 的 yield 前执行准备；yield 的值交给测试；测试结束后继续执行后面的清理。测试断言失败时，已进入的 fixture 仍应按框架流程完成清理。

清理需要围住实际拥有的资源，例如连接、临时配置或依赖替换。不要把某个完全无关的全局环境也顺手重置。

4.3 用一个可独立运行的实验观察 pytest 的实际收集

外层代码只负责把内层测试文本写到临时目录，并启动同一个 Python 的 pytest。平时写仓库测试时，直接把内层内容放进 `tests/test_*.py` 即可，不必照搬这层临时包装。

```python
# runnable: hb21_fixture_suite
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

test_source = '''
import os
import pytest

def doubled(value):
    if value < 0:
        raise ValueError("value must be nonnegative")
    return value * 2

@pytest.fixture
def values():
    return [1, 2]

@pytest.mark.parametrize("value, expected", [(0, 0), (2, 4), (5, 10)])
def test_doubled(value, expected):
    assert doubled(value) == expected

def test_rejects_negative():
    with pytest.raises(ValueError, match="nonnegative"):
        doubled(-1)

def test_fixture_is_fresh(values):
    values.append(3)
    assert values == [1, 2, 3]

def test_another_fixture_is_fresh(values):
    assert values == [1, 2]

def test_file_and_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("HB21_MODE", "demo")
    path = tmp_path / "result.txt"
    path.write_text(os.environ["HB21_MODE"], encoding="utf-8")
    assert path.read_text(encoding="utf-8") == "demo"
'''

with TemporaryDirectory(prefix="hb21-suite-") as directory:
    path = Path(directory) / "test_demo.py"
    path.write_text(test_source, encoding="utf-8")
    environment = os.environ | {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(path)],
        cwd=directory, env=environment, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "7 passed" in result.stdout
    print(result.stdout.strip())
```

共有 7 项测试，不是 5 项：参数化的函数产生 3 项，其余 4 个测试函数各 1 项。两个 values 使用者得到独立列表，所以第一个追加的 3 不会跑进第二个测试。

5）monkeypatch 与 mock：替换一个边界，不是伪造所有现实

5.1 monkeypatch 适合临时改属性、环境变量与路径

`monkeypatch.setenv` 设置当前测试中的环境变量，`setattr` 替换指定属性，`chdir` 临时改变目录。pytest fixture 会在结束时恢复相应状态。

独立脚本中可以使用 `pytest.MonkeyPatch.context()`，明确把替换限制在一个代码块内。

```python
# runnable: hb21_monkeypatch_scope
import os
import pytest

original = os.environ.get("HB21_DEMO_MODE")
with pytest.MonkeyPatch.context() as patcher:
    patcher.setenv("HB21_DEMO_MODE", "temporary")
    assert os.environ["HB21_DEMO_MODE"] == "temporary"
assert os.environ.get("HB21_DEMO_MODE") == original
print("临时配置已恢复")
```

如果模块在导入时就把环境变量读取到常量里，之后改环境变量不会自动重新计算那个常量。本仓库的数据库 URL 就是在模块导入时读取，因此测试直接替换引擎与会话工厂，而不是只改一个环境变量后假装已经换库。

5.2 mock 可以记录调用，也可以返回预先安排的结果

`Mock` 适合模拟同步调用；`AsyncMock` 适合被 await 的异步调用。它们让你检查“有没有调用、传了什么”，或者稳定触发某个失败分支。

```python
# runnable: hb21_mock_calls
import asyncio
from unittest.mock import AsyncMock, Mock

sender = Mock(return_value="accepted")
result = sender("document-7", priority=2)
assert result == "accepted"
sender.assert_called_once_with("document-7", priority=2)

async def main():
    repository = AsyncMock(return_value={"id": 7})
    value = await repository(7)
    assert value == {"id": 7}
    repository.assert_awaited_once_with(7)

asyncio.run(main())
print("同步检查调用；异步还可以检查是否真的 await")
```

Mock 可以让一个根本不存在的接口看起来正常，因此对真实对象进行模拟时，可考虑 `spec`、`spec_set` 或 autospec 限制它的属性和调用形状。模拟越多，越需要另一些集成测试验证真实组件能接起来。

5.3 patch 应替换使用位置，不一定是最初定义的位置

假如某模块写了 `from time import time`，它已经把函数绑定到自己的模块变量。测试应替换这个使用方的 `time` 名称，而不是以为改掉 `time` 模块里的属性就必然影响所有已导入引用。

这与普通变量赋值规则一致：把一个对象交给另一个名字以后，原名字后来指向别处，不会把所有其他名字一起搬走。

6）读懂本仓库已有测试到底保证什么

6.1 纯函数测试：输入直接到算法

文本标准化、片段集合和 Jaccard 分数可以不启动 API、不连接数据库就测试。这类测试快，失败位置也相对集中。

这里应覆盖空文本、短文本、全角字符、大小写、空白、重复片段和非法窗口等边界。正常示例通过，不代表边界自动正确。

6.2 API 测试：不仅看返回 201

`tests/test_api.py` 的 fixture 为测试建立临时 SQLite 数据库，用 TestClient 进入应用生命周期，替换真实引擎和会话工厂。

创建成功测试会核对固定声明、方法名、分数范围与落库记录，并确认数据库中没有 `left_text`、`right_text` 这两个原文字段。这比“请求返回了 JSON”更接近项目真正关心的行为。

错误响应测试提交包含标记的过长文本，断言返回 422，同时确认响应没有重复输出那段原文标记，也没有错误项的 `input` 字段。

6.3 故障测试：明确模拟 flush 失败与 commit 失败

仓库用 FailingSession 记录调用顺序。flush 失败时不应继续 commit；commit 失败时说明已经经过 flush。两种情况都应 rollback，并向客户端返回 503。

这验证的是应用面对数据库异常时的控制流程，不是证明所有真实数据库网络故障都已覆盖。真实驱动断连、超时与锁冲突，还可以有各自的集成测试。

7）排错时，让每一步缩小范围

7.1 先读最早的失败，不要只盯最后一行红字

一个 import 失败可能让整批测试无法收集；一个 fixture 初始化失败可能影响多个测试。它们都不是“每个业务函数一起坏了”。

先分清失败阶段：收集、准备、执行、清理。再看具体异常类型、源文件和最早的业务相关位置。

7.2 先复现最小测试，再观察中间值

假设预期分数 0.5，实际是 1.0。先单独运行对应测试；打印或断点观察标准化文本、左右片段集合、交集与并集；找到第一个与预期不同的步骤。

如果左右集合就已经一样了，先查标准化和切片，不必先改数据库返回格式。排错是沿数据变化定位，不是随机轮流修改所有层。

7.3 修复前补回归测试，修复后扩大核对范围

找到一个原来没覆盖的输入后，先写能复现它的测试。修复后先跑该测试，再跑邻近模块，最后跑完整测试集。

不要为了让测试通过而把 expected 改成当前错误结果。修改预期必须有行为规则改变的依据，而不是“现在程序就是这样返回”。

8）三道练习与完整答案

8.1 练习一：同一个例子，窗口大小改变了什么

要求：对 `abcd` 与 `abce`，核对窗口 1、2、3、4 的分数分别为 0.6、0.5、1/3、0。先手算片段，再执行答案。

```python
# runnable: hb21_answer_parameter_cases
import pytest
from ip_copyright_inspector.similarity import compare_texts

cases = [(1, 0.6), (2, 0.5), (3, 1 / 3), (4, 0.0)]

@pytest.mark.parametrize("window, expected", cases)
def test_window(window, expected):
    result = compare_texts("abcd", "abce", ngram_size=window)
    assert result.score == pytest.approx(expected)

for window, expected in cases:
    test_window(window, expected)
print("四组输入均通过；放进测试文件后 pytest 会分别收集四项")
```

这个独立脚本末尾的循环用于直接运行答案；真正由 pytest 收集时，装饰器会提供四组参数。两种运行方式不要同时解释成“都是 pytest 启动的”。

8.2 练习二：保存文本到临时文件，并保留原有换行

要求：函数使用 UTF-8 写文件；测试使用 tmp_path，不写固定真实文件。下面答案让 pytest 实际注入临时目录。

```python
# runnable: hb21_answer_tmp_path
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

source = '''
from pathlib import Path

def save_report(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

def test_round_trip(tmp_path):
    target = tmp_path / "报告.txt"
    content = "第一行\\n第二行"
    save_report(target, content)
    assert target.read_text(encoding="utf-8") == content
    assert target.parent == tmp_path
'''
with TemporaryDirectory(prefix="hb21-answer-") as directory:
    file = Path(directory) / "test_report.py"
    file.write_text(source, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(file)],
        cwd=directory,
        env=os.environ | {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    print(result.stdout.strip())
```

预期核对的是读取后的文本内容，而不是所有操作系统上的磁盘字节换行形式完全相同。需要逐字节协议时，应改用 bytes 并明确编码和换行规则。

8.3 练习三：提交失败后，必须尝试回滚

要求：函数先提交；提交抛 RuntimeError 后必须 await 回滚，再把原异常继续抛给调用者。答案使用 AsyncMock，不连接数据库。

```python
# runnable: hb21_answer_rollback
import asyncio
from unittest.mock import AsyncMock, Mock
import pytest

async def finish_transaction(session):
    try:
        await session.commit()
    except RuntimeError:
        await session.rollback()
        raise

async def main():
    session = Mock()
    session.commit = AsyncMock(side_effect=RuntimeError("forced failure"))
    session.rollback = AsyncMock()
    with pytest.raises(RuntimeError, match="forced failure"):
        await finish_transaction(session)
    session.commit.assert_awaited_once_with()
    session.rollback.assert_awaited_once_with()
    assert session.commit.await_count == session.rollback.await_count == 1
    print("提交失败没有被吞掉，回滚也确实被 await")

asyncio.run(main())
```

此处用 RuntimeError 让例子独立。在仓库真实路由中，捕获的是 SQLAlchemyError，并转成适合客户端的 503；不能为了套答案，把所有异常都当作同一种数据库故障。

9）常用命令与资料

9.1 先缩小，再扩大

```powershell
uv run --locked python -m pytest
uv run --locked python -m pytest tests/test_api.py
uv run --locked python -m pytest tests/test_api.py -k persistence
uv run --locked python -m pytest -x
uv run --locked python -m pytest -vv
uv run --locked python -m pytest -s
```

第一条跑整套；第二条跑单文件；`-k` 按名称表达式筛选；`-x` 遇到首个失败就停；`-vv` 提供更详细信息；`-s` 不捕获标准输出，便于临时看 print。

如果需要交互断点，可以在自己操作的终端使用 pytest 的 `--pdb` 或代码中的 `breakpoint()`。自动检查流程里不要留下无人继续的交互断点。

9.2 官方资料

[pytest 断言](https://docs.pytest.org/en/stable/how-to/assert.html)、[参数化](https://docs.pytest.org/en/stable/how-to/parametrize.html)、[fixture](https://docs.pytest.org/en/stable/how-to/fixtures.html) 对应测试表达和准备流程。

[monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)、[临时目录](https://docs.pytest.org/en/stable/how-to/tmp_path.html)、[unittest.mock](https://docs.python.org/3/library/unittest.mock.html) 对应可恢复替换、隔离文件和调用核对。
