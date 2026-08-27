"""Run every standard-library practice script with the current interpreter."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LABS = [
    ROOT / "examples" / "basics_lab.py",
    ROOT / "examples" / "functions_lab.py",
    ROOT / "examples" / "oop_lab.py",
    ROOT / "examples" / "concurrency_lab.py",
    ROOT / "examples" / "pitfalls_lab.py",
]


def main() -> int:
    child_environment = os.environ.copy()
    child_environment["PYTHONUTF8"] = "1"

    for lab in LABS:
        relative_path = lab.relative_to(ROOT)
        print(f"\nrunning {relative_path}", flush=True)
        completed = subprocess.run(
            [sys.executable, str(lab)],
            cwd=ROOT,
            check=False,
            env=child_environment,
        )
        if completed.returncode != 0:
            print(f"failed: {relative_path}")
            return completed.returncode

    print("\nall practice scripts passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
