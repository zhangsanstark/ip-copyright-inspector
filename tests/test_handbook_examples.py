"""Check the handbook harness, not external tools or optional services."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_handbook_examples.py"
SPEC = importlib.util.spec_from_file_location("handbook_harness", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
harness = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = harness
SPEC.loader.exec_module(harness)


def chapter(tmp_path, body, name="01-test.md"):
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_parser_recognizes_kinds_and_ignores_shell(tmp_path):
    path = chapter(tmp_path, """普通文字
```python
# runnable: hb01_ok
assert 1 + 1 == 2
```
```python
# fragment: depends on earlier code
call_something()
```
```python
# optional: requires another package
import optional_package
```
```powershell
python --version
```
""")
    examples = harness.parse_chapter(path)
    assert [e.kind for e in examples] == ["runnable", "fragment", "optional"]
    assert examples[0].line == 3


@pytest.mark.parametrize("body", [
    "```python\nassert True\n```\n",
    "```python\n# runnable: hb02_wrong\nassert True\n```\n",
    "```python\n# runnable: hb01_bad\nprint(1)\n```\n",
    "```python\n# runnable: hb01_bad\nassert (\n```\n",
    "```python\n# runnable: hb01_open\nassert True\n",
])
def test_parser_rejects_invalid_runnable_blocks(tmp_path, body):
    with pytest.raises(ValueError):
        harness.parse_chapter(chapter(tmp_path, body))


def test_duplicate_ids_rejected(tmp_path):
    content = "```python\n# runnable: hb01_same\nassert True\n```\n"
    chapter(tmp_path, content + content)
    with pytest.raises(ValueError, match="duplicate"):
        harness.collect_examples(tmp_path)


def test_chapter_filter_does_not_parse_other_work_in_progress(tmp_path):
    chapter(tmp_path, "```python\n# runnable: hb01_ok\nassert True\n```\n")
    chapter(tmp_path, "```python\nunmarked\n```\n", "02-other.md")
    assert len(harness.collect_examples(tmp_path, {"01"})) == 1


def test_export_preserves_existing_files(tmp_path):
    path = chapter(tmp_path, "```python\n# runnable: hb01_export\nassert 2 + 2 == 4\n```\n")
    examples = harness.parse_chapter(path)
    destination = tmp_path / "exported"
    assert harness.export_examples(examples, destination) == 1
    script = destination / "hb01_export.py"
    assert "assert 2 + 2 == 4" in script.read_text(encoding="utf-8")
    script.write_text("# user's edited copy\n", encoding="utf-8")
    with pytest.raises(ValueError, match="overwrite"):
        harness.export_examples(examples, destination)
    assert script.read_text(encoding="utf-8") == "# user's edited copy\n"


def test_tilde_fence_and_long_outer_fence(tmp_path):
    path = chapter(tmp_path, "~~~py\n# runnable: hb01_tilde\nassert True\n~~~\n"
                   "````text\n```python\nnot executable\n```\n````\n")
    assert len(harness.parse_chapter(path)) == 1


def test_subprocess_isolated_and_unicode(tmp_path):
    code = "# runnable: hb01_process\nfrom pathlib import Path\nassert not Path('README.md').exists()\nprint('你好')\n"
    example = harness.parse_chapter(chapter(tmp_path, f"```python\n{code}```\n"))[0]
    ok, output = harness.run_example(example, 5)
    assert ok and "你好" in output


def test_subprocess_failure_is_reported(tmp_path):
    example = harness.parse_chapter(chapter(tmp_path,
        "```python\n# runnable: hb01_failure\nassert False, 'expected failure'\n```\n"))[0]
    ok, output = harness.run_example(example, 5)
    assert not ok and "expected failure" in output


def _example(tmp_path, code, name="hb01_process_tree"):
    return harness.Example(tmp_path / "01-test.md", 1, "01", "runnable", name, code)


def _process_is_running(pid):
    """Do not send termination signals while checking the owned test PIDs."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        api.OpenProcess.restype = wintypes.HANDLE
        api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        api.WaitForSingleObject.restype = wintypes.DWORD
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        api.CloseHandle.restype = wintypes.BOOL
        handle = api.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE only
        if not handle:
            error = ctypes.get_last_error()
            assert error == 87, ctypes.WinError(error)  # PID no longer exists
            return False
        try:
            state = api.WaitForSingleObject(handle, 0)
            assert state in {0, 0x102}
            return state == 0x102
        finally:
            api.CloseHandle(handle)
    # A dead orphan may await its OS parent reaping it. It cannot execute code.
    status = Path(f"/proc/{pid}/stat")
    try:
        if status.exists() and status.read_text().rsplit(")", 1)[1].split()[0] == "Z":
            return False
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def test_plain_timeout_is_bounded_and_keeps_output(tmp_path):
    example = _example(tmp_path, "import time\nprint('before timeout', flush=True)\ntime.sleep(20)\nassert False\n")
    started = time.monotonic()
    ok, output = harness.run_example(example, 0.8)
    assert time.monotonic() - started < 4
    assert not ok and "exceeded 0.8 seconds" in output
    assert "before timeout" in output


