"""Offline tests for check_currency.py. Run with: python3 -m unittest discover scripts"""

import unittest
from datetime import datetime, timezone

from check_currency import Repo, check, classify, extract_repos, repo_slug

NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)

README = """\
# Awesome Example

- [Tool](https://github.com/acme/tool) - A tool. ([paper](https://doi.org/10.1/x))
- [Paper](https://arxiv.org/abs/1234.5678) - A paper. *arXiv 2024* · [Code](https://github.com/lab/artifact)
  - [Nested](https://github.com/acme/nested.git) - Nested entry.
1. [Ordered](https://github.com/acme/ordered/) - Ordered entry.
| [Bench](https://github.com/lab/bench) | 2025 |
See the [discussions](https://github.com/acme/tool/discussions) and [org](https://github.com/orgs/acme).
"""


class ExtractTests(unittest.TestCase):
    def test_repo_slug_variants(self):
        self.assertEqual(repo_slug("https://github.com/a/b"), "a/b")
        self.assertEqual(repo_slug("https://github.com/a/b.git"), "a/b")
        self.assertEqual(repo_slug("https://github.com/a/b/tree/main/src"), "a/b")
        self.assertIsNone(repo_slug("https://github.com/orgs/acme"))
        self.assertIsNone(repo_slug("https://gitlab.com/a/b"))

    def test_main_links_versus_artifacts(self):
        repos = extract_repos(README)
        self.assertTrue(repos["acme/tool"].main_link)
        self.assertTrue(repos["acme/nested"].main_link)
        self.assertTrue(repos["acme/ordered"].main_link)
        self.assertFalse(repos["lab/artifact"].main_link)
        self.assertFalse(repos["lab/bench"].main_link)
        self.assertNotIn("orgs/acme", repos)

    def test_repeated_repository_is_merged(self):
        repos = extract_repos(README)
        self.assertEqual(repos["acme/tool"].lines, [3, 8])


def api(full_name, archived=False, pushed="2026-09-01T00:00:00Z"):
    return 200, {"full_name": full_name, "archived": archived, "pushed_at": pushed}


class ClassifyTests(unittest.TestCase):
    def test_healthy(self):
        self.assertIsNone(classify(Repo("a/b", True), *api("a/b"), NOW, 365))

    def test_missing(self):
        self.assertEqual(classify(Repo("a/b"), 404, None, NOW, 365).kind, "missing")

    def test_moved_is_case_insensitive(self):
        self.assertIsNone(classify(Repo("A/B"), *api("a/b"), NOW, 365))
        finding = classify(Repo("a/b"), *api("c/b"), NOW, 365)
        self.assertEqual((finding.kind, finding.detail), ("moved", "now at https://github.com/c/b"))

    def test_archived(self):
        self.assertEqual(classify(Repo("a/b"), *api("a/b", archived=True), NOW, 365).kind, "archived")

    def test_inactive_only_for_main_links(self):
        stale = api("a/b", pushed="2024-01-01T00:00:00Z")
        self.assertEqual(classify(Repo("a/b", main_link=True), *stale, NOW, 365).kind, "inactive")
        self.assertIsNone(classify(Repo("a/b", main_link=False), *stale, NOW, 365))

    def test_api_failure_is_never_healthy(self):
        with self.assertRaises(LookupError):
            classify(Repo("a/b"), 403, None, NOW, 365)

    def test_check_separates_unchecked(self):
        responses = {"a/ok": api("a/ok"), "a/gone": (404, None), "a/limited": (429, None)}
        repos = {slug: Repo(slug, True) for slug in responses}
        findings, unchecked = check(repos, lambda slug: responses[slug], NOW, 365)
        self.assertEqual([f.slug for f in findings], ["a/gone"])
        self.assertEqual(len(unchecked), 1)


if __name__ == "__main__":
    unittest.main()
