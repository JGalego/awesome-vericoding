---
name: PVS
filename: learnpvs.pvs
contributors:
    - ["JGalego"]
title: Learn PVS in Y Minutes
---

[PVS](https://pvs.csl.sri.com) is a specification language and theorem prover. The theory states definitions and lemmas. Proofs are stored in a separate script, so this file alone does not contain a proof. What the typechecker produces from it are type-correctness conditions, including the termination obligation on a recursive definition.

```text
learn: THEORY
BEGIN

  maximum(a, b: int): int =
    IF a >= b THEN a ELSE b ENDIF

  % Proof: (grind)
  maximum_spec: LEMMA
    FORALL (a, b: int):
      maximum(a, b) >= a AND maximum(a, b) >= b AND
      (maximum(a, b) = a OR maximum(a, b) = b)

  % `nat` subtraction is partial. The `n - 1` sits under the ELSE, and PVS
  % emits a TCC asking for `n /= 0` there. The MEASURE is a second obligation:
  % `n - 1` is smaller than `n` on that same branch.
  sum(n: nat): RECURSIVE nat =
    IF n = 0 THEN 0 ELSE n + sum(n - 1) ENDIF
    MEASURE n

END learn
```
