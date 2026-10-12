#!/usr/bin/env python3
"""Report GitHub repositories in the list that need a maintainer's attention.

For every github.com repository linked from the README, the GitHub API tells us
whether it is missing, moved, archived, or inactive. Inactivity is only
reported for main links (the first link of a list item, usually a tool),
because a paper's code repository is expected to go quiet once the paper
ships.

    GITHUB_TOKEN=... python3 scripts/check_currency.py --readme README.md --out report.md

The script always exits 0 when it could run. When $GITHUB_OUTPUT is set it
writes `findings` and `unchecked` counts there so a workflow can decide
whether to open an issue.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

LINK = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\[")
GITHUB_REPO = re.compile(r"^https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
# Paths under github.com/<owner>/ that are not repositories.
NOT_REPOS = {"orgs", "topics", "sponsors", "settings", "marketplace", "apps"}


@dataclass
class Repo:
    slug: str
    main_link: bool = False
    lines: list[int] = field(default_factory=list)


@dataclass
class Finding:
    slug: str
    kind: str
    detail: str
    lines: list[int]


def repo_slug(url: str) -> Optional[str]:
    match = GITHUB_REPO.match(url)
    if not match:
        return None
    owner, name = match.groups()
    if owner.lower() in NOT_REPOS:
        return None
    if name.endswith(".git"):
        name = name[:-4]
    return f"{owner}/{name}"


def extract_repos(text: str) -> dict[str, Repo]:
    """Map lowercase slugs to repositories, remembering if any use is a main link."""
    repos: dict[str, Repo] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        urls = LINK.findall(line)
        is_item = bool(LIST_ITEM.match(line))
        for position, url in enumerate(urls):
            slug = repo_slug(url)
            if slug is None:
                continue
            repo = repos.setdefault(slug.lower(), Repo(slug=slug))
            repo.lines.append(number)
            if is_item and position == 0:
                repo.main_link = True
    return repos


Fetcher = Callable[[str], tuple[int, Optional[dict]]]


def github_fetcher(token: Optional[str]) -> Fetcher:
    def fetch(slug: str) -> tuple[int, Optional[dict]]:
        request = urllib.request.Request(
            f"https://api.github.com/repos/{slug}",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "awesome-vericoding-currency-check",
                **({"Authorization": f"Bearer {token}"} if token else {}),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, None
        except (urllib.error.URLError, TimeoutError):
            return 0, None

    return fetch


def classify(repo: Repo, status: int, data: Optional[dict], now: datetime, inactive_days: int) -> Optional[Finding]:
    """Return a finding for this repository, or None if it looks healthy.

    Raises LookupError when the API could not answer (rate limits, outages),
    so that an unchecked repository is never mistaken for a healthy one.
    """
    if status == 404:
        return Finding(repo.slug, "missing", "repository not found", repo.lines)
    if status != 200 or data is None:
        raise LookupError(f"{repo.slug}: HTTP {status}")
    full_name = data.get("full_name", repo.slug)
    if full_name.lower() != repo.slug.lower():
        return Finding(repo.slug, "moved", f"now at https://github.com/{full_name}", repo.lines)
    if data.get("archived"):
        return Finding(repo.slug, "archived", "repository is archived", repo.lines)
    pushed = data.get("pushed_at")
    if repo.main_link and pushed:
        last_push = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        if now - last_push > timedelta(days=inactive_days):
            return Finding(repo.slug, "inactive", f"no pushes since {last_push.date()}", repo.lines)
    return None


def check(repos: dict[str, Repo], fetch: Fetcher, now: datetime, inactive_days: int) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    unchecked: list[str] = []
    for repo in sorted(repos.values(), key=lambda r: r.slug.lower()):
        status, data = fetch(repo.slug)
        try:
            finding = classify(repo, status, data, now, inactive_days)
        except LookupError as error:
            unchecked.append(str(error))
            continue
        if finding:
            findings.append(finding)
    return findings, unchecked


def render(findings: list[Finding], unchecked: list[str], total: int, inactive_days: int) -> str:
    titles = {
        "missing": "Missing",
        "moved": "Moved (update the link)",
        "archived": "Archived",
        "inactive": f"Inactive for more than {inactive_days} days (main links only)",
    }
    out = [
        "# List currency report",
        "",
        f"Checked {total} GitHub repositories: {len(findings)} need attention, {len(unchecked)} could not be checked.",
        "",
    ]
    for kind, title in titles.items():
        group = [f for f in findings if f.kind == kind]
        if not group:
            continue
        out += [f"## {title}", ""]
        for f in group:
            where = ", ".join(f"L{n}" for n in f.lines)
            out.append(f"- [ ] [{f.slug}](https://github.com/{f.slug}): {f.detail} (README {where})")
        out.append("")
    if unchecked:
        out += ["## Could not be checked", ""] + [f"- {u}" for u in unchecked] + [""]
    out += [
        "Archived or inactive tools should be removed, or kept only with a reason recorded in the pull request.",
        "",
    ]
    return "\n".join(out)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--readme", default="README.md")
    parser.add_argument("--out", default="currency-report.md")
    parser.add_argument("--inactive-days", type=int, default=365)
    args = parser.parse_args(argv)

    with open(args.readme, encoding="utf-8") as handle:
        repos = extract_repos(handle.read())
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    findings, unchecked = check(repos, github_fetcher(token), datetime.now(timezone.utc), args.inactive_days)

    report = render(findings, unchecked, len(repos), args.inactive_days)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(report)
    print(report)

    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write(f"findings={len(findings)}\nunchecked={len(unchecked)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
