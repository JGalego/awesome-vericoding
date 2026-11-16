// Escape-hatch scanning, shared by the scanner page and scripts/hatches.mjs.
//
// The patterns come from the README's Trust Checklist, which
// scripts/build_data.py turns into one regular expression per escape hatch.
// This module adds what the checklist does not say: where each verifier's
// comments are, so that a `sorry` mentioned in a comment is reported apart
// from a `sorry` in the code.

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
