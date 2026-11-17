#!/usr/bin/env python3
"""Build the site's "What's New" page and Atom feed from the README's history.

An entry's date is the first commit that added a line linking its URL or
naming it, so moving or rewording an entry does not make it new again.
Entries from the list's first day are the starting list and are left out.

    python3 scripts/whats_new.py --page new.html --feed feed.xml

The Pages workflow runs this before the Jekyll build, with the full history
checked out. The output is not committed.
"""

from __future__ import annotations

import argparse
import html
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from build_data import LINK, ROOT, build, unescape

SITE = "https://jgalego.github.io/awesome-vericoding/"
FEED_SIZE = 50
RECORD, FIELD = "\x1e", "\x1f"


def git_log(repo: Path) -> str:
    """The README's history, oldest first, with only the added lines of each diff."""
    shallow = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    if shallow == "true":
        sys.exit("whats_new.py needs the full history: check out with fetch-depth: 0")
    return subprocess.run(
        ["git", "log", "--reverse", "--no-color", "--no-ext-diff", "-p", "-U0",
         f"--format={RECORD}%H{FIELD}%cI{FIELD}%s", "--", "README.md"],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout


def parse_log(log: str) -> list[dict]:
    """Split `git log` output into commits with their added lines."""
    commits = []
    for record in log.split(RECORD)[1:]:
        header, _, diff = record.partition("\n")
        sha, date, subject = header.split(FIELD, 2)
        added = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
        commits.append({"sha": sha, "date": date, "subject": subject, "added": added})
    return commits


def first_seen(commits: list[dict]) -> dict[str, dict]:
    """Map each linked name and URL to the first commit that added it."""
    seen: dict[str, dict] = {}
    for commit in commits:
        for line in commit["added"]:
            text = line.strip()
            if not text.startswith(("-", "|")) and not text[:1].isdigit():
                continue
            match = LINK.search(text)
            if not match:
                continue
            for key in ("url:" + match.group(2), "name:" + unescape(match.group(1))):
                seen.setdefault(key, commit)
    return seen


def new_entries(entries: list[dict], commits: list[dict]) -> list[dict]:
    """Entries added after the first day, newest first and in README order within a commit."""
    if not commits:
        return []
    seen = first_seen(commits)
    order = {commit["sha"]: number for number, commit in enumerate(commits)}
    found = []
    for position, entry in enumerate(entries):
        candidates = [seen[key] for key in ("url:" + entry["url"], "name:" + entry["name"]) if key in seen]
        if not candidates:
            continue
        commit = min(candidates, key=lambda c: order[c["sha"]])
        if commit["date"][:10] == commits[0]["date"][:10]:
            continue
        found.append((-order[commit["sha"]], position, {**entry, "added": commit["date"], "commit": commit["sha"]}))
    return [entry for *_, entry in sorted(found, key=lambda item: item[:2])]


def where(entry: dict) -> str:
    return " › ".join(part for part in (entry["section"], entry.get("subsection"), entry.get("group")) if part)


def page(entries: list[dict], site: str = SITE) -> str:
    """The What's New page, newest first, one list per day."""
    out = [
        "---",
        "layout: default",
        "title: What's New",
        "description: Entries added to Awesome Vericoding, newest first.",
        "---",
        "{% raw %}",
        '<nav class="primer-back"><a href="./">← The list</a></nav>',
        "<h1>What's New</h1>",
        f'<p>Entries added since the list began, newest first. Follow along with the <a href="{site}feed.xml">Atom feed</a>.</p>',
    ]
    day = None
    for entry in entries:
        date = datetime.fromisoformat(entry["added"])
        if date.date() != day:
            if day is not None:
                out.append("</ul>")
            day = date.date()
            out.append(f'<h2 id="{day.isoformat()}">{date.day} {date:%B %Y}</h2>')
            out.append('<ul class="new-list">')
        description = f" - {html.escape(entry['description'])}" if entry.get("description") else ""
        out.append(
            f'<li><a href="{html.escape(entry["url"])}">{html.escape(entry["name"])}</a>{description}'
            f' <span class="new-where">{html.escape(where(entry))}</span></li>'
        )
    out.append("</ul>" if day is not None else "<p>Nothing yet.</p>")
    out.append("{% endraw %}")
    return "\n".join(out) + "\n"


def feed(entries: list[dict], site: str = SITE) -> str:
    """An Atom feed of the newest entries."""
    recent = entries[:FEED_SIZE]
    updated = max((entry["added"] for entry in recent), default="1970-01-01T00:00:00Z")
    out = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        "  <title>Awesome Vericoding: new entries</title>",
        f'  <link href="{site}new.html"/>',
        f'  <link rel="self" href="{site}feed.xml"/>',
        f"  <id>{site}feed.xml</id>",
        f"  <updated>{updated}</updated>",
        "  <author><name>Awesome Vericoding</name></author>",
    ]
    for entry in recent:
        out += [
            "  <entry>",
            f"    <title>{xml_escape(entry['name'])}</title>",
            f'    <link href="{xml_escape(entry["url"])}"/>',
            f"    <id>{xml_escape(entry['url'])}</id>",
            f"    <updated>{entry['added']}</updated>",
            f'    <category term="{xml_escape(where(entry), {chr(34): "&quot;"})}"/>',
            f"    <summary>{xml_escape(entry.get('description') or '')}</summary>",
            "  </entry>",
        ]
    out.append("</feed>")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--page", type=Path, default=ROOT / "new.html")
    parser.add_argument("--feed", type=Path, default=ROOT / "feed.xml")
    parser.add_argument("--site", default=SITE, help="the site's absolute URL, ending in /")
    args = parser.parse_args(argv)

    entries = build((ROOT / "README.md").read_text(encoding="utf-8"))["entries"]
    added = new_entries(entries, parse_log(git_log(ROOT)))
    args.page.write_text(page(added, args.site), encoding="utf-8")
    args.feed.write_text(feed(added, args.site), encoding="utf-8")
    print(f"{len(added)} new entries", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
