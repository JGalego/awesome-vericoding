"""Offline tests for whats_new.py. Run with: python3 -m unittest discover scripts"""

import unittest
import xml.etree.ElementTree as ET

from whats_new import RECORD, FIELD, feed, new_entries, page, parse_log


def commit(sha, date, *added):
    diff = "".join(f"+{line}\n" for line in added)
    return f"{RECORD}{sha}{FIELD}{date}{FIELD}Subject {sha}\n\ndiff --git a/README.md b/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old line\n{diff}"


LOG = (
    commit("a", "2026-10-12T10:00:00+01:00", "- [Dafny](https://dafny.org) - Old.", "- [Lean](https://lean-lang.org) - Old.")
    + commit("b", "2026-10-12T18:00:00+01:00", "- [Primer](https://example.com/primer) - Same day.")
    + commit("c", "2026-11-16T09:00:00+00:00", "  - [Verus](https://verus.example) - New.", "Prose with a [link](https://prose.example).")
    + commit("d", "2026-11-17T09:00:00+00:00", "- [Dafny](https://dafny.org) - Moved.", "| [Bench](https://bench.example) | 2025 |",
             "- [Lean 4](https://lean-lang.org) - Renamed.", "- [F\\*](https://fstar.example) - Uses <html> & \"quotes\".")
)


def entry(name, url, description="Text."):
    return {"name": name, "url": url, "description": description, "section": "Classic", "subsection": "Tools", "group": None}


ENTRIES = [
    entry("Dafny", "https://dafny.org"),
    entry("Lean 4", "https://lean-lang.org"),
    entry("Primer", "https://example.com/primer"),
    entry("Verus", "https://verus.example"),
    entry("Bench", "https://bench.example"),
    entry("F*", "https://fstar.example", 'Uses <html> & "quotes".'),
    entry("Prose", "https://prose.example"),
]


class WhatsNewTests(unittest.TestCase):
    def setUp(self):
        self.commits = parse_log(LOG)
        self.new = new_entries(ENTRIES, self.commits)

    def test_parses_only_added_lines(self):
        self.assertEqual([c["sha"] for c in self.commits], ["a", "b", "c", "d"])
        self.assertNotIn("old line", self.commits[0]["added"])
        self.assertNotIn(" b/README.md", "".join(self.commits[0]["added"]))

    def test_first_day_moves_renames_and_prose_are_not_new(self):
        self.assertEqual([e["name"] for e in self.new], ["Bench", "F*", "Verus"])

    def test_newest_first_with_dates(self):
        self.assertEqual([e["added"][:10] for e in self.new], ["2026-11-17", "2026-11-17", "2026-11-16"])
        self.assertEqual(self.new[-1]["commit"], "c")

    def test_page_escapes_and_groups_by_day(self):
        html = page(self.new, "https://site.example/")
        self.assertIn("{% raw %}", html)
        self.assertEqual(html.count("<h2"), 2)
        self.assertIn("17 November 2026", html)
        self.assertIn("Uses &lt;html&gt; &amp; &quot;quotes&quot;.", html)
        self.assertIn('href="https://site.example/feed.xml"', html)

    def test_feed_is_valid_atom(self):
        root = ET.fromstring(feed(self.new, "https://site.example/"))
        ns = {"a": "http://www.w3.org/2005/Atom"}
        self.assertEqual(root.find("a:updated", ns).text, "2026-11-17T09:00:00+00:00")
        titles = [e.find("a:title", ns).text for e in root.findall("a:entry", ns)]
        self.assertEqual(titles, ["Bench", "F*", "Verus"])

    def test_empty_history(self):
        self.assertEqual(new_entries(ENTRIES, []), [])
        self.assertIn("Nothing yet.", page([]))
        ET.fromstring(feed([]))


if __name__ == "__main__":
    unittest.main()
