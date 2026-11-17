#!/usr/bin/env node
// Search code for the escape hatches listed in the README's Trust Checklist.
//
//   node scripts/hatches.mjs primers [--badge badges/sorry.json] [--no-fail]
//   node scripts/hatches.mjs FILE... [--verifier "Lean 4"]
//
// Hatches inside comments are reported apart from those in code, using each
// verifier's comment syntax.
//
// `primers` scans every primer whose tool has a Trust Checklist row and, with
// --badge, writes the shields.io endpoint JSON behind the README's `sorry`
// badge. Hatches inside comments are listed but not counted. The exit status
// is 1 when a hatch is found outside a comment, unless --no-fail is given.
//
// The patterns are built from the README with scripts/build_data.py, or read
// from an already built file with --data.

import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

// Comment syntax for each Trust Checklist row. Block comments nest in all of
// these languages. Isabelle's cartouches hold prose (`text ‹...›`), and no
// escape hatch on its row can appear inside one, so they are treated as
// comments.
export const SYNTAX = {
  Dafny: { line: ["//"], block: [["/*", "*/"]] },
  Verus: { line: ["//"], block: [["/*", "*/"]] },
  Kani: { line: ["//"], block: [["/*", "*/"]] },
  "Lean 4": { line: ["--"], block: [["/-", "-/"]] },
  Rocq: { line: [], block: [["(*", "*)"]] },
  Isabelle: { line: [], block: [["(*", "*)"], ["‹", "›"], ["\\<open>", "\\<close>"]] },
  "F*": { line: ["//"], block: [["(*", "*)"]] },
  SPARK: { line: ["--"], block: [] },
};

const FALLBACK = { line: ["//"], block: [["/*", "*/"]] };

// [start, end) offsets of every comment. Strings are skipped so that a
// comment marker inside a string literal does not open a comment, but the
// string itself still counts as code: F* options such as
// `#set-options "--admit_smt_queries true"` live in strings.
export function commentRanges(code, syntax = FALLBACK) {
  const ranges = [];
  const n = code.length;
  let i = 0;
  while (i < n) {
    if (code[i] === "'" && code.startsWith("'\"'", i)) {
      i += 3;
      continue;
    }
    if (code[i] === "'" && code.startsWith("'\\\"'", i)) {
      i += 4;
      continue;
    }
    if (code[i] === '"') {
      i++;
      while (i < n && code[i] !== '"' && code[i] !== "\n") i += code[i] === "\\" ? 2 : 1;
      i++;
      continue;
    }
    const line = syntax.line.find((marker) => code.startsWith(marker, i));
    if (line) {
      const newline = code.indexOf("\n", i);
      const end = newline === -1 ? n : newline;
      ranges.push([i, end]);
      i = end;
      continue;
    }
    const block = syntax.block.find(([open]) => code.startsWith(open, i));
    if (block) {
      const [open, close] = block;
      let depth = 0;
      let j = i;
      while (j < n) {
        if (code.startsWith(open, j)) {
          depth++;
          j += open.length;
        } else if (code.startsWith(close, j)) {
          depth--;
          j += close.length;
          if (depth === 0) break;
        } else {
          j++;
        }
      }
      ranges.push([i, j]);
      i = j;
      continue;
    }
    i++;
  }
  return ranges;
}

function lineStarts(code) {
  const starts = [0];
  for (let i = 0; i < code.length; i++) if (code[i] === "\n") starts.push(i + 1);
  return starts;
}

