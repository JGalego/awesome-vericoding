#!/usr/bin/env node
// Search code for the escape hatches listed in the README's Trust Checklist.
//
//   node scripts/hatches.mjs primers [--badge badges/sorry.json] [--no-fail]
//   node scripts/hatches.mjs FILE... [--verifier "Lean 4"]
//
// `primers` scans every primer whose tool has a Trust Checklist row and, with
// --badge, writes the shields.io endpoint JSON behind the README's `sorry`
// badge. Hatches inside comments are listed but not counted. The exit status
// is 1 when a hatch is found outside a comment, unless --no-fail is given.
//
// The patterns are read from --data (default: data/list.json); when that file
// does not exist they are built from the README with scripts/build_data.py.

import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { badge, detect, scan } from "../assets/js/hatches.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

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
  const options = { data: join(ROOT, "data/list.json"), badge: null, fail: true, verifier: null, files: [] };
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
  const text = existsSync(path)
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
