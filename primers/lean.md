---
name: Lean 4
filename: learnlean.lean
contributors:
    - ["JGalego"]
title: Learn Lean 4 in Y Minutes
---

Lean 4 is a functional language and a proof assistant in the same system. The [Lean 4 tour](https://learnxinyminutes.com/lean4/) covers the language. This file is the verification slice: a theorem for each program, then one imperative loop whose verification conditions are produced by `mvcgen`. It typechecks on Lean 4.34.

```text
import Std.Tactic.Do

open Std.Do

set_option mvcgen.warning false

def maximum (a b : Int) : Int :=
  if a ≥ b then a else b

-- `split` follows the `if`. `omega` is linear arithmetic; it does not unfold
-- definitions, so `unfold` comes first.
theorem maximum_spec (a b : Int) :
    maximum a b ≥ a ∧ maximum a b ≥ b ∧ (maximum a b = a ∨ maximum a b = b) := by
  unfold maximum
  split <;> omega

def sum : List Int → Int
  | [] => 0
  | x :: xs => x + sum xs

theorem sum_append (xs ys : List Int) : sum (xs ++ ys) = sum xs + sum ys := by
  induction xs with
  | nil => simp [sum]
  | cons x xs ih => simp [sum, ih, Int.add_assoc]

-- `Fin xs.length` is an index that is in range by construction.
-- The obligation `0 < (x :: xs).length` is itself a proof, here `by simp`.
def lookup (xs : List α) (i : Fin xs.length) : α :=
  xs[i]

theorem lookup_zero (x : α) (xs : List α) :
    lookup (x :: xs) ⟨0, by simp⟩ = x := by
  simp [lookup]

-- `mvcgen` turns a `do` block into verification conditions.
-- In Lean 4.34 the tactic is marked experimental; the option above silences that warning.
def count (n : Nat) : Id Nat := do
  let mut i := 0
  while i < n do
    i := i + 1
  return i

-- A `while` becomes two obligations you have to supply: a variant (`inv1`)
-- and an invariant over `inl` (still looping) and `inr` (loop finished).
-- Straight-line `do` code needs neither. This loop does.
theorem count_spec (n : Nat) :
    ⦃⌜True⌝⦄ count n ⦃⇓ r => ⌜r = n⌝⦄ := by
  mvcgen [count]
  case inv1 =>
    exact fun i => ⟨n - i⟩
  case inv2 =>
    exact ⇓ c => match c with
      | Sum.inl i => ⌜i ≤ n⌝
      | Sum.inr i => ⌜i = n⌝
  all_goals simp_all [WhileVariant.eval, SVal.evalsTo]
  all_goals try omega
```