@pytest.mark.parametrize("timeout", [False, True], ids=["successful-parent", "timed-out-parent"])
def test_success_and_timeout_clean_up_grandchildren(tmp_path, timeout):
    child_pid_file = tmp_path / "child.pid"
    leaf_pid_file = tmp_path / "leaf.pid"
    leaf_source = (
        "import os,sys,time\nfrom pathlib import Path\n"
        "Path(sys.argv[1]).write_text(str(os.getpid()))\n"
        "time.sleep(20)\n"
    )
    child_source = (
        "import os,subprocess,sys,time\nfrom pathlib import Path\n"
        f"subprocess.Popen([sys.executable, '-c', {leaf_source!r}, {str(leaf_pid_file)!r}])\n"
        f"Path({str(child_pid_file)!r}).write_text(str(os.getpid()))\n"
        "time.sleep(20)\n"
    )
    source = (
        "import subprocess,sys,time\nfrom pathlib import Path\n"
        f"subprocess.Popen([sys.executable, '-c', {child_source!r}])\n"
        "deadline = time.monotonic() + 3\n"
        f"while not (Path({str(child_pid_file)!r}).exists() and Path({str(leaf_pid_file)!r}).exists()):\n"
        "    assert time.monotonic() < deadline, 'descendants did not start'\n"
        "    time.sleep(0.01)\n"
        "print('descendants started', flush=True)\n"
        + ("time.sleep(20)\n" if timeout else "")
        + "assert True\n"
    )
    started = time.monotonic()
    ok, output = harness.run_example(_example(tmp_path, source), 1.5 if timeout else 5)
    assert time.monotonic() - started < 5
    assert ok is not timeout, output
    assert "descendants started" in output
    assert ("exceeded" in output) is timeout
    for path in (child_pid_file, leaf_pid_file):
        pid = int(path.read_text())
        deadline = time.monotonic() + 2
        while _process_is_running(pid) and time.monotonic() < deadline:
            time.sleep(0.01)
        assert not _process_is_running(pid), f"owned descendant {pid} survived cleanup"


