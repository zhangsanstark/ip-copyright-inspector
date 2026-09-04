"""Check that Markdown notes use the repository's low-profile text style."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIPPED_PARTS = {
    ".git", ".venv", "node_modules", "dist", "build", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "__pycache__", ".practice",
}
ATX_HEADING = re.compile(r"^\s{0,3}#{1,6}(?:\s|$)")
HTML_HEADING = re.compile(r"<\s*h[1-6](?:\s|>)", re.IGNORECASE)
SETEXT_MARK = re.compile(r"^\s*(?:=+|-+)\s*$")
BOLD_TEXT = re.compile(r"(?:\*\*|__)(?=\S).+?(?<=\S)(?:\*\*|__)")
INLINE_CODE = re.compile(r"`[^`]*`")


@dataclass(frozen=True)
class Violation:
    path: Path
    line_number: int
    reason: str
    line: str


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not any(part in SKIPPED_PARTS for part in path.parts)
    )


def inspect_file(path: Path) -> list[Violation]:
    violations: list[Violation] = []
    in_fence = False
    fence_token = ""
    previous_visible = ""

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = raw_line.lstrip()
        if stripped.startswith(("```", "~~~")):
            token = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_token = token
            elif token == fence_token:
                in_fence = False
                fence_token = ""
            previous_visible = ""
            continue

        if in_fence:
            continue

        visible = INLINE_CODE.sub("", raw_line)
        reason = ""
        if ATX_HEADING.search(visible):
            reason = "使用了井号 Markdown 标题"
        elif HTML_HEADING.search(visible):
            reason = "使用了 HTML 标题标签"
        elif SETEXT_MARK.fullmatch(visible) and previous_visible.strip():
            reason = "使用了下划线式 Markdown 标题"
        elif BOLD_TEXT.search(visible):
            reason = "使用了粗体文字模拟强调或标题"

        if reason:
            violations.append(Violation(path, line_number, reason, raw_line))

        previous_visible = visible

    return violations


def main() -> int:
    violations = [
        violation
        for path in markdown_files()
        for violation in inspect_file(path)
    ]

    if not violations:
        print("note format check passed")
        return 0

    for violation in violations:
        relative_path = violation.path.relative_to(ROOT)
        print(
            f"{relative_path}:{violation.line_number}: "
            f"{violation.reason}: {violation.line.strip()}"
        )
    print(f"note format check failed: {len(violations)} violation(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
