"""Offline tests for build_data.py. Run with: python3 -m unittest discover scripts"""

import re
import unittest
from pathlib import Path

from build_data import ENTRY, build, hatch_pattern, parse_entry

README = """\
# Awesome Example

Intro with a [link](https://example.com) that is not an entry.

## Contents

- [🚀 Start Here](#-start-here)

## 🚀 Start Here

> *Tagline*

1. [First Read](https://first.example) - Read this first.
2. Ask a model for something, which is not an entry.

```mermaid
flowchart LR
    a --> b
```

## 📐 Classic Vericoding

### 🧩 Languages

- [Dafny](https://dafny.org) ⭐ 🏭 - Language with contracts ([LPAR 2010 paper](https://doi.org/10.1007/x)).
- Rust
  - [Verus](https://github.com/verus-lang/verus) ⭐ - SMT-based verifier for Rust.
- [Book](https://book.example) 💰 - A paid book about Rocq.

### 📊 Benchmarks

| Benchmark                         | Year | Verifiers    | Size         | Task            |
| --------------------------------- | ---- | ------------ | ------------ | --------------- |
| [Bench](https://arxiv.org/abs/1)  | 2025 | Dafny, Lean  | 1,000 tasks  | Proof synthesis |

## 🤖 AI Vericoding

### ✨ Generation

- [A Paper: With a Colon](https://arxiv.org/abs/2) - Generates *verified* F* code. *FSE Industry 2024* · [Code](https://github.com/a/b)

## 🔍 Trust Checklist

| Verifier | Escape hatches to search for          | How to audit           |
| -------- | ------------------------------------- | ---------------------- |
| Dafny    | `assume`, bodiless `{:extern}` things | `dafny verify --warn`  |
| SPARK    | `pragma Assume`, `SPARK_Mode (Off)`   | Review the summary     |

## Contributing

- [Guidelines](https://example.com/contributing) - Not an entry.
"""


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.data = build(README)
        self.by_name = {e["name"]: e for e in self.data["entries"]}

    def test_finds_entries_and_skips_navigation(self):
        self.assertEqual(
            list(self.by_name),
            ["First Read", "Dafny", "Verus", "Book", "Bench", "A Paper: With a Colon"],
        )

    def test_sections_groups_and_markers(self):
        verus = self.by_name["Verus"]
        self.assertEqual((verus["section"], verus["subsection"], verus["group"]), ("Classic Vericoding", "Languages", "Rust"))
        self.assertIsNone(self.by_name["Book"]["group"], "an unindented entry ends the group")
        self.assertEqual(self.by_name["Dafny"]["markers"], ["start", "production"])
        self.assertEqual(self.by_name["Book"]["markers"], ["paid"])
        self.assertIsNone(self.by_name["First Read"]["subsection"])

    def test_paper_venue_year_and_links(self):
        paper = self.by_name["A Paper: With a Colon"]
        self.assertEqual(paper["venue"], "FSE Industry 2024")
        self.assertEqual(paper["year"], 2024)
        self.assertEqual(paper["code"], "https://github.com/a/b")
        self.assertEqual(paper["description"], "Generates verified F* code.")
        self.assertEqual(paper["verifiers"], ["F*"])

    def test_tool_paper_link_is_not_a_venue(self):
        dafny = self.by_name["Dafny"]
        self.assertIsNone(dafny["year"])
        self.assertEqual(dafny["links"], [{"label": "LPAR 2010 paper", "url": "https://doi.org/10.1007/x"}])
        self.assertEqual(dafny["description"], "Language with contracts (LPAR 2010 paper).")

    def test_verifiers_from_group_and_table(self):
        self.assertEqual(self.by_name["Verus"]["verifiers"], ["Verus"])
        self.assertEqual(self.by_name["Book"]["verifiers"], ["Rocq"])
        bench = self.by_name["Bench"]
        self.assertEqual((bench["year"], bench["kind"]), (2025, "table"))
        self.assertEqual(bench["verifiers"], ["Dafny", "Lean"])
        self.assertEqual(bench["description"], "1,000 tasks · Proof synthesis")

    def test_trust_checklist(self):
        dafny, spark = self.data["trust"]
        self.assertEqual(dafny["verifier"], "Dafny")
        self.assertEqual([h["text"] for h in dafny["hatches"]], ["assume", "{:extern}"])
        self.assertEqual(dafny["audit"], "dafny verify --warn")
        self.assertEqual((dafny["flags"], spark["flags"]), ("", "i"))


