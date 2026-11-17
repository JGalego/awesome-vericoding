"""Offline tests for primers.py. Run with: python3 -m unittest discover scripts"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import primers
from primers import PrimerError, affected, extract, names, parse

PRIMER = """\
---
name: Example
filename: learnexample.dfy
---

Intro.

```text
method M() {}
```
"""


class ParseTests(unittest.TestCase):
    def test_filename_and_code(self):
        self.assertEqual(parse(PRIMER), ("learnexample.dfy", "method M() {}\n"))

    def test_rejects_missing_or_extra_blocks(self):
        with self.assertRaisesRegex(PrimerError, "found 0"):
            parse(PRIMER.replace("```text\nmethod M() {}\n```\n", ""))
        with self.assertRaisesRegex(PrimerError, "found 2"):
            parse(PRIMER + "\n```text\nmore\n```\n")

    def test_rejects_paths_in_filename(self):
        with self.assertRaisesRegex(PrimerError, "plain file name"):
            parse(PRIMER.replace("learnexample.dfy", "../escape.dfy"))
        with self.assertRaisesRegex(PrimerError, "no filename"):
            parse(PRIMER.replace("filename: learnexample.dfy\n", ""))

    def test_every_primer_extracts(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in names():
                path = extract(name, Path(directory))
                self.assertTrue(path.read_text(encoding="utf-8").strip(), name)


class AffectedTests(unittest.TestCase):
    def test_only_touched_primers(self):
        with mock.patch.object(primers, "checked", return_value=["dafny", "lean", "rocq"]):
            self.assertEqual(affected(["primers/lean.md", "README.md"]), ["lean"])
            self.assertEqual(affected(["scripts/primers/rocq.sh"]), ["rocq"])
            self.assertEqual(affected(["primers/agda.md"]), [], "agda has no check script")
            self.assertEqual(affected([]), [])

    def test_shared_files_check_everything(self):
        with mock.patch.object(primers, "checked", return_value=["dafny", "lean"]):
            self.assertEqual(affected(["scripts/primers.py"]), ["dafny", "lean"])
            self.assertEqual(affected([".github/workflows/primers.yml"]), ["dafny", "lean"])


if __name__ == "__main__":
    unittest.main()
