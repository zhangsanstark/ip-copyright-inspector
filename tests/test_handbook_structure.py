"""Keep a large plain-text handbook navigable when individual chapters change."""

from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
HANDBOOK = ROOT / "docs" / "handbook"
CHAPTERS = sorted(HANDBOOK.glob("[0-9][0-9]-*.md"))


def prose_lines(path):
    fence = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        opening = re.match(r"^\s*(`{3,}|~{3,})", line)
        if opening:
            token = opening.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            yield number, line
    assert fence is None, f"unclosed fence in {path.name}"


def test_numbered_chapters_cover_reading_sequence():
    assert [path.name[:2] for path in CHAPTERS] == [f"{number:02}" for number in range(1, 26)]


@pytest.mark.parametrize("path", CHAPTERS, ids=lambda path: path.name[:2])
def test_plain_section_numbers_are_continuous(path):
    main_number = 0
    sub_number = 0
    for line_number, line in prose_lines(path):
        main = re.match(r"^(\d+)）", line)
        sub = re.match(r"^(\d+)\.(\d+)\s", line)
        if main:
            assert int(main.group(1)) == main_number + 1, f"{path.name}:{line_number}"
            main_number += 1
            sub_number = 0
        elif sub:
            assert int(sub.group(1)) == main_number, f"{path.name}:{line_number} wrong parent"
            assert int(sub.group(2)) == sub_number + 1, f"{path.name}:{line_number} discontinuous subsection"
            sub_number += 1
    assert main_number >= 5, f"{path.name} has no usable section structure"


def test_relative_handbook_links_resolve():
    paths = list(HANDBOOK.glob("*.md")) + [ROOT / "README.md", ROOT / "docs" / "README.md",
                                          ROOT / "examples" / "README.md"]
    for path in paths:
        for number, line in prose_lines(path):
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", line):
                if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                    continue
                target = target.split("#", 1)[0].strip("<>")
                assert (path.parent / target).resolve().is_file(), f"{path.name}:{number}: {target}"


def test_markdown_table_columns_are_not_split_by_unescaped_code_pipes():
    for path in HANDBOOK.glob("*.md"):
        expected = None
        for number, line in prose_lines(path):
            if line.startswith("|"):
                count = len(re.findall(r"(?<!\\)\|", line))
                if expected is None:
                    expected = count
                assert count == expected, f"{path.name}:{number}: escape pipes inside table cells"
            else:
                expected = None


def test_handbook_does_not_use_oversized_heading_markup():
    for path in HANDBOOK.glob("*.md"):
        for number, line in prose_lines(path):
            assert not re.match(r"^\s{0,3}#{1,6}(\s|$)", line), f"{path.name}:{number}"
            assert not re.search(r"<h[1-6](?:\s|>)", line, re.IGNORECASE), f"{path.name}:{number}"
