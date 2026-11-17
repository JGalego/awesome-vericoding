// Tests for scripts/hatches.mjs. Run with:
//   node --test scripts/test_hatches.mjs

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { badge, commentRanges, detect, primerCode, scan, SYNTAX } from "./hatches.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const TRUST = JSON.parse(execFileSync("python3", [join(ROOT, "scripts/build_data.py")], { encoding: "utf8" })).trust;
const ROW = Object.fromEntries(TRUST.map((row) => [row.verifier, row]));

const counted = (findings) => findings.filter((f) => !f.comment).map((f) => f.match);
const commented = (findings) => findings.filter((f) => f.comment).map((f) => f.match);

test("every Trust Checklist row has comment syntax and patterns that compile", () => {
  for (const row of TRUST) {
    assert.ok(SYNTAX[row.verifier], `no comment syntax for ${row.verifier}`);
    for (const hatch of row.hatches) {
      const regex = new RegExp(hatch.pattern, "g" + row.flags);
      assert.match(hatch.text.replace("(...)", "(x)"), regex, `${row.verifier}: ${hatch.text}`);
    }
  }
});

test("comment ranges: line, nested block, and markers inside strings", () => {
  const lean = 'def s := "-- not a comment" -- a comment\n/- outer /- inner -/ still -/ x';
  const ranges = commentRanges(lean, SYNTAX["Lean 4"]).map(([a, b]) => lean.slice(a, b));
  assert.deepEqual(ranges, ["-- a comment", "/- outer /- inner -/ still -/"]);
  const rust = "let c = '\"'; // after a quote char\nlet d = 1;";
  assert.deepEqual(commentRanges(rust, SYNTAX.Verus).map(([a, b]) => rust.slice(a, b)), ["// after a quote char"]);
});

test("Lean: sorry in code counts, sorry in comments does not", () => {
  const code = "theorem a : True := by\n  sorry\n-- never leave a sorry\n/- or a /- nested -/ sorry -/\n";
  const findings = scan(code, ROW["Lean 4"]);
  assert.deepEqual(counted(findings), ["sorry"]);
  assert.deepEqual(commented(findings), ["sorry", "sorry"]);
  assert.equal(findings[0].line, 2);
  assert.equal(findings[0].column, 3);
});

test("Lean: attributes with arguments, and words that only contain a hatch", () => {
  const code = "@[simp, implemented_by fastImpl] def f := 1\ntheorem axiomatic_ok : True := trivial\naxiom bad : False\n";
  assert.deepEqual(counted(scan(code, ROW["Lean 4"])), ["@[simp, implemented_by fastImpl]", "axiom"]);
});

test("F*: options inside a string still count", () => {
  const code = '#set-options "--admit_smt_queries true"\nlet f () : Lemma False = admit ()\n(* assume nothing *)\n';
  const findings = scan(code, ROW["F*"]);
  assert.deepEqual(counted(findings), ["--admit_smt_queries true", "admit ()"]);
  assert.deepEqual(commented(findings), ["assume"]);
});

test("SPARK: case-insensitive, and SPARK_Mode on is fine", () => {
  const code = "package P with SPARK_Mode is\n   pragma assume (X > 0);\n   pragma Spark_Mode (OFF);\nend P;\n";
  assert.deepEqual(counted(scan(code, ROW.SPARK)), ["pragma assume", "Spark_Mode (OFF)"]);
});

test("Dafny, Rocq, Isabelle, Verus, Kani", () => {
  assert.deepEqual(counted(scan('method {:extern "Foo"} M()\n// assume false;\nassume x > 0;', ROW.Dafny)), ['{:extern "Foo"}', "assume"]);
  assert.deepEqual(counted(scan("Lemma l : False.\nProof. admit. Admitted.\n(* Admitted *)", ROW.Rocq)), ["admit", "Admitted"]);
  assert.deepEqual(counted(scan("text ‹we never use sorry›\nlemma x: False sorry", ROW.Isabelle)), ["sorry"]);
  assert.deepEqual(counted(scan("#[verifier::external_body]\nfn f() { assume(x > 0); }", ROW.Verus)), ["#[verifier::external_body]", "assume("]);
  assert.deepEqual(counted(scan("// Kani assumes requires\nkani::assume(x < 3);", ROW.Kani)), ["kani::assume"]);
});

test("detect", () => {
  assert.equal(detect("", "proof.dfy"), "Dafny");
  assert.equal(detect("", "Foo.thy"), "Isabelle");
  assert.equal(detect("verus! {\n fn f() {}\n}"), "Verus");
  assert.equal(detect("#[kani::proof]\nfn check() {}"), "Kani");
  assert.equal(detect("theory Scratch\n  imports Main\nbegin\nend"), "Isabelle");
  assert.equal(detect("Lemma l : 1 = 1.\nProof. reflexivity. Qed."), "Rocq");
  assert.equal(detect("theorem t : 1 = 1 := by rfl"), "Lean 4");
  assert.equal(detect("method M(x: int) returns (y: int)\n  ensures y > x\n{ y := x + 1; }"), "Dafny");
  assert.equal(detect("module Learn\nlet lemma_x () : Lemma (1 == 1) = ()"), "F*");
  assert.equal(detect("package Learn with SPARK_Mode is\nend Learn;"), "SPARK");
  assert.equal(detect("fn main() {}", "main.rs"), null);
});

test("badge", () => {
  assert.deepEqual(badge(0), { schemaVersion: 1, label: "sorry", message: "0", color: "brightgreen" });
  assert.equal(badge(3).color, "red");
});

test("primerCode finds the block and its first line", () => {
  const markdown = "---\nname: X\n---\n\nIntro.\n\n```text\nline one\nline two\n```\n";
  assert.deepEqual(primerCode(markdown), { code: "line one\nline two\n", firstLine: 8 });
});
