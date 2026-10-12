#!/usr/bin/env python3
"""Align the pipes of every Markdown table in the given files.

awesome-lint enforces remark-lint's table-pipe-alignment and table-cell-padding
rules, so a contributor who adds a table row would otherwise have to re-pad
every row by hand. Run this instead:

    python3 scripts/align_tables.py README.md

The script rewrites files in place and exits with status 1 if it changed
anything, which lets pre-commit report the fix.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

# A pipe that is not escaped with a backslash separates two cells.
CELL_SPLIT = re.compile(r"(?<!\\)\|")
DELIMITER_CELL = re.compile(r"^:?-+:?$")


def display_width(text: str) -> int:
    """Approximate the rendered width of text in a monospace editor."""
    width = 0
    for char in text:
        if unicodedata.combining(char):
            continue
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def split_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|") and not stripped.endswith("\\|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in CELL_SPLIT.split(stripped)]


def is_delimiter_row(cells: list[str]) -> bool:
    return all(DELIMITER_CELL.match(cell) for cell in cells)


def format_delimiter(cell: str, width: int) -> str:
    left = cell.startswith(":")
    right = cell.endswith(":")
    dashes = width - left - right
    return (":" if left else "") + "-" * dashes + (":" if right else "")


def align_table(lines: list[str]) -> list[str]:
    rows = [split_row(line) for line in lines]
    columns = max(len(row) for row in rows)
    for row in rows:
        row.extend([""] * (columns - len(row)))

    widths = [3] * columns
    for row in rows:
        if is_delimiter_row(row):
            continue
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], display_width(cell))

    output = []
    for row in rows:
        if is_delimiter_row(row):
            cells = [format_delimiter(cell, widths[i]) for i, cell in enumerate(row)]
        else:
            cells = [cell + " " * (widths[i] - display_width(cell)) for i, cell in enumerate(row)]
        output.append("| " + " | ".join(cells) + " |")
    return output


def align_text(text: str) -> str:
    lines = text.split("\n")
    result: list[str] = []
    in_fence = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.lstrip().startswith("|"):
            block = []
            while index < len(lines) and lines[index].lstrip().startswith("|"):
                block.append(lines[index])
                index += 1
            # Only treat the block as a table if its second row is a delimiter row.
            if len(block) >= 2 and is_delimiter_row(split_row(block[1])):
                result.extend(align_table(block))
            else:
                result.extend(block)
            continue
        result.append(line)
        index += 1
    return "\n".join(result)


def main(paths: list[str]) -> int:
    changed = False
    for name in paths or ["README.md"]:
        path = Path(name)
        original = path.read_text(encoding="utf-8")
        aligned = align_text(original)
        if aligned != original:
            path.write_text(aligned, encoding="utf-8")
            print(f"aligned tables in {path}")
            changed = True
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
