"""Validate and run trusted, explicitly marked handbook examples in isolation.

This is a convenience runner, not a security sandbox. Only run a handbook whose
code you trust. Each example gets a separate process and temporary directory.
Ordinary child processes are cleaned up on success as well as failure. Windows
uses a private Job Object; POSIX uses a new process group. POSIX examples must
not detach with setsid/setpgid or launch work through an external service.
The execution timeout has a separate, bounded five-second cleanup allowance.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
HANDBOOK = ROOT / "docs" / "handbook"
CHAPTER_NAME = re.compile(r"^(\d{2})-.+\.md$")
MARKER = re.compile(r"^# (runnable|fragment|optional):\s*(\S.*)$")
EXAMPLE_ID = re.compile(r"^hb(\d{2})_[a-z0-9_]+$")
CLEANUP_TIMEOUT = 5.0
BOOTSTRAP = """import runpy
import sys

# The runner releases this gate only after process ownership is established.
if sys.stdin.buffer.read(1) != b'G':
    raise SystemExit('runner did not authorize example execution')
sys.stdin.close()
sys.stdin = open(__import__('os').devnull, encoding='utf-8')
sys.argv = [sys.argv[1]]
runpy.run_path(sys.argv[0], run_name='__main__')
"""


@dataclass(frozen=True)
class Example:
    path: Path
    line: int
    chapter: str
    kind: str
    name: str
    code: str


def parse_chapter(path: Path) -> list[Example]:
    """Extract Python fences, rejecting unmarked or unverifiable runnable code."""
    match = CHAPTER_NAME.fullmatch(path.name)
    if match is None:
        raise ValueError(f"not a numbered chapter: {path}")
    chapter = match.group(1)
    examples: list[Example] = []
    fence = ""
    language = ""
    start = 0
    body: list[str] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        if not fence:
            opening = re.fullmatch(r"(`{3,}|~{3,})([^`~]*)", stripped)
            if opening:
                fence, language = opening.groups()
                language = language.strip().lower()
                start, body = number + 1, []
            continue
        if re.fullmatch(re.escape(fence[0]) + "{" + str(len(fence)) + ",}", stripped):
            if language in {"python", "py"}:
                marker = MARKER.fullmatch(body[0]) if body else None
                if marker is None:
                    raise ValueError(f"{path}:{start}: Python block needs an explicit marker")
                kind, name = marker.groups()
                code = "\n".join(body) + "\n"
                if kind == "runnable":
                    id_match = EXAMPLE_ID.fullmatch(name)
                    if id_match is None or id_match.group(1) != chapter:
                        raise ValueError(f"{path}:{start}: invalid chapter example id: {name}")
                    try:
                        tree = ast.parse(code, filename=f"{path}:{start}")
                    except SyntaxError as exc:
                        raise ValueError(f"{path}:{start}: invalid runnable Python: {exc}") from exc
                    if not any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
                        raise ValueError(f"{path}:{start}: runnable block needs an assert")
                examples.append(Example(path, start, chapter, kind, name, code))
            fence, language, body = "", "", []
        else:
            body.append(raw)
    if fence:
        raise ValueError(f"{path}:{start}: unclosed code fence")
    return examples


def collect_examples(directory: Path, chapters: set[str] | None = None) -> list[Example]:
    examples: list[Example] = []
    identifiers: set[str] = set()
    for path in sorted(directory.glob("[0-9][0-9]-*.md")):
        if chapters is not None and path.name[:2] not in chapters:
            continue
        for example in parse_chapter(path):
            if example.kind == "runnable":
                if example.name in identifiers:
                    raise ValueError(f"duplicate example id: {example.name}")
                identifiers.add(example.name)
            examples.append(example)
    return examples


def export_examples(examples: list[Example], destination: Path) -> int:
    """Create standalone scripts without replacing any existing file."""
    runnable = [example for example in examples if example.kind == "runnable"]
    targets = [destination / f"{example.name}.py" for example in runnable]
    if any(target.exists() for target in targets):
        raise ValueError("export would overwrite an existing script; choose a new directory")
    destination.mkdir(parents=True, exist_ok=True)
    for example, target in zip(runnable, targets, strict=True):
        with target.open("x", encoding="utf-8") as output:
            output.write(example.code)
    return len(runnable)


class _WindowsJob:
    """Own only the gated example and its CreateProcess descendants.

    No breakaway flags are enabled. If job setup/assignment is unsupported,
    fail before releasing the bootstrap gate rather than running uncontained.
    https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
    """

    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount",
            )]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimits),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        class Accounting(ctypes.Structure):
            _fields_ = [
                ("TotalUserTime", ctypes.c_longlong),
                ("TotalKernelTime", ctypes.c_longlong),
                ("ThisPeriodTotalUserTime", ctypes.c_longlong),
                ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
                ("TotalPageFaultCount", wintypes.DWORD),
                ("TotalProcesses", wintypes.DWORD),
                ("ActiveProcesses", wintypes.DWORD),
                ("TotalTerminatedProcesses", wintypes.DWORD),
            ]

        class ThreadEntry(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ThreadID", wintypes.DWORD),
                ("th32OwnerProcessID", wintypes.DWORD),
                ("tpBasePri", wintypes.LONG),
                ("tpDeltaPri", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
            ]

        self.ctypes = ctypes
        self.accounting_type = Accounting
        self.thread_entry_type = ThreadEntry
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "TerminateJobObject": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            "QueryInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
            "CreateToolhelp32Snapshot": ([wintypes.DWORD, wintypes.DWORD], wintypes.HANDLE),
            "Thread32First": ([wintypes.HANDLE, ctypes.POINTER(ThreadEntry)], wintypes.BOOL),
            "Thread32Next": ([wintypes.HANDLE, ctypes.POINTER(ThreadEntry)], wintypes.BOOL),
            "OpenThread": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "GetProcessIdOfThread": ([wintypes.HANDLE], wintypes.DWORD),
            "ResumeThread": ([wintypes.HANDLE], wintypes.DWORD),
            "IsProcessInJob": ([wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL),
            "WaitForSingleObject": ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.api, name)
            function.argtypes = arguments
            function.restype = result
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            self._error("create")
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x00002000  # KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(
            self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            error = ctypes.get_last_error()
            self.close()
            raise OSError(f"Windows Job Object limit setup failed: {ctypes.WinError(error)}")

    def _error(self, operation: str) -> None:
        error = self.ctypes.WinError(self.ctypes.get_last_error())
        raise OSError(f"Windows Job Object {operation} failed: {error}")

    def assign(self, pid: int) -> None:
        # AssignProcessToJobObject requires SET_QUOTA | TERMINATE rights.
        process_handle = self.api.OpenProcess(0x0100 | 0x0001, False, pid)
        if not process_handle:
            self._error("open child")
        try:
            if not self.api.AssignProcessToJobObject(self.handle, process_handle):
                self._error("assign child")
        finally:
            self.api.CloseHandle(process_handle)

    def resume_owned_launcher(self, pid: int) -> None:
        """Resume the sole thread of the new, suspended, already assigned PID.

        Windows venv python.exe can launch the actual interpreter before a
        Python-level gate executes. CREATE_SUSPENDED closes that earlier race.
        Popen does not expose its primary thread handle, so use the documented
        Tool Help APIs and verify the opened thread's owner before resuming it.
        https://learn.microsoft.com/en-us/windows/win32/toolhelp/traversing-the-thread-list
        """
        snapshot = self.api.CreateToolhelp32Snapshot(0x00000004, 0)  # SNAPTHREAD
        if snapshot == self.ctypes.c_void_p(-1).value:
            self._error("snapshot suspended launcher thread")
        thread_ids = []
        try:
            entry = self.thread_entry_type()
            entry.dwSize = self.ctypes.sizeof(entry)
            if not self.api.Thread32First(snapshot, self.ctypes.byref(entry)):
                self._error("find suspended launcher thread")
            while True:
                if entry.th32OwnerProcessID == pid:
                    thread_ids.append(entry.th32ThreadID)
                if not self.api.Thread32Next(snapshot, self.ctypes.byref(entry)):
                    if self.ctypes.get_last_error() != 18:  # NO_MORE_FILES
                        self._error("enumerate suspended launcher thread")
                    break
        finally:
            self.api.CloseHandle(snapshot)
        if len(thread_ids) != 1:
            raise OSError("cannot safely identify the suspended launcher's sole thread")
        # SUSPEND_RESUME | QUERY_LIMITED_INFORMATION, not access to other threads.
        thread = self.api.OpenThread(0x0002 | 0x0800, False, thread_ids[0])
        if not thread:
            self._error("open suspended launcher thread")
        try:
            if self.api.GetProcessIdOfThread(thread) != pid:
                raise OSError("suspended launcher thread ownership changed")
            previous_count = self.api.ResumeThread(thread)
            if previous_count == 0xFFFFFFFF:
                self._error("resume suspended launcher")
            if previous_count != 1:
                raise OSError("unexpected launcher suspension count; refusing to execute")
        finally:
            self.api.CloseHandle(thread)

    def _member_handles(self, deadline: float) -> list[int]:
        """Capture waitable handles while membership, rather than PID, is known."""
        from ctypes import wintypes

        capacity = 16
        while True:
            class ProcessIds(self.ctypes.Structure):
                _fields_ = [
                    ("NumberOfAssignedProcesses", wintypes.DWORD),
                    ("NumberOfProcessIdsInList", wintypes.DWORD),
                    ("ProcessIdList", self.ctypes.c_size_t * capacity),
                ]

            identifiers = ProcessIds()
            if self.api.QueryInformationJobObject(
                self.handle, 3, self.ctypes.byref(identifiers),
                self.ctypes.sizeof(identifiers), None,
            ):
                break
            if self.ctypes.get_last_error() != 234:  # MORE_DATA
                self._error("list job members")
            if time.monotonic() >= deadline:
                raise OSError("Windows Job Object member query exceeded cleanup deadline")
            capacity = max(capacity * 2, identifiers.NumberOfAssignedProcesses)
        handles = []
        try:
            for pid in identifiers.ProcessIdList[:identifiers.NumberOfProcessIdsInList]:
                # SYNCHRONIZE | QUERY_LIMITED_INFORMATION; no terminate permission.
                handle = self.api.OpenProcess(0x00100000 | 0x1000, False, pid)
                if not handle:
                    if self.ctypes.get_last_error() == 87:  # Already gone.
                        continue
                    self._error("open job member for exit wait")
                member = wintypes.BOOL()
                if not self.api.IsProcessInJob(handle, self.handle, self.ctypes.byref(member)):
                    self.api.CloseHandle(handle)
                    self._error("verify job member")
                if member.value:
                    handles.append(handle)
                else:
                    self.api.CloseHandle(handle)
            return handles
        except BaseException:
            for handle in handles:
                self.api.CloseHandle(handle)
            raise

    def terminate(self, deadline: float) -> None:
        handles = self._member_handles(deadline)
        try:
            if not self.api.TerminateJobObject(self.handle, 1):
                self._error("terminate")
            while True:
                accounting = self.accounting_type()
                if not self.api.QueryInformationJobObject(
                    self.handle, 1, self.ctypes.byref(accounting),
                    self.ctypes.sizeof(accounting), None,
                ):
                    self._error("query active processes")
                if accounting.ActiveProcesses == 0:
                    break
                if time.monotonic() >= deadline:
                    raise OSError("Windows Job Object cleanup exceeded five seconds")
                time.sleep(0.01)
            # ActiveProcesses reaches zero before all exiting processes release
            # their file handles. Wait for process objects, not the job signal.
            for handle in handles:
                remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
                state = self.api.WaitForSingleObject(handle, remaining_ms)
                if state == 0xFFFFFFFF:
                    self._error("wait for member exit")
                if state != 0:
                    raise OSError("Windows Job Object member exit exceeded cleanup deadline")
        finally:
            for handle in handles:
                self.api.CloseHandle(handle)

    def close(self) -> None:
        if self.handle:
            handle, self.handle = self.handle, None
            if not self.api.CloseHandle(handle):
                self._error("close")


class _ExampleDirectory(tempfile.TemporaryDirectory):
    """Retry only Windows file-sharing races within the same cleanup budget."""

    cleanup_deadline: float | None = None

    def cleanup(self) -> None:
        deadline = self.cleanup_deadline
        if deadline is None:
            deadline = time.monotonic() + CLEANUP_TIMEOUT
        while True:
            try:
                super().cleanup()
                return
            except OSError as exc:
                # Job members born between the handle snapshot and termination
                # are killed too, but their final handle release can lag behind
                # ActiveProcesses==0. Do not hide other errors or wait forever.
                remaining = deadline - time.monotonic()
                if os.name != "nt" or getattr(exc, "winerror", None) not in {32, 33} or remaining <= 0:
                    raise
                time.sleep(min(0.02, remaining))


def _stop_process_tree(
    process: subprocess.Popen, job: _WindowsJob | None, deadline: float
) -> None:
    """Terminate only this invocation's job/group, then reap its direct child."""
    errors: list[str] = []
    try:
        if job is not None:
            job.terminate(deadline)
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    except OSError as exc:
        errors.append(str(exc))
    finally:
        if job is not None:
            try:
                # KILL_ON_JOB_CLOSE also protects the termination-error path.
                job.close()
            except OSError as exc:
                errors.append(str(exc))
        # Assignment may have failed while the bootstrap was still gated.
        try:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=max(0.001, deadline - time.monotonic()))
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"direct child cleanup failed: {exc}")
        if process.stdin is not None:
            process.stdin.close()
    if errors:
        raise OSError("; ".join(errors))


