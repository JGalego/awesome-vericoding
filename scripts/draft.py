#!/usr/bin/env python3
"""Draft one README entry for a candidate from a scout issue.

A maintainer comments `/draft <url>` on a scout issue. This script fetches the
page itself, asks a model (Gemini by default) to pick a subsection and write a
one-sentence description, then checks the result mechanically against the rules
in contributing.md before touching the README. The model never chooses where
the line goes, never writes the title of a paper, and never sees any file other
than the page it was handed. If a check fails the README is left alone and the
report says why.

    GITHUB_TOKEN=... SCOUT_API_KEY=... GITHUB_REPOSITORY=owner/repo COMMENT_BODY='/draft https://...' \\
        ISSUE_BODY='...' python3 scripts/draft.py --report draft-report.md

When $GITHUB_OUTPUT is set it writes `status` (ok or rejected), `branch`, and
`title` there for the workflow.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from scout import (
    ARXIV_ID,
    DEFAULT_MODEL,
    chat,
    fetch,
    github_get,
    known_keys,
    normalize,
    parse_arxiv,
)

CAP = 15  # flat subsections
GROUP_CAP = 10  # each language group in a nested subsection
MAX_WORDS = 30
BANNED = (
    "blazing", "best", "revolutionary", "game-changing", "groundbreaking", "cutting-edge",
    "seamless", "powerful", "world-class", "unlock", "leverage", "next-generation", "state-of-the-art",
)
# Subsections whose entries are not plain list items.
UNSUPPORTED = ("benchmarks", "cheat sheets", "start here", "trust checklist", "milestones")
# Subsections ordered by year of first release; the rest are alphabetical.
CHRONOLOGICAL = (
    "foundations", "essays", "verified systems", "industry reports", "position papers", "surveys",
    "verified code generation", "proof and annotation synthesis", "specification generation",
    "verified translation", "field reports", "theorem-proving models",
)
TAG = re.compile(r"^(?:arXiv|Blog|[A-Z][A-Za-z+ ]{1,30}) 20\d\d$")
COMMENT_URL = re.compile(r"/draft\s+<?(https?://[^\s>]+)")


# --------------------------------------------------------------------------
# README structure


@dataclass
class Section:
    heading: str
    start: int  # index of the heading line
    end: int  # index after the last line before the next heading

    @property
    def key(self) -> str:
        return re.sub(r"^[^\w]+", "", self.heading).strip().lower()

    @property
    def supported(self) -> bool:
        return not any(word in self.key for word in UNSUPPORTED)

    @property
    def chronological(self) -> bool:
        return self.key in CHRONOLOGICAL


def sections(lines: list[str]) -> list[Section]:
    heads = [i for i, line in enumerate(lines) if line.startswith("### ")]
    out = []
    for n, i in enumerate(heads):
        stop = len(lines)
        for j in range(i + 1, len(lines)):
            if lines[j].startswith("#"):
                stop = j
                break
        out.append(Section(lines[i][4:].strip(), i, stop))
    return out


def groups(lines: list[str], sec: Section) -> list[str]:
    """Names of language groups such as `- Rust`, for subsections that nest entries."""
    return [ln[2:].strip() for ln in lines[sec.start:sec.end] if ln.startswith("- ") and not ln.startswith("- [")]


def entry_lines(lines: list[str], sec: Section, group: Optional[str]) -> list[int]:
    """Indices of the entry lines in a subsection, or in one group of it."""
    idxs = list(range(sec.start + 1, sec.end))
    if group:
        top = next((i for i in idxs if lines[i].strip() == f"- {group}" and not lines[i].startswith(" ")), None)
        if top is None:
            return []
        out = []
        for i in range(top + 1, sec.end):
            if lines[i].startswith("- "):
                break
            if lines[i].startswith("  - ["):
                out.append(i)
        return out
    return [i for i in idxs if lines[i].startswith("- [")]


def sort_key(line: str) -> str:
    match = re.match(r"\s*- \[([^\]]*)\]", line)
    return (match.group(1) if match else line).casefold()


def insert_position(lines: list[str], sec: Section, group: Optional[str], name: str) -> Optional[int]:
    """Line index at which to insert, honoring the ordering rules."""
    existing = entry_lines(lines, sec, group)
    if group and not existing:
        top = next((i for i, ln in enumerate(lines[sec.start:sec.end], sec.start) if ln == f"- {group}"), None)
        return None if top is None else top + 1
    if not existing:
        return None  # an empty subsection needs its first entry by hand
    if sec.chronological:
        return existing[-1] + 1
    for i in existing:
        if sort_key(lines[i]) > name.casefold():
            return i
    return existing[-1] + 1


# --------------------------------------------------------------------------
# The mechanical checks


def count_numbers(text: str) -> list[str]:
    return re.findall(r"\d[\d,.]*\d|\d", text)


def check_entry(name: str, description: str, source_text: str, kind_is_paper: bool) -> list[str]:
    problems = []
    words = description.split()
    if not description or not description[0].isupper():
        problems.append("The description must start with a capital letter.")
    if not description.endswith("."):
        problems.append("The description must end with a period.")
    if len(words) >= MAX_WORDS:
        problems.append(f"The description has {len(words)} words; keep it under {MAX_WORDS}.")
    if not kind_is_paper and len(name) >= 4 and name.casefold() in description.casefold():
        problems.append("The description repeats the entry's name.")
    lowered = description.casefold()
    for word in BANNED:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            problems.append(f"The description uses the marketing word '{word}'.")
    haystack = source_text.replace(",", "")
    for number in count_numbers(description):
        if number.replace(",", "") not in haystack:
            problems.append(f"The number '{number}' does not appear in the fetched source.")
    return problems


def compose(name: str, url: str, description: str, tag: Optional[str], code: Optional[str], nested: bool) -> str:
    line = f"- [{name}]({url}) - {description}"
    if tag:
        line += f" *{tag}*"
        if code:
            line += f" · [Code]({code})"
    return ("  " if nested else "") + line


# --------------------------------------------------------------------------
# Fetching the candidate


@dataclass
class Page:
    url: str
    title: str
    text: str
    year: str
    is_paper: bool = False
    problems: list[str] = field(default_factory=list)


def strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def clean_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parsed.query) if not k.lower().startswith("utm_")]
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query), fragment=""))


def load_page(url: str, token: str) -> Page:
    match = ARXIV_ID.search(url)
    if match:
        body = fetch(f"https://export.arxiv.org/api/query?id_list={match.group(1)}", timeout=60, retry_on=(429, 503), pauses=(10, 30, 60))
        cands = parse_arxiv(body.decode("utf-8", "replace")) if body else []
        if not cands:
            return Page(url, "", "", "", problems=["Could not read the paper from the arXiv API."])
        c = cands[0]
        return Page(c.url, c.title, f"{c.title}. {c.summary}", c.date[:4], is_paper=True)

    gh = re.match(r"^https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?$", url)
    if gh:
        slug = f"{gh.group(1)}/{gh.group(2).removesuffix('.git')}"
        repo = github_get(f"/repos/{slug}", token)
        if not isinstance(repo, dict) or "full_name" not in repo:
            return Page(url, "", "", "", problems=["Could not read the repository from the GitHub API."])
        problems = []
        if repo.get("archived"):
            problems.append("The repository is archived.")
        pushed = repo.get("pushed_at", "")
        if pushed and datetime.fromisoformat(pushed.replace("Z", "+00:00")) < datetime.now(timezone.utc) - timedelta(days=365):
            problems.append("The repository has had no pushes in the last 12 months.")
        readme = github_get(f"/repos/{slug}/readme", token)
        text = ""
        if isinstance(readme, dict) and readme.get("content"):
            import base64

            text = base64.b64decode(readme["content"]).decode("utf-8", "replace")[:6000]
        return Page(
            repo["html_url"], repo["name"], f"{repo['name']}. {repo.get('description') or ''}\n{text}",
            str(datetime.now(timezone.utc).year), problems=problems,
        )

    body = fetch(url)
    if not body:
        return Page(url, "", "", "", problems=["The URL did not resolve."])
    html = body.decode("utf-8", "replace")
    title = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    meta = re.search(r'(?is)<meta[^>]+name="description"[^>]+content="([^"]*)"', html)
    text = " ".join(filter(None, [title.group(1) if title else "", meta.group(1) if meta else "", strip_html(html)[:6000]]))
    return Page(clean_url(url), " ".join((title.group(1) if title else "").split()), text, str(datetime.now(timezone.utc).year))


# --------------------------------------------------------------------------
# The model


def build_messages(page: Page, subsections: list[tuple[str, list[str]]]) -> list[dict]:
    menu = []
    for heading, grp in subsections:
        menu.append(f"- {heading}" + (f" (groups: {', '.join(grp)})" if grp else ""))
    system = (
        "You help maintain an awesome list about vericoding: code that comes with a machine-checked proof "
        "against a formal specification, written by people or by AI. You will be given the text of one web page. "
        "Decide whether it belongs and, if so, write its list entry.\n\n"
        "The page must be about at least one of: verification-aware languages, verifiers or proof assistants applied "
        "to programs; verified software systems; benchmarks or datasets of verified code, specifications, or proofs; "
        "or AI that writes verified code, specifications, or proofs. Set fits=false, with a one-sentence reason, if "
        "the page is marketing, a product announcement, filler, or padded writing; has no checkable artifact such as "
        "code, proofs, data, or a method; only mentions formal verification in passing or uses it as a label; is "
        "testing, fuzzing, or static analysis that produces no proofs; is design-level model checking with no link to "
        "code; or is formalized mathematics, physics, statistics, security, or another domain that merely uses a "
        "proof assistant or formal methods, with no carry-over to program proofs. When in doubt set fits=false.\n\n"
        "If it fits, pick exactly one subsection from this list, copied exactly, and a group if the subsection "
        "lists groups:\n" + "\n".join(menu) + "\n\n"
        "Write one factual sentence of at most 25 words. Start with a capital letter and end with a period. "
        "No marketing words. Do not repeat the name. Use only numbers that appear in the page text. "
        "For papers and posts also give venue_tag as 'arXiv YYYY' for preprints or 'Blog YYYY' for posts, "
        "or the published venue and year. Use null for fields that do not apply. When fits is true, evidence must be an "
        "exact quote of 20 to 200 characters copied from the page text that shows it is about verified code, "
        "specifications, or proofs; when fits is false, use null.\n\n"
        'Reply with JSON only: {"fits": bool, "reason": str, "subsection": str, "group": str|null, '
        '"name": str, "description": str, "venue_tag": str|null, "code_url": str|null}. '
        "code_url must be a URL that appears in the page text."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"URL: {page.url}\nTitle: {page.title}\n\nPage text:\n{page.text[:6000]}"},
    ]


def ask_model(messages: list[dict], token: str, model: str) -> Optional[dict]:
    content = chat(messages, token, model)
    if content is None:
        return None
    answer = parse_answer(content)
    if answer is None:
        print(f"warning: no usable JSON in the model's answer: {content[:300]!r}", file=sys.stderr)
    return answer


def parse_answer(text: str) -> Optional[dict]:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) and isinstance(data.get("fits"), bool) else None


# --------------------------------------------------------------------------
# Putting it together


@dataclass
class Result:
    ok: bool
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    lines: Optional[list[str]] = None
    entry: str = ""
    title: str = ""
    slug: str = ""
    section: str = ""


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "entry"


def draft(readme: str, page: Page, answer: dict, known: set[str]) -> Result:
    lines = readme.split("\n")
    secs = {s.heading: s for s in sections(lines)}
    result = Result(False)

    if page.problems:
        result.problems += page.problems
        return result
    if not answer.get("fits"):
        result.problems.append(f"The model declined: {answer.get('reason') or 'no reason given'}")
        return result
    if normalize(page.url) in known:
        result.problems.append("This URL is already in the README, an open PR, or an earlier scout issue.")
        return result

    evidence = " ".join(str(answer.get("evidence") or "").split())
    if len(evidence) < 20 or " ".join(evidence.casefold().split()) not in " ".join(page.text.casefold().split()):
        result.problems.append(
            "The model gave no quote from the page showing it is about code with machine-checked proofs, "
            "or the quote is not on the page."
        )
        return result

    sec = secs.get(str(answer.get("subsection")))
    if sec is None or not sec.supported:
        result.problems.append(f"'{answer.get('subsection')}' is not a subsection this script can add to. Add it by hand.")
        return result
    grp = answer.get("group") or None
    available = groups(lines, sec)
    if available and grp not in available:
        result.problems.append(f"'{sec.heading}' needs one of these groups: {', '.join(available)}.")
        return result
    if not available and grp:
        grp = None

    name = page.title if page.is_paper else str(answer.get("name") or "").strip()
    if not name:
        result.problems.append("No name for the entry.")
        return result
    if not page.is_paper and name.casefold() not in page.text.casefold():
        result.problems.append(f"The name '{name}' does not appear in the fetched page.")

    tag = answer.get("venue_tag") or None
    if page.is_paper and (not tag or tag.startswith("arXiv")):
        tag = f"arXiv {page.year}"
    chronological = sec.chronological
    if chronological and not tag:
        result.problems.append("Entries in this subsection need a venue tag.")
    if tag and not TAG.match(tag):
        result.problems.append(f"The venue tag '{tag}' is not in the form 'Venue 2026'.")
    if not chronological:
        tag = None

    code = answer.get("code_url") or None
    if not page.is_paper:
        code = None  # a repository or post is its own link
    if code and code not in page.text:
        result.problems.append("The code URL does not appear in the fetched page.")
        code = None
    if code and normalize(code) in known:
        code = None

    description = str(answer.get("description") or "").strip()
    result.problems += check_entry(name, description, page.text, page.is_paper)
    if result.problems:
        return result

    pos = insert_position(lines, sec, grp, name)
    if pos is None:
        result.problems.append("Could not find where to insert the entry.")
        return result
    entry = compose(name, page.url, description, tag, code, nested=bool(grp))
    if grp:
        count, cap, where = len(entry_lines(lines, sec, grp)), GROUP_CAP, f"The '{grp}' group in '{sec.heading}'"
    else:
        count = sum(1 for i in range(sec.start, sec.end) if re.match(r"\s*- \[", lines[i]))
        cap, where = CAP, f"'{sec.heading}'"
    if count >= cap:
        result.warnings.append(
            f"{where} already has {count} entries (the guideline is at most {cap}). "
            "Say which entry this one should replace and why, or why it is worth the extra place."
        )
    new = lines[:pos] + [entry] + lines[pos:]
    return Result(True, [], result.warnings, new, entry, f"Add {name}", slugify(name), sec.heading)


def pr_body(result: Result, page: Page, issue: str, answer: dict) -> str:
    out = [
        f"Drafted by `scripts/draft.py` from [{issue}] and **not yet checked by a person**. "
        "Open the source, read the entry against it, and check every claim before merging.",
        "",
        f"- Source: {page.url}",
        f"- Subsection: {result.section}",
        f"- Model's reason: {answer.get('reason') or 'none given'}",
        "- Mechanical checks passed: the URL resolves and is not already listed, the description is a capitalized "
        f"sentence under {MAX_WORDS} words with no marketing words, every number appears in the fetched source, "
        "and the entry sits in the position the ordering rules give.",
        "",
        "```md",
        result.entry,
        "```",
    ]
    if result.warnings:
        out += [""] + [f"> {w}" for w in result.warnings]
    return "\n".join(out) + "\n"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--readme", default="README.md")
    parser.add_argument("--report", default="draft-report.md")
    parser.add_argument("--issue", default="a scout issue", help="how to refer to the source issue")
    parser.add_argument("--model", default=os.environ.get("SCOUT_MODEL") or DEFAULT_MODEL)
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN", "")
    comment = os.environ.get("COMMENT_BODY", "")
    issue_body = os.environ.get("ISSUE_BODY", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")

    def finish(status: str, report: str, result: Optional[Result] = None) -> int:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report)
        out = os.environ.get("GITHUB_OUTPUT")
        if out:
            with open(out, "a", encoding="utf-8") as f:
                f.write(f"status={status}\n")
                if result and result.ok:
                    f.write(f"branch=draft/{result.slug}\ntitle={result.title}\n")
        print(f"{status}: {report.splitlines()[0] if report else ''}")
        return 0

    match = COMMENT_URL.search(comment)
    if not match or not token:
        return finish("rejected", "Usage: comment `/draft <url>` where the URL is one of the links in this issue.\n")
    url = match.group(1).rstrip(".,;)")
    if normalize(url) not in known_keys(issue_body):
        return finish("rejected", f"{url} is not linked from this issue, so I will not draft it.\n")

    with open(args.readme, encoding="utf-8") as f:
        readme = f.read()
    known = known_keys(readme)
    if repo:
        pulls = github_get(f"/repos/{repo}/pulls?state=open&per_page=100", token)
        for pr in pulls if isinstance(pulls, list) else []:
            known |= known_keys(pr.get("body") or "")

    page = load_page(url, token)
    secs = sections(readme.split("\n"))
    lines = readme.split("\n")
    menu = [(s.heading, groups(lines, s)) for s in secs if s.supported and (page.is_paper or not s.chronological)]
    api_key = os.environ.get("SCOUT_API_KEY", "")
    if not api_key and not page.problems:
        return finish("rejected", "The SCOUT_API_KEY secret is not set, so there is no model to draft with.\n")
    answer = None if page.problems else ask_model(build_messages(page, menu), api_key, args.model)
    if answer is None and not page.problems:
        return finish("rejected", "The model did not give a usable answer, so nothing was drafted. Try again later.\n")

    result = draft(readme, page, answer or {}, known)
    if not result.ok:
        return finish("rejected", "Nothing was drafted:\n\n" + "\n".join(f"- {p}" for p in result.problems) + "\n")

    with open(args.readme, "w", encoding="utf-8") as f:
        f.write("\n".join(result.lines or []))
    return finish("ok", pr_body(result, page, args.issue, answer or {}), result)


if __name__ == "__main__":
    sys.exit(main())
