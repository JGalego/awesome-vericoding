---
name: Velvet
filename: learnvelvet.lean
contributors:
    - ["JGalego"]
title: Learn Velvet in Y Minutes
---

[Velvet](https://velvetprover.dev) is a Dafny-style language embedded in Lean. `method` elaborates to a monadic program. `prove_correct` is an ordinary Lean proof of the verification conditions, so a goal that automation does not close is finished with Lean tactics on that same goal.

```text
import Velvet

method maximum (a b : Nat) returns (r : Nat)
  ensures r ≥ a ∧ r ≥ b ∧ (r = a ∨ r = b)
do
  if a ≥ b then return a else return b

prove_correct maximum by
  velvet_vcgen [maximum] with finish

method count (n : Nat) returns (r : Nat)
  ensures r = n
do
  let mut i : Nat := 0
  while loop_cond: i ≠ n
    invariant bound: i ≤ n
    decreasing remaining: n - i
  do
    i := i + 1
  return i

prove_correct count by
  velvet_vcgen [count] with finish
```

`with finish` asks Velvet to discharge every condition with its default automation. Replacing `finish` with a `case` is how a condition that automation misses is proved by hand, in Lean, against the same verification condition.
