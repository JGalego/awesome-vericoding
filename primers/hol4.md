---
name: HOL4
filename: learnhol4.sml
contributors:
    - ["JGalego"]
title: Learn HOL4 in Y Minutes
---

[HOL4](https://hol-theorem-prover.org) is a proof assistant in the LCF family, and the logic used for the CakeML compiler. The script below is what Holmake runs. A `Definition` stores its equation under a name, and a later tactic sees that equation only if the name is passed to it.

```text
open HolKernel boolLib bossLib Parse

val _ = new_theory "learn"

(* `Definition` stores the equation under the name `maximum_def`.
   `rw` is rewrite plus decision procedures; the definition is not in scope
   until you pass that name. *)
Definition maximum_def:
  maximum (a:num) b = if a >= b then a else b
End

Theorem maximum_spec:
  !a b. maximum a b >= a /\ maximum a b >= b /\
        (maximum a b = a \/ maximum a b = b)
Proof
  rw [maximum_def]
QED

Definition sum_def:
  (sum ([]: num list) = 0) /\
  (sum (x::xs) = x + sum xs)
End

(* `Induct` picks the first universally quantified variable.
   `>>` sends every subgoal to the next tactic. *)
Theorem sum_append:
  !xs ys. sum (xs ++ ys) = sum xs + sum ys
Proof
  Induct >> rw [sum_def]
QED

val _ = export_theory ()
```