def run_example(example: Example, timeout: float) -> tuple[bool, str]:
    if os.name not in {"nt", "posix"}:
        raise OSError(f"process-tree cleanup is unsupported on platform {os.name!r}")
    if not 0 < timeout <= 300:
        raise ValueError("timeout must be greater than zero and at most 300")
    environment = os.environ.copy()
    environment.pop("PYTHONOPTIMIZE", None)
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(ROOT / "src"), environment.get("PYTHONPATH", "")) if part
    )
    temporary = _ExampleDirectory(prefix="ip-handbook-")
    with temporary as directory:
        # runpy preserves a real __main__.__file__ for multiprocessing spawn.
        script = Path(directory) / f"{example.name}.py"
        script.write_text(example.code, encoding="utf-8")
        bootstrap = Path(directory) / "_runner_bootstrap.py"
        bootstrap.write_text(BOOTSTRAP, encoding="utf-8")
        stdout_path, stderr_path = Path(directory) / "stdout.txt", Path(directory) / "stderr.txt"
        # File capture does not wait for EOF on pipes inherited by descendants.
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            job = _WindowsJob() if os.name == "nt" else None
            process = None
            ok, detail = False, ""
            try:
                started = time.monotonic()
                process = subprocess.Popen(
                    [sys.executable, "-X", "utf8", str(bootstrap), str(script)],
                    cwd=directory, env=environment, stdin=subprocess.PIPE,
                    stdout=stdout, stderr=stderr,
                    start_new_session=os.name == "posix",
                    # Suspend even the venv launcher until Job assignment.
                    creationflags=(subprocess.CREATE_NO_WINDOW | 0x00000004) if os.name == "nt" else 0,
                )
                if job is not None:
                    job.assign(process.pid)
                    job.resume_owned_launcher(process.pid)
                assert process.stdin is not None
                process.stdin.write(b"G")
                process.stdin.flush()
                process.stdin.close()
                ok = process.wait(timeout=max(0.001, timeout - (time.monotonic() - started))) == 0
            except subprocess.TimeoutExpired:
                detail = f"exceeded {timeout:g} seconds"
            except OSError as exc:
                detail = f"process setup/execution failed: {exc}"
            finally:
                temporary.cleanup_deadline = time.monotonic() + CLEANUP_TIMEOUT
                try:
                    if process is not None:
                        _stop_process_tree(process, job, temporary.cleanup_deadline)
                    elif job is not None:
                        job.close()
                except OSError as exc:
                    ok = False
                    detail += f"\nprocess-tree cleanup failed: {exc}"
        output = stdout_path.read_text(encoding="utf-8", errors="replace")
        output += stderr_path.read_text(encoding="utf-8", errors="replace")
        if detail:
            output = detail.strip() + "\n" + output
        return ok, output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", nargs="+", help="chapter numbers, e.g. 01 08")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--list", action="store_true", help="list blocks without executing them")
    action.add_argument("--export", type=Path, help="export standalone .py files without running or overwriting")
    parser.add_argument("--show-output", action="store_true", help="also print successful output")
    parser.add_argument("--timeout", type=float, default=40, help="seconds per runnable block")
    args = parser.parse_args(argv)
    if not 0 < args.timeout <= 300:
        parser.error("--timeout must be greater than zero and at most 300")
    available = {p.name[:2] for p in HANDBOOK.glob("[0-9][0-9]-*.md")}
    requested = set(args.chapter or available)
    unknown = requested - available
    if unknown:
        parser.error("unknown chapters: " + ", ".join(sorted(unknown)))
    try:
        selected = collect_examples(HANDBOOK, requested)
    except (OSError, ValueError) as exc:
        print(f"handbook check failed: {exc}", file=sys.stderr)
        return 1
    runnable = [example for example in selected if example.kind == "runnable"]
    skipped = [example for example in selected if example.kind != "runnable"]
    if not runnable:
        print("no runnable examples selected", file=sys.stderr)
        return 1
    if args.list:
        for example in selected:
            print(f"{example.kind}: {example.name} ({example.path.name}:{example.line})")
    elif args.export is not None:
        try:
            count = export_examples(selected, args.export.resolve())
        except (OSError, ValueError) as exc:
            print(f"export failed: {exc}", file=sys.stderr)
            return 1
        print(f"exported {count} scripts to {args.export.resolve()}")
    else:
        failures = 0
        for example in runnable:
            try:
                ok, output = run_example(example, args.timeout)
            except OSError as exc:
                ok, output = False, f"environment/file access error: {exc}"
            print(f"{'PASS' if ok else 'FAIL'} {example.name}", flush=True)
            if output and (args.show_output or not ok):
                print(output.rstrip(), flush=True)
            if not ok:
                failures += 1
                print(f"  source: {example.path}:{example.line}")
        print(f"runnable: {len(runnable)}, passed: {len(runnable) - failures}, failed: {failures}")
        if failures:
            return 1
    print(f"fragment/optional blocks not executed: {len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
