#!/usr/bin/env python3
"""Extract the code from the primers and run each one through its verifier.

Every primer in primers/ holds exactly one fenced code block, and its front
matter names the file that block should be saved as. A primer is checked by a
script at scripts/primers/<name>.sh, which installs a pinned version of the
tool when it is missing and exits non-zero when the code does not verify.

    python3 scripts/primers.py names              # every primer, one per line
    python3 scripts/primers.py list               # primers with a check script, as JSON
    python3 scripts/primers.py list --changed primers/dafny.md  # only those a change affects
    python3 scripts/primers.py extract dafny DIR  # write DIR/learndafny.dfy
    python3 scripts/primers.py check dafny lean   # extract and verify each one

Tools are installed under $PRIMER_CACHE (default ~/.cache/awesome-vericoding),
which the Primers workflow caches between runs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIMERS = ROOT / "primers"
CHECKS = ROOT / "scripts" / "primers"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
FENCE = re.compile(r"^```[^\n]*\n(.*?)^```[ \t]*$", re.S | re.M)


class PrimerError(Exception):
    pass


def names() -> list[str]:
    return sorted(p.stem for p in PRIMERS.glob("*.md"))


def checked() -> list[str]:
    return sorted(p.stem for p in CHECKS.glob("*.sh") if (PRIMERS / f"{p.stem}.md").exists())


# A change to one of these can affect every primer's check.
SHARED = {"scripts/primers.py", ".github/workflows/primers.yml"}


def affected(changed: list[str]) -> list[str]:
    """Primers with a check script that a change to these paths could break."""
    if SHARED.intersection(changed):
        return checked()
    touched = {Path(path).stem for path in changed if path.startswith(("primers/", "scripts/primers/"))}
    return [name for name in checked() if name in touched]


def parse(text: str) -> tuple[str, str]:
    """Return (filename, code) for one primer's Markdown source."""
    match = FRONT_MATTER.match(text)
    if not match:
        raise PrimerError("no front matter")
    filename = None
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "filename":
            filename = value.strip().strip("\"'")
    if not filename:
        raise PrimerError("front matter has no filename")
    if "/" in filename or filename.startswith("."):
        raise PrimerError(f"filename {filename!r} is not a plain file name")
    blocks = FENCE.findall(text[match.end():])
    if len(blocks) != 1:
        raise PrimerError(f"expected one code block, found {len(blocks)}")
    return filename, blocks[0]


def extract(name: str, directory: Path) -> Path:
    source = PRIMERS / f"{name}.md"
    if not source.exists():
        raise PrimerError(f"no primer named {name!r}")
    try:
        filename, code = parse(source.read_text(encoding="utf-8"))
    except PrimerError as error:
        raise PrimerError(f"{source.relative_to(ROOT)}: {error}") from None
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(code, encoding="utf-8")
    return path


def check(name: str, keep: bool = False) -> int:
    script = CHECKS / f"{name}.sh"
    if not script.exists():
        print(f"::warning::{name}: no check script at {script.relative_to(ROOT)}", flush=True)
        return 1
    work = Path(tempfile.mkdtemp(prefix=f"primer-{name}-"))
    path = extract(name, work)
    print(f"--- {name}: {script.relative_to(ROOT)} {path}", flush=True)
    result = subprocess.run(["bash", str(script), str(path)], cwd=work)
    if keep:
        print(f"    kept {work}", flush=True)
    else:
        subprocess.run(["rm", "-rf", str(work)])
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("names", help="print every primer, one per line")
    listing = commands.add_parser("list", help="print primers that have a check script, as JSON")
    listing.add_argument("--changed", nargs="*", metavar="PATH", help="only primers these changed paths affect")
    one = commands.add_parser("extract", help="write a primer's code to a directory")
    one.add_argument("name")
    one.add_argument("directory", nargs="?", default=".")
    many = commands.add_parser("check", help="extract primers and run their check scripts")
    many.add_argument("names", nargs="*", help="default: every primer with a check script")
    many.add_argument("--keep", action="store_true", help="keep the extracted files")
    args = parser.parse_args(argv)

    try:
        if args.command == "names":
            print("\n".join(names()))
            return 0
        if args.command == "list":
            print(json.dumps(checked() if args.changed is None else affected(args.changed)))
            return 0
        if args.command == "extract":
            print(extract(args.name, Path(args.directory).resolve()))
            return 0
        failed = [name for name in (args.names or checked()) if check(name, args.keep) != 0]
    except PrimerError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if failed:
        print(f"Failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