def matches(token, text):
    return re.search(hatch_pattern(token), text) is not None


class HatchPatternTests(unittest.TestCase):
    def test_words_have_boundaries(self):
        self.assertTrue(matches("assume", "assume x > 0;"))
        self.assertFalse(matches("assume", "Kani assumes requires"))
        self.assertFalse(matches("admit", "Admitted."))
        self.assertTrue(matches("sorry", "theorem t : p := by sorry"))

    def test_calls_and_spacing(self):
        self.assertTrue(matches("assume(...)", "assume (x > 0);"))
        self.assertFalse(matches("assume(...)", "assume_x"))
        self.assertTrue(matches("admit ()", "admit()"))
        self.assertTrue(matches("SPARK_Mode (Off)", "pragma SPARK_Mode( Off );"))
        self.assertFalse(matches("SPARK_Mode (Off)", "package Learn with SPARK_Mode is"))
        self.assertTrue(matches("--admit_smt_queries true", '#set-options "--admit_smt_queries  true"'))
        self.assertTrue(matches("--lax", "fstar.exe --lax Learn.fst"))
        self.assertTrue(matches("kani::assume", "kani::assume(x < 10);"))

    def test_attributes_with_arguments(self):
        self.assertTrue(matches("{:extern}", 'method {:extern "Foo"} Bar()'))
        self.assertTrue(matches("{:axiom}", "lemma {:axiom} L()"))
        self.assertTrue(matches("{:verify false}", "method {:verify  false} M()"))
        self.assertFalse(matches("{:verify false}", "method {:verify true} M()"))
        self.assertTrue(matches("@[implemented_by]", "@[simp, implemented_by fastImpl] def f"))
        self.assertTrue(matches("@[extern]", '@[extern "lean_add"] def add'))
        self.assertTrue(matches("#[verifier::external_body]", "#[verifier::external_body]\nfn f()"))
        self.assertFalse(matches("#[verifier::external_body]", "#[verifier::external]\nfn f()"))

    def test_every_real_checklist_pattern_matches_its_own_text(self):
        readme = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
        trust = build(readme)["trust"]
        self.assertGreater(len(trust), 0)
        for row in trust:
            self.assertTrue(row["hatches"], row["verifier"])
            for hatch in row["hatches"]:
                sample = hatch["text"].replace("(...)", "(x)")
                flags = re.I if row["flags"] == "i" else 0
                self.assertRegex(sample, re.compile(hatch["pattern"], flags), (row["verifier"], hatch["text"]))


class RealReadmeTests(unittest.TestCase):
    def test_every_linked_item_becomes_an_entry(self):
        readme = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
        body = readme.split("\n## 🚀", 1)[1].split("\n## Contributing", 1)[0]
        expected = [
            line for line in body.splitlines()
            if re.match(r"^\s*(?:-|\d+\.) \[[^\]]+\]\(https?://", line) or re.match(r"^\| \[", line)
        ]
        entries = build(readme)["entries"]
        self.assertEqual(len(entries), len(expected))
        for entry in entries:
            self.assertTrue(entry["url"].startswith("http"), entry)
            self.assertTrue(entry["section"], entry)

    def test_entry_regex_requires_a_web_link(self):
        self.assertIsNone(ENTRY.match("[🚀 Start Here](#-start-here)"))
        self.assertIsNone(parse_entry("Rust"))


if __name__ == "__main__":
    unittest.main()