// Index of the last element <= value.
function floorIndex(sorted, value) {
  let lo = 0;
  let hi = sorted.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (sorted[mid] <= value) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

// Every escape hatch from one Trust Checklist row that appears in `code`,
// in source order: { hatch, match, index, end, line, column, comment }.
export function scan(code, row) {
  const comments = commentRanges(code, SYNTAX[row.verifier] || FALLBACK);
  const commentStarts = comments.map(([start]) => start);
  const inComment = (index) => {
    if (!comments.length) return false;
    const [start, end] = comments[floorIndex(commentStarts, index)];
    return index >= start && index < end;
  };
  const starts = lineStarts(code);
  const findings = [];
  const seen = new Set();
  for (const hatch of row.hatches) {
    const regex = new RegExp(hatch.pattern, "g" + (row.flags || ""));
    for (const match of code.matchAll(regex)) {
      const key = `${match.index}:${match[0].length}`;
      if (seen.has(key)) continue;
      seen.add(key);
      const line = floorIndex(starts, match.index);
      findings.push({
        hatch: hatch.text,
        match: match[0],
        index: match.index,
        end: match.index + match[0].length,
        line: line + 1,
        column: match.index - starts[line] + 1,
        comment: inComment(match.index),
      });
    }
  }
  return findings.sort((a, b) => a.index - b.index || a.end - b.end);
}

const EXTENSIONS = {
  dfy: "Dafny",
  lean: "Lean 4",
  v: "Rocq",
  thy: "Isabelle",
  fst: "F*",
  fsti: "F*",
  ads: "SPARK",
  adb: "SPARK",
  ada: "SPARK",
};

// A best guess at which Trust Checklist row applies, or null.
export function detect(code, filename = "") {
  const dot = filename.lastIndexOf(".");
  const extension = dot === -1 ? "" : filename.slice(dot + 1).toLowerCase();
  if (EXTENSIONS[extension]) return EXTENSIONS[extension];
  if (/\bverus!\s*\{|\bvstd::/.test(code)) return "Verus";
  if (/#\[kani::|\bkani::/.test(code)) return "Kani";
  if (extension === "rs") return null;
  if (/^\s*theory\s+\S+[\s\S]*?\bimports\b[\s\S]*?\bbegin\b/m.test(code)) return "Isabelle";
  if (/\bSPARK_Mode\b/i.test(code) || /^\s*(?:package|procedure)\s+[\w.]+[\s\S]*?\bis\b[\s\S]*?\bend\s+[\w.]+\s*;/im.test(code)) return "SPARK";
  if (/^\s*module\s+[A-Z][\w.]*\s*$/m.test(code) && /\b(?:Lemma|Tot|GTot)\b/.test(code)) return "F*";
  if (/\b(?:Qed|Admitted|Defined)\s*\./.test(code) || /^\s*(?:Fixpoint|Inductive|Theorem|Lemma)\s/m.test(code)) return "Rocq";
  if (/:=\s*by\b|^\s*(?:import\s+[A-Z]\w*|open\s+\w|namespace\s+\w)/m.test(code)) return "Lean 4";
  if (/\b(?:method|lemma|predicate|function)\b[^{]*\b(?:requires|ensures|decreases)\b/.test(code)) return "Dafny";
  if (/\b(?:theorem|lemma|def|example)\b[\s\S]*?:=/.test(code)) return "Lean 4";
  return null;
}

// A shields.io endpoint badge for a count of escape hatches.
export function badge(count) {
  return {
    schemaVersion: 1,
    label: "sorry",
    message: String(count),
    color: count === 0 ? "brightgreen" : "red",
  };
}

// The Trust Checklist row for each primer. Primers for tools without a row are
// not scanned and are listed as uncovered.
export const PRIMER_ROWS = {
  dafny: "Dafny",
  fstar: "F*",
  isabelle: "Isabelle",
  kani: "Kani",
  lean: "Lean 4",
  rocq: "Rocq",
  spark: "SPARK",
  velvet: "Lean 4",
  verus: "Verus",
};

function parseArgs(argv) {
  const options = { data: null, badge: null, fail: true, verifier: null, files: [] };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--data") options.data = argv[++i];
    else if (arg === "--badge") options.badge = argv[++i];
    else if (arg === "--verifier") options.verifier = argv[++i];
    else if (arg === "--no-fail") options.fail = false;
    else if (arg === "-h" || arg === "--help") options.help = true;
    else options.files.push(arg);
  }
  return options;
}

function loadTrust(path) {
  const text = path
    ? readFileSync(path, "utf8")
    : execFileSync("python3", [join(ROOT, "scripts/build_data.py")], { encoding: "utf8" });
  return JSON.parse(text).trust;
}

// The primer's code block and the line of the Markdown file it starts on.
export function primerCode(markdown) {
  const match = markdown.match(/^```[^\n]*\n([\s\S]*?)^```[ \t]*$/m);
  if (!match) return null;
  const start = match.index + match[0].indexOf("\n") + 1;
  return { code: match[1], firstLine: markdown.slice(0, start).split("\n").length };
}

function report(file, findings, lineOffset = 0) {
  const annotate = process.env.GITHUB_ACTIONS === "true";
  for (const f of findings) {
    const line = f.line + lineOffset;
    const where = `${file}:${line}:${f.column}`;
    if (f.comment) {
      console.log(`  ${where}: \`${f.match}\` in a comment (not counted)`);
    } else {
      console.log(`  ${where}: \`${f.match}\` (escape hatch \`${f.hatch}\`)`);
      if (annotate) console.log(`::error file=${file},line=${line},col=${f.column}::Escape hatch \`${f.match}\` (Trust Checklist: \`${f.hatch}\`)`);
    }
  }
}

function scanPrimers(trust, options) {
  const rows = Object.fromEntries(trust.map((row) => [row.verifier, row]));
  const primers = execFileSync("python3", [join(ROOT, "scripts/primers.py"), "names"], { encoding: "utf8" })
    .trim()
    .split(/\s+/);
  let count = 0;
  const uncovered = [];
  for (const name of primers) {
    const row = rows[PRIMER_ROWS[name]];
    if (!row) {
      uncovered.push(name);
      continue;
    }
    const file = `primers/${name}.md`;
    const primer = primerCode(readFileSync(join(ROOT, file), "utf8"));
    if (!primer) throw new Error(`${file}: no code block`);
    const findings = scan(primer.code, row);
    const counted = findings.filter((f) => !f.comment).length;
    count += counted;
    console.log(`${file} (${row.verifier}): ${counted ? `${counted} escape hatch${counted === 1 ? "" : "es"}` : "clean"}`);
    report(file, findings, primer.firstLine - 1);
  }
  console.log(`\n${count} escape hatch${count === 1 ? "" : "es"} in ${primers.length - uncovered.length} primers.`);
  if (uncovered.length) console.log(`No Trust Checklist row yet, not scanned: ${uncovered.join(", ")}.`);
  if (options.badge) {
    mkdirSync(dirname(resolve(options.badge)), { recursive: true });
    writeFileSync(options.badge, JSON.stringify(badge(count)) + "\n");
    console.log(`Wrote ${options.badge}`);
  }
  return count;
}

function scanFiles(trust, options) {
  const rows = Object.fromEntries(trust.map((row) => [row.verifier, row]));
  let count = 0;
  for (const file of options.files) {
    const code = readFileSync(file, "utf8");
    const verifier = options.verifier || detect(code, basename(file));
    const row = rows[verifier];
    if (!row) {
      console.error(`${file}: cannot tell which verifier this is for; pass --verifier (one of: ${Object.keys(rows).join(", ")})`);
      return -1;
    }
    const findings = scan(code, row);
    const counted = findings.filter((f) => !f.comment).length;
    count += counted;
    console.log(`${file} (${verifier}): ${counted ? `${counted} escape hatch${counted === 1 ? "" : "es"}` : "clean"}`);
    report(relative(process.cwd(), resolve(file)), findings);
  }
  return count;
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help || !options.files.length) {
    console.log("usage: node scripts/hatches.mjs primers [--badge FILE] [--no-fail]\n       node scripts/hatches.mjs FILE... [--verifier NAME]");
    return options.help ? 0 : 2;
  }
  const trust = loadTrust(options.data);
  const count = options.files.length === 1 && options.files[0] === "primers" ? scanPrimers(trust, options) : scanFiles(trust, options);
  if (count < 0) return 2;
  return count > 0 && options.fail ? 1 : 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = main();
}
