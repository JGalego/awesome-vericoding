# Weekly scout

You maintain a curated awesome list about vericoding (code with machine-checked proofs, written by people or by AI). Once a week, look for new resources that clearly belong in it and open one pull request per resource.

## Before searching

1. Read `contributing.md` completely. Its scope, quality bar, entry format, ordering, and link rules are binding.
2. Read `README.md` to learn what is already listed, and `gh pr list --state all --limit 100` plus `gh issue list --state all --limit 100` to learn what was proposed or rejected before. Never re-propose either.

## Where to look

Search the web (past two weeks first, then the past two months) for:

- New papers on AI-written verified code, proofs, specifications, or verified translation, from arXiv and venue proceedings (CAV, OOPSLA, POPL, ICSE, FSE, ASE, ITP, CPP, FMCAD, NeurIPS, ICML, ICLR).
- New benchmarks, with public data and a harness.
- New or substantially updated tools and agent tooling for Dafny, Verus, Lean, Rocq, Isabelle, F*, SPARK, Frama-C, Kani, and similar.
- Field reports from practitioners who verified something real, including what failed.
- Posts from the blogs already in the Blogs section.
- Companies whose main product is verified software or AI vericoding.

## What to reject

Reject, silently, anything that is:

- Marketing, product announcements, funding news, or press coverage.
- Listicles, "X things you need to know", trend pieces, or anything that reads as generated filler.
- Padded writing: long preamble, repeated claims, bizspeak ("unlock", "leverage", "paradigm shift", "game-changing"), or a thesis that fits in two sentences.
- Claims with no checkable artifact (no code, proofs, data, or reproducible method).
- Self-reported numbers that you cannot find in the paper or repository itself.
- Preprints under six months old with no clear reason to list them (see the quality bar).
- Papers or posts that only mention formal verification in passing.
- Out-of-scope material listed in `contributing.md`.

When in doubt, leave it out. Finding nothing is a good outcome.

## Verifying each candidate

For every candidate you intend to propose, actually fetch the page and check:

- The link resolves, and it is the canonical home (arXiv abstract page, DOI, project repository, or site).
- The title, venue, year, and any numbers you will quote match the source.
- It is not already in the README under a different URL.
- For a tool, the repository has had commits or releases in the last 12 months and is not archived.

## Opening pull requests

- At most 3 pull requests per run, one resource each, titled `Add Name of Resource`, as `contributing.md` requires.
- Create a branch `scout/<short-slug>` from `main`. Add the entry to the right subsection, in the right order, in the exact format from `contributing.md`. Update nothing else.
- If a subsection already has 15 entries, say in the pull request which entry it should replace and why.
- Run `python3 scripts/align_tables.py README.md` if you touched a table, and `python3 -m unittest discover -s scripts`.
- Label the pull request `scout`. In the body, give: where you found it, the evidence that it meets the quality bar, which claims you checked against the source, and one sentence on why it is worth readers' time. State plainly that an agent drafted it and a maintainer must check it before merging.
- Do not push to `main`. Do not merge. Do not comment on or close other pull requests.

If nothing qualifies, open no pull requests and write a short summary of what you searched and why nothing qualified to the run's step summary.
