---
name: WhyML
filename: learnwhyml.mlw
contributors:
    - ["JGalego"]
title: Learn WhyML in Y Minutes
---

WhyML is the programming language of [Why3](https://why3.org). A module imports theories, defines logical functions, and states the contracts that become proof obligations. On Why3 1.8, Alt-Ergo 2.4 discharges every goal in the module below after the `split_vc` transformation.

```text
(* A WhyML module mixes a program and the logic the program is checked against.
   `use` imports a theory. `int` here is mathematical, from `int.Int`. *)
module Learn

  use int.Int

  (* `result` is the value of the expression after the `=`.
     One `ensures` is one proof obligation. A failed goal names that clause. *)
  let max (a b: int) : int
    ensures { result >= a /\ result >= b }
    ensures { result = a \/ result = b }
  = if a >= b then a else b

  (* `let function` is logical: it may be used in specifications.
     `let rec function` needs a `variant`, or Why3 rejects the definition.
     The variant is an expression of a well-founded order, here a non-negative int. *)
  let rec function sum_to (n: int) : int
    requires { n >= 0 }
    variant { n }
  = if n = 0 then 0 else n + sum_to (n - 1)

  (* `let ref i = 0` is a mutable variable, read as `i` and assigned with `<-`.
     A `while` with no `invariant` gives the prover nothing to use.
     After the loop, the invariant holds and the guard does not. *)
  let sum_loop (n: int) : int
    requires { n >= 0 }
    ensures { result = sum_to n }
  = let ref i = 0 in
    let ref s = 0 in
    while i < n do
      invariant { 0 <= i <= n }
      invariant { s = sum_to i }
      variant { n - i }
      i <- i + 1;
      s <- s + i
    done;
    s

end
```
