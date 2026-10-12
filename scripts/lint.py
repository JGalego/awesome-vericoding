#!/usr/bin/env python3
"""Run awesome-lint, treating environment-dependent rules as warnings.

Two awesome-lint rules depend on the repository rather than the list:
`awesome-git-repo-age` fails until the first commit is 30 days old, and
`awesome-github` needs a GitHub remote with a description, topics, and a
license. Failing on those would block every commit to a new or offline clone,
so by default they are reported but do not fail the run. Every other rule
fails it.

    python3 scripts/lint.py           # day-to-day and in pull requests
    python3 scripts/lint.py --strict  # before submitting to sindresorhus/awesome
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys

AWESOME_LINT = "awesome-lint@2.3.0"
ENVIRONMENT_RULES = {"awesome-git-repo-age", "awesome-github"}
MESSAGE = re.compile(r"^\s*[✖⚠]\s+(?:\d+:\d+\s+)?(?P<text>.*?)\s{2,}(?P<rule>[\w:-]+)\s*$")


def command() -> list[str]:
    # Prefer a binary on PATH (pre-commit installs one); fall back to npx.
    if shutil.which("awesome-lint"):
        return ["awesome-lint"]
    return ["npx", "--yes", AWESOME_LINT]


def parse(output: str) -> list[tuple[str, str]]:
    messages = []
    for line in output.splitlines():
        match = MESSAGE.match(line)
        if match:
            rule = match.group("rule").removeprefix("remark-lint:")
            messages.append((rule, match.group("text")))
    return messages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true", help="also fail on repository age and GitHub metadata")
    args = parser.parse_args()

    env = {**os.environ, "FORCE_COLOR": "0", "NO_COLOR": "1"}
    result = subprocess.run(command(), capture_output=True, text=True, env=env)
    output = result.stdout + result.stderr
    messages = parse(output)

    if result.returncode != 0 and not messages:
        print(output)
        print("awesome-lint failed without reporting any rule; see the output above.", file=sys.stderr)
        return 1

    failures = [(rule, text) for rule, text in messages if args.strict or rule not in ENVIRONMENT_RULES]
    for rule, text in messages:
        level = "error" if (rule, text) in failures else "warning"
        print(f"{level}: {text} ({rule})")

    if failures:
        print(f"awesome-lint: {len(failures)} error(s).")
        return 1
    print("awesome-lint: no errors" + ("." if not messages else " (environment warnings only)."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
