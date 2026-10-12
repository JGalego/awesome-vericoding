# Contributing

Thanks for helping. This list is a curation, not a catalog. Every entry should be among the best resources on vericoding, with one sentence telling readers why it is worth their time.

## Ground Rules

- One resource per pull request, titled `Add Name of Resource`.
- Search the README, open pull requests, and closed issues first.
- Only suggest things you have used or read.
- AI tools may help you draft, but check every link, number, and claim yourself. Pull requests that look like unreviewed AI output will be closed. Vericoding is about not trusting unchecked output, and that applies here too.
- If you only want to suggest a resource, use the [suggestion form](https://github.com/JGalego/awesome-vericoding/issues/new?template=suggest-resource.yml) instead.

## Scope

In scope is anything about writing code that comes with a machine-checked proof against a formal specification: languages, verifiers, proof assistants, verified systems, learning material, and research on AI that writes code, specifications, or proofs.

Out of scope:

- Testing, fuzzing, and static analysis that do not produce proofs.
- Design-level model checking with no link to code, such as most TLA+ work. Awesome TLA+ covers it.
- Formalized mathematics, unless the technique carries over to program proofs. The Theorem-Proving Models section has a high bar.
- Services that sell audits without public tools or research.

## Quality Bar

| Type              | Requirements                                                                                                                                                                  |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tool              | Public, documented, and installable. Commits or releases within the last 12 months. Not archived.                                                                             |
| Paper             | Peer-reviewed at a recognized venue, or at least 25 citations, or introduces a benchmark or tool others use. Preprints under six months old need a clear reason to be listed. |
| Benchmark         | Public data, a documented size, and an evaluation harness or protocol.                                                                                                        |
| Learning resource | Current with the tool it teaches. Free, or marked 💰.                                                                                                                         |
| Essay             | A widely read argument or story about verified software by a practitioner or researcher. Not a product announcement.                                                          |
| Organization      | Verified software or AI vericoding is a primary focus, with a public description of the work.                                                                                 |

Subsections are shortlists and aim for at most 15 entries. When a subsection is full, say which entry yours should replace and why. One in, one out.

## Entry Format

Tools and other resources:

```md
- [Name](https://project.example) - What it does and why it matters, in one sentence.
```

A tool entry may cite its defining paper at the end of the description, for example `([OOPSLA 2023 paper](https://doi.org/10.1145/3586037))`.

Papers:

```md
- [Exact Paper Title](https://arxiv.org/abs/2409.13082) - What it contributes, in one sentence. *OOPSLA 2025* · [Code](https://github.com/org/repo)
```

Essays use the paper format with a short venue tag such as *Blog 2026*.

Benchmarks go in the Benchmarks table. Keep it sorted by year, then by name, and realign the table with `python3 scripts/align_tables.py README.md`. The pre-commit hook does this for you.

Description rules:

- Start with a capital letter and end with a period. Keep it under 30 words, and do not repeat the entry's name.
- State facts, not marketing. Words like "blazing", "best", or "revolutionary" will be removed. Numbers must come from the source.
- Use the published venue and year as the venue tag, such as *OOPSLA 2025*. Use *arXiv 2026* for preprints, and update the tag when the paper is published.
- Use current names, such as Rocq instead of Coq.

Section headings start with an emoji, followed by an overview in italics: one short sentence with no commas or semicolons that adds something the heading does not. If you add or rename a section, update the table of contents to match; awesome-lint checks it.

Markers:

- ⭐ marks a good place to start. Maintainers assign it, at most two per subsection.
- 🏭 marks production use. Link the public evidence in your pull request.
- 💰 marks a paid resource.

## Ordering

- Tools, books, courses, venues, forums, and organizations are alphabetical.
- Papers, essays, and verified systems are ordered by year of first public release, oldest first, so each subsection reads as a lineage.
- Benchmarks are ordered by year, then by name.

## Links

- Link the canonical home: the project site or repository, the arXiv abstract page (not the PDF) for papers, or the DOI for papers without an arXiv version.
- Use HTTPS and drop tracking parameters.
- When a repository moves, link the new location instead of relying on the redirect.
- A URL may appear only once as a main link in the README, because awesome-lint rejects duplicates. Refer to other entries by name.
- When a page disappears, link a Wayback Machine snapshot with an explicit timestamp, such as `https://web.archive.org/web/20260101000000/https://example.com/page`.

## Before Opening a Pull Request

1. Install the hooks once with `pip install pre-commit && pre-commit install`, or run `pre-commit run --all-files` before pushing. The hooks run awesome-lint, align tables, and fix whitespace.
2. Check the two entries next to yours. If one no longer meets the quality bar, fix it or say so in your pull request.
3. Fill in the pull request template.

## Maintenance

Three automated checks keep the list healthy, and a fourth publishes it:

- **Lint** runs awesome-lint on every pull request.
- **Links** runs lychee on every pull request and once a month, and opens an issue when links break.
- **Currency** checks every GitHub repository in the list once a month and opens an issue for any that are archived, missing, or inactive for over a year.
- **Pages** publishes the list as a website on every push to `main`. To preview it locally, run `bundle install && bundle exec jekyll serve --baseurl ""` and open <http://localhost:4000/>.

Tools that are archived or inactive for more than a year are removed. Papers stay unless they are retracted or clearly superseded.

## Mentioned in Awesome Vericoding

If your project is listed, you are welcome to add this badge to its README:

```md
[![Mentioned in Awesome Vericoding](https://awesome.re/mentioned-badge.svg)](https://github.com/JGalego/awesome-vericoding)
```
