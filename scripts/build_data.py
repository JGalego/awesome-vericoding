#!/usr/bin/env python3
"""Turn the README into JSON for the website.

The README stays the only place where entries are written. This script reads it
and writes one JSON file with two parts:

- `entries`: every linked list item and benchmark row, with its section, group,
  markers, venue, year, extra links, and the verifiers it mentions. The site's
  search and filters read these, and anyone can fetch the file as an API.
  A primer's entry also has `primer`: its page on the site and, when it is
  written in a mainstream language, that language, from its `filename:`.
- `trust`: the Trust Checklist, with a regular expression for each escape
  hatch, used by scripts/hatches.mjs for the primer check and the `sorry` badge.

    python3 scripts/build_data.py --out data/list.json

The Pages workflow runs this before the Jekyll build. The output is not
committed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HEADING = re.compile(r"^(#{2,3})\s+(.*?)\s*$")
LIST_ITEM = re.compile(r"^(\s*)(?:[-*+]|\d+\.)\s+(.*)$")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
ENTRY = re.compile(
    r"^\[(?P<name>[^\]]+)\]\((?P<url>https?://[^)\s]+)\)"
    r"(?P<markers>(?:\s*(?:⭐|🏭|💰))*)"
    r"(?:\s+-\s+(?P<rest>.*))?$"
)
EXTRA_LINK = re.compile(r"\s+·\s+\[(?P<label>[^\]]+)\]\((?P<url>[^)\s]+)\)\s*$")
VENUE = re.compile(r"\s+\*(?P<venue>[^*]+)\*\s*$")
YEAR = re.compile(r"\b(19[5-9]\d|20\d\d)\b")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
PRIMER_URL = re.compile(r"^https://github\.com/JGalego/awesome-vericoding/blob/main/primers/(?P<name>[a-z0-9-]+)\.md$")
FILENAME = re.compile(r"^filename:\s*(\S+)\s*$", re.MULTILINE)
# Primers written in a language people already ship. The others are written
# in the verifier's own language, such as Dafny or Lean.
PRIMER_LANGUAGES = {
    "ada": "Ada", "c": "C", "go": "Go", "hs": "Haskell", "java": "Java",
    "ml": "OCaml", "py": "Python", "rs": "Rust", "scala": "Scala",
}
CODE_SPAN = re.compile(r"`([^`]+)`")

MARKERS = {"⭐": "start", "🏭": "production", "💰": "paid"}

# Sections that hold navigation or prose rather than entries.
SKIP_SECTIONS = {"Contents", "Contributing"}
TRUST_SECTION = "Trust Checklist"

# Verifiers worth filtering by. A pattern is matched against an entry's name,
# description, group, and the Verifiers column of a table.
VERIFIERS = {
    "Dafny": r"\bDafny\b",
    "Lean": r"\bLean\b",
    "Verus": r"\bVerus\b",
    "Rocq": r"\b(?:Rocq|Coq)\b",
    "Isabelle": r"\bIsabelle\b",
    "F*": r"(?<![\w*])F\*",
    "SPARK": r"\bSPARK\b",
    "Kani": r"\bKani\b",
    "Why3": r"\bWhy(?:3|ML)\b",
    "Frama-C": r"\b(?:Frama-C|ACSL)\b",
    "Viper": r"\bViper\b",
    "Agda": r"\bAgda\b",
    "Idris": r"\bIdris\b",
    "HOL4": r"\bHOL4\b",
    "ACL2": r"\bACL2\b",
    "Boogie": r"\bBoogie\b",
}
VERIFIER_PATTERNS = {name: re.compile(pattern) for name, pattern in VERIFIERS.items()}

# Ada is case-insensitive, so SPARK's escape hatches are too.
CASE_INSENSITIVE = {"SPARK"}


def heading_text(raw: str) -> str:
    """Drop the leading emoji from a heading such as '🚀 Start Here'."""
    return re.sub(r"^[^\w(]+", "", raw).strip()


ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|])")


def unescape(markdown: str) -> str:
    """Drop Markdown backslash escapes, such as the one in `F\\*`."""
    return ESCAPE.sub(r"\1", markdown)


def plain(markdown: str) -> str:
    """Markdown inline text to plain text."""
    text = LINK.sub(r"\1", markdown)
    text = CODE_SPAN.sub(r"\1", text)
    text = re.sub(r"(?<![\w\\])\*([^*]+)(?<!\\)\*(?!\w)", r"\1", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def verifiers_in(*texts: str) -> list[str]:
    joined = " ".join(texts)
    return [name for name, pattern in VERIFIER_PATTERNS.items() if pattern.search(joined)]


def parse_entry(text: str) -> dict | None:
    match = ENTRY.match(text.strip())
    if not match:
        return None
    rest = match.group("rest") or ""
    links = []
    while True:
        extra = EXTRA_LINK.search(rest)
        if not extra:
            break
        links.insert(0, {"label": extra.group("label"), "url": extra.group("url")})
        rest = rest[: extra.start()]
    venue = year = None
    tag = VENUE.search(rest)
    if tag:
        venue = tag.group("venue").strip()
        rest = rest[: tag.start()]
        years = YEAR.findall(venue)
        year = int(years[-1]) if years else None
    links = [{"label": label, "url": url} for label, url in LINK.findall(rest)] + links
    return {
        "name": unescape(match.group("name")),
        "url": match.group("url"),
        "markers": [MARKERS[m] for m in re.findall("⭐|🏭|💰", match.group("markers"))],
        "description": plain(rest),
        "description_md": rest.strip(),
        "venue": venue,
        "year": year,
        "links": links,
        "code": next((link["url"] for link in links if link["label"] == "Code"), None),
    }


def split_row(line: str) -> list[str]:
    cells = CELL_SPLIT.split(line.strip())
    return [cell.strip().replace("\\|", "|") for cell in cells[1:-1]]


def js_escape(text: str) -> str:
    """Escape for a regular expression that both Python and JavaScript accept."""
    return re.sub(r"([\\^$.*+?()\[\]{}|/])", r"\\\1", text)


def _join(token: str) -> str:
    """A pattern for one token, flexible about whitespace around brackets."""
    pieces = re.findall(r"\w+|\s+|[()\[\]{}]|[^\w\s()\[\]{}]+", token)
    out: list[str] = []
    for i, piece in enumerate(pieces):
        if piece.isspace():
            before, after = pieces[i - 1], pieces[i + 1]
            words = re.match(r"\w", before[-1]) and re.match(r"\w", after[0])
            out.append(r"\s+" if words else r"\s*")
            continue
        if i and not pieces[i - 1].isspace() and (piece in "()[]{}" or pieces[i - 1] in "()[]{}"):
            out.append(r"\s*")
        out.append(js_escape(piece))
    return "".join(out)


ATTRIBUTE = re.compile(r"^(@\[|#\[|\{:)(.+)(\]|\})$")


def hatch_pattern(token: str) -> str:
    """A regular expression for one escape hatch written in the Trust Checklist.

    `assume(...)` matches any call, an attribute such as `{:extern}` or
    `@[implemented_by]` also matches when it carries arguments or sits in a list
    with other attributes, and words get word boundaries so that `assume` does
    not match `assumes`.
    """
    token = token.strip()
    attribute = ATTRIBUTE.match(token)
    if attribute:
        opener, inner, closer = attribute.groups()
        body = _join(inner) + (r"\b" if re.match(r"\w", inner[-1]) else "")
        if opener == "{:":
            return r"\{\s*:\s*" + body + r"[^}]*\}"
        if opener == "#[":
            return r"#!?\[[^\]]*?\b" + body + r"[^\]]*\]"
        return r"@\[[^\]]*?\b" + body + r"[^\]]*\]"
    call = token.endswith("(...)")
    if call:
        token = token[: -len("(...)")]
    pattern = _join(token)
    if re.match(r"\w", token[0]):
        pattern = r"\b" + pattern
    if call:
        return pattern + r"\s*\("
    if re.match(r"\w", token[-1]):
        pattern += r"\b"
    return pattern


def parse_trust_row(cells: list[str]) -> dict:
    verifier, hatches, audit = cells[0], cells[1], cells[2]
    tokens = CODE_SPAN.findall(hatches)
    return {
        "verifier": plain(verifier),
        "hatches": [{"text": token, "pattern": hatch_pattern(token)} for token in tokens],
        "flags": "i" if plain(verifier) in CASE_INSENSITIVE else "",
        "hatches_md": hatches,
        "audit_md": audit,
        "audit": plain(audit),
    }


def primer_info(url: str, primers: Path) -> dict | None:
    match = PRIMER_URL.match(url)
    if not match:
        return None
    name = match.group("name")
    path = primers / f"{name}.md"
    filename = FILENAME.search(path.read_text(encoding="utf-8")) if path.exists() else None
    extension = filename.group(1).rsplit(".", 1)[-1] if filename else ""
    return {"page": f"primers/{name}.html", "language": PRIMER_LANGUAGES.get(extension)}


def build(readme: str, primers: Path = ROOT / "primers") -> dict:
    entries: list[dict] = []
    trust: list[dict] = []
    section = subsection = group = None
    in_fence = False
    table_header: list[str] | None = None

    for line in readme.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        heading = HEADING.match(line)
        if heading:
            title = heading_text(heading.group(2))
            if len(heading.group(1)) == 2:
                section, subsection = title, None
            else:
                subsection = title
            group = None
            table_header = None
            continue
        if section is None or section in SKIP_SECTIONS:
            continue

        if line.startswith("|"):
            cells = split_row(line)
            if table_header is None:
                table_header = [plain(cell) for cell in cells]
                continue
            if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
                continue
            if section == TRUST_SECTION:
                trust.append(parse_trust_row(cells))
                continue
            entry = parse_entry(cells[0])
            if entry is None:
                continue
            fields = dict(zip(table_header[1:], (plain(cell) for cell in cells[1:])))
            year = fields.get("Year", "")
            entry.update(
                year=int(year) if year.isdigit() else entry["year"],
                description=" · ".join(v for k, v in fields.items() if k in ("Task", "Size") and v),
                fields=fields,
            )
            entries.append(dict(section=section, subsection=subsection, group=None, kind="table", **entry))
            continue
        table_header = None

        item = LIST_ITEM.match(line)
        if not item:
            continue
        indent, text = len(item.group(1)), item.group(2)
        entry = parse_entry(text)
        if entry is None:
            if indent == 0 and not text.startswith("["):
                group = plain(text)
            continue
        if indent == 0:
            group = None
        entries.append(dict(section=section, subsection=subsection, group=group, kind="list", **entry))

    for entry in entries:
        entry["verifiers"] = verifiers_in(
            entry["name"],
            entry["description"],
            entry["group"] or "",
            entry.get("fields", {}).get("Verifiers", ""),
        )
        primer = primer_info(entry["url"], primers)
        if primer:
            entry["primer"] = primer
    return {"entries": entries, "trust": trust}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--readme", default=str(ROOT / "README.md"))
    parser.add_argument("--out", default="-", help="output path, or - for stdout")
    args = parser.parse_args(argv)

    data = build(Path(args.readme).read_text(encoding="utf-8"))
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    if args.out == "-":
        sys.stdout.write(text)
    else:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"{out}: {len(data['entries'])} entries, {len(data['trust'])} Trust Checklist rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