def test_cleanup_does_not_kill_unrelated_process(tmp_path):
    unrelated = subprocess.Popen(
        [getattr(sys, "_base_executable", sys.executable), "-c", "import time; time.sleep(20)"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    try:
        example = _example(tmp_path, "assert 2 + 2 == 4\n")
        ok, output = harness.run_example(example, 5)
        assert ok, output
        assert unrelated.poll() is None
    finally:
        unrelated.kill()
        unrelated.wait(timeout=3)


def test_real_script_supports_multiprocessing_spawn(tmp_path):
    source = """import multiprocessing

def doubled(value):
    return value * 2

if __name__ == '__main__':
    with multiprocessing.get_context('spawn').Pool(1) as pool:
        assert pool.map(doubled, [2, 3]) == [4, 6]
    print('spawn worked')
"""
    ok, output = harness.run_example(_example(tmp_path, source), 10)
    assert ok and "spawn worked" in output, output


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object ownership gate")
@pytest.mark.parametrize("stage", ["assign", "resume_owned_launcher"])
def test_assignment_failure_never_releases_example(tmp_path, monkeypatch, stage):
    marker = tmp_path / "must-not-execute.txt"
    source = f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\nassert True\n"
    started = []
    original_popen = subprocess.Popen

    def tracked_popen(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        started.append(process)
        return process

    def fail_assignment(self, pid):
        raise OSError("forced assignment failure")

    monkeypatch.setattr(harness.subprocess, "Popen", tracked_popen)
    monkeypatch.setattr(harness._WindowsJob, stage, fail_assignment)
    ok, output = harness.run_example(_example(tmp_path, source), 5)
    assert not ok and "forced assignment failure" in output
    assert not marker.exists()
    assert len(started) == 1 and started[0].poll() is not None


def test_process_initialization_failure_is_reported(tmp_path, monkeypatch):
    def fail_popen(*args, **kwargs):
        raise OSError("forced process creation failure")

    monkeypatch.setattr(harness.subprocess, "Popen", fail_popen)
    ok, output = harness.run_example(_example(tmp_path, "assert True\n"), 5)
    assert not ok and "forced process creation failure" in output


@pytest.mark.skipif(os.name != "nt", reason="Windows late job member / file-sharing race")
def test_member_born_after_snapshot_is_still_cleaned_up(tmp_path, monkeypatch):
    ready = tmp_path / "child-ready"
    release = tmp_path / "release-child"
    leaf_pid = tmp_path / "late-leaf.pid"
    leaf_source = (
        "import os,time\nfrom pathlib import Path\n"
        f"Path({str(leaf_pid)!r}).write_text(str(os.getpid()))\n"
        "time.sleep(20)\n"
    )
    child_source = (
        "import subprocess,sys,time\nfrom pathlib import Path\n"
        f"Path({str(ready)!r}).write_text('ready')\n"
        "deadline = time.monotonic() + 5\n"
        f"while not Path({str(release)!r}).exists():\n"
        "    assert time.monotonic() < deadline\n"
        "    time.sleep(0.01)\n"
        f"subprocess.Popen([sys.executable, '-c', {leaf_source!r}])\n"
        "time.sleep(20)\n"
    )
    source = (
        "import subprocess,sys,time\nfrom pathlib import Path\n"
        f"subprocess.Popen([sys.executable, '-c', {child_source!r}])\n"
        "deadline = time.monotonic() + 3\n"
        f"while not Path({str(ready)!r}).exists():\n"
        "    assert time.monotonic() < deadline\n"
        "    time.sleep(0.01)\n"
        "assert True\n"
    )
    original = harness._WindowsJob._member_handles

    def snapshot_then_release(self, deadline):
        handles = original(self, deadline)
        release.write_text("go")
        while not leaf_pid.exists():
            if time.monotonic() >= deadline:
                for handle in handles:
                    self.api.CloseHandle(handle)
                raise OSError("late test member did not start")
            time.sleep(0.01)
        return handles

    monkeypatch.setattr(harness._WindowsJob, "_member_handles", snapshot_then_release)
    ok, output = harness.run_example(_example(tmp_path, source), 5)
    assert ok, output
    pid = int(leaf_pid.read_text())
    deadline = time.monotonic() + 2
    while _process_is_running(pid) and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not _process_is_running(pid)


def test_committed_handbook_has_unique_valid_examples():
    examples = harness.collect_examples(harness.HANDBOOK)
    assert examples
    assert {e.chapter for e in examples} == {f"{number:02}" for number in range(1, 26)}
