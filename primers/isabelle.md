---
name: Isabelle
filename: learnisabelle.thy
contributors:
    - ["JGalego"]
title: Learn Isabelle in Y Minutes
---

[Isabelle/HOL](https://isabelle.in.tum.de) is a proof assistant whose most widely used logic is higher-order logic. Equations produced by `fun` become simplification rules, so a goal that is only unfolding is closed by `simp`. `auto` will not choose an induction for you. The induction has to be named.

```text
theory Learn
  imports Main
begin

(* `fun` equations are simplification rules. `by simp` is the whole proof
   when unfolding and arithmetic are enough. *)
fun maximum :: "int ⇒ int ⇒ int" where
  "maximum a b = (if a ≥ b then a else b)"

lemma maximum_spec:
  "maximum a b ≥ a ∧ maximum a b ≥ b ∧ (maximum a b = a ∨ maximum a b = b)"
  by simp

fun sum :: "int list ⇒ int" where
  "sum [] = 0"
| "sum (x # xs) = x + sum xs"

(* `by auto` does not invent an induction. Name the induction, then simplify
   both cases. The cons case rewrites with the equation for `sum` and the
   induction hypothesis, which `simp_all` already has in context. *)
lemma sum_append: "sum (xs @ ys) = sum xs + sum ys"
  by (induction xs) simp_all

end
```
