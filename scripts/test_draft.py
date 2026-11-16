"""Offline tests for draft.py. Run with: python3 -m unittest discover scripts"""

import unittest

from draft import (
    Page, check_entry, compose, draft, groups, insert_position, parse_answer, sections, slugify,
)

README = """\
# Awesome Example

## Tools

### 💼 Companies

> *Businesses*

- [Alpha](https://alpha.example) - Does alpha.
- [Gamma](https://gamma.example) - Does gamma.

### 🧪 Field Reports

> *Reports*

- [Old](https://example.com/old) - Older report. *Blog 2025*
- [Newer](https://example.com/newer) - Newer report. *Blog 2026*

### 🔧 Verifiers

> *Keep the language*

- C
  - [CBMC](https://github.com/diffblat/cbmc) - Checks C.
- Rust
  - [Aeneas](https://aeneas.example) - Translates Rust.
  - [Verus](https://github.com/verus-lang/verus) - Verifies Rust.

### 📊 Benchmarks

> *Numbers*

| A | B |

### 🌱 Empty

> *Nothing yet*

## Next
"""

LINES = README.split("\n")
SECS = {s.heading: s for s in sections(LINES)}


def answer(**kw):
    base = {"fits": True, "reason": "Has proofs.", "subsection": "💼 Companies", "group": None,
            "name": "Beta", "description": "Builds provers for Lean.", "venue_tag": None, "code_url": None,
            "evidence": "Beta builds provers for Lean."}
    base.update(kw)
    return base


def page(title="Beta", text="Beta builds provers for Lean.", paper=False, url="https://beta.example"):
    return Page(url, title, text, "2026", is_paper=paper)


class StructureTests(unittest.TestCase):
    def test_sections_and_groups(self):
        self.assertIn("💼 Companies", SECS)
        self.assertEqual(groups(LINES, SECS["🔧 Verifiers"]), ["C", "Rust"])
        self.assertTrue(SECS["💼 Companies"].supported)
        self.assertFalse(SECS["📊 Benchmarks"].supported)
        self.assertTrue(SECS["🧪 Field Reports"].chronological)
        self.assertFalse(SECS["💼 Companies"].chronological)

    def test_alphabetical_insert(self):
        sec = SECS["💼 Companies"]
        self.assertEqual(LINES[insert_position(LINES, sec, None, "Beta")], "- [Gamma](https://gamma.example) - Does gamma.")
        self.assertEqual(insert_position(LINES, sec, None, "Zeta"), LINES.index("- [Gamma](https://gamma.example) - Does gamma.") + 1)
        self.assertEqual(LINES[insert_position(LINES, sec, None, "aardvark")], "- [Alpha](https://alpha.example) - Does alpha.")

    def test_chronological_appends(self):
        sec = SECS["🧪 Field Reports"]
        pos = insert_position(LINES, sec, None, "Anything")
        self.assertEqual(LINES[pos - 1], "- [Newer](https://example.com/newer) - Newer report. *Blog 2026*")

    def test_group_insert(self):
        sec = SECS["🔧 Verifiers"]
        pos = insert_position(LINES, sec, "Rust", "Creusot")
        self.assertEqual(LINES[pos], "  - [Verus](https://github.com/verus-lang/verus) - Verifies Rust.")
        self.assertEqual(insert_position(LINES, sec, "Rust", "Zed"), LINES.index("  - [Verus](https://github.com/verus-lang/verus) - Verifies Rust.") + 1)

    def test_empty_section_is_left_to_a_person(self):
        self.assertIsNone(insert_position(LINES, SECS["🌱 Empty"], None, "X"))


class CheckTests(unittest.TestCase):
    def test_good_description(self):
        self.assertEqual(check_entry("Beta", "Builds provers for Lean.", "x", False), [])

    def test_each_rule(self):
        self.assertTrue(check_entry("Beta", "builds provers.", "", False))
        self.assertTrue(check_entry("Beta", "Builds provers", "", False))
        self.assertTrue(check_entry("Beta", "Beta builds provers.", "", False))
        self.assertTrue(check_entry("Beta", "A revolutionary prover.", "", False))
        self.assertTrue(check_entry("Beta", " ".join(["word"] * 30) + ".", "", False))

    def test_name_may_repeat_for_papers(self):
        self.assertEqual(check_entry("Vericoding at Scale", "Vericoding at Scale is measured.", "", True), [])

    def test_numbers_must_come_from_the_source(self):
        self.assertTrue(check_entry("Beta", "Verifies 12,504 tasks.", "It verifies 300 tasks.", False))
        self.assertEqual(check_entry("Beta", "Verifies 12,504 tasks.", "benchmark of 12,504 specifications", False), [])


class DraftTests(unittest.TestCase):
    def test_happy_path_inserts_one_line(self):
        r = draft(README, page(), answer(), set())
        self.assertTrue(r.ok, r.problems)
        self.assertEqual(r.entry, "- [Beta](https://beta.example) - Builds provers for Lean.")
        self.assertEqual(len(r.lines), len(LINES) + 1)
        self.assertEqual(r.title, "Add Beta")
        self.assertEqual(r.slug, "beta")

    def test_paper_uses_fetched_title_and_arxiv_tag(self):
        p = page(title="Real Paper Title", text="Real Paper Title. We verify things.", paper=True, url="https://arxiv.org/abs/2611.00001")
        r = draft(README, p, answer(subsection="🧪 Field Reports", name="Invented Title", description="Verifies things.", venue_tag="arXiv 2030",
                                    code_url=None, evidence="Real Paper Title. We verify things."), set())
        self.assertTrue(r.ok, r.problems)
        self.assertEqual(r.entry, "- [Real Paper Title](https://arxiv.org/abs/2611.00001) - Verifies things. *arXiv 2026*")

    def test_nested_entry_is_indented(self):
        r = draft(README, page(text="Beta verifies Rust programs."), answer(subsection="🔧 Verifiers", group="Rust", description="Verifies Rust.", evidence="Beta verifies Rust programs."), set())
        self.assertTrue(r.ok, r.problems)
        self.assertTrue(r.entry.startswith("  - [Beta]"))

    def test_rejections(self):
        cases = {
            "declined": answer(fits=False, reason="Marketing."),
            "unsupported section": answer(subsection="📊 Benchmarks"),
            "unknown section": answer(subsection="Nope"),
            "needs group": answer(subsection="🔧 Verifiers"),
            "bad description": answer(description="no capital"),
            "name not on page": answer(name="Ghost"),
            "bad tag": answer(subsection="🧪 Field Reports", venue_tag="soon"),
            "missing tag": answer(subsection="🧪 Field Reports", venue_tag=None),
        }
        for label, ans in cases.items():
            with self.subTest(label):
                r = draft(README, page(), ans, set())
                self.assertFalse(r.ok)
                self.assertTrue(r.problems)

    def test_already_known_and_page_problems(self):
        self.assertFalse(draft(README, page(), answer(), {"beta.example"}).ok)
        bad = page()
        bad.problems = ["The repository is archived."]
        self.assertFalse(draft(README, bad, answer(), set()).ok)

    def test_code_url_must_be_on_the_page(self):
        p = page(text="Beta builds provers for Lean. https://github.com/b/beta", paper=True, url="https://arxiv.org/abs/2611.00002")
        ok = draft(README, p, answer(subsection="🧪 Field Reports", venue_tag="Blog 2026", code_url="https://github.com/b/beta"), set())
        self.assertIn("· [Code](https://github.com/b/beta)", ok.entry)
        bad = draft(README, page(paper=True, url="https://arxiv.org/abs/2611.00002"), answer(subsection="🧪 Field Reports", venue_tag="Blog 2026", code_url="https://github.com/made/up"), set())
        self.assertFalse(bad.ok)

    def test_a_repository_ignores_the_models_code_url(self):
        r = draft(README, page(), answer(code_url="https://github.com/made/up"), set())
        self.assertTrue(r.ok, r.problems)
        self.assertNotIn("Code]", r.entry)

    def test_scope_evidence_is_required_and_must_be_on_the_page(self):
        for label, evidence in {"missing": None, "short": "Lean.", "not on page": "Beta proves programs correct with Dafny."}.items():
            with self.subTest(label):
                r = draft(README, page(), answer(evidence=evidence), set())
                self.assertFalse(r.ok)
                self.assertIn("quote", r.problems[0])
        shouty = draft(README, page(), answer(evidence="BETA  builds provers\nfor LEAN."), set())
        self.assertTrue(shouty.ok, shouty.problems)

    def test_cap_warns_but_does_not_block(self):
        big = README.replace("- [Gamma](https://gamma.example) - Does gamma.\n", "".join(f"- [Z{i}](https://z{i}.example) - Z.\n" for i in range(14)))
        r = draft(big, page(), answer(), set())
        self.assertTrue(r.ok)
        self.assertTrue(r.warnings)


class HelperTests(unittest.TestCase):
    def test_parse_answer(self):
        self.assertEqual(parse_answer('```json\n{"fits": false, "reason": "x"}\n```'), {"fits": False, "reason": "x"})
        self.assertIsNone(parse_answer("no json"))
        self.assertIsNone(parse_answer('{"fits": "yes"}'))

    def test_compose_and_slug(self):
        self.assertEqual(compose("A", "https://a.example", "Does A.", "Blog 2026", "https://github.com/a/a", False),
                         "- [A](https://a.example) - Does A. *Blog 2026* · [Code](https://github.com/a/a)")
        self.assertEqual(slugify("Harnessing: Code Agents!"), "harnessing-code-agents")


if __name__ == "__main__":
    unittest.main()
