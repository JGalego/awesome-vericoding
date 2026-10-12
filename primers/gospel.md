---
name: Gospel
filename: learngospel.ml
contributors:
    - ["JGalego"]
title: Learn Gospel in Y Minutes
---

Gospel attaches a contract to an OCaml declaration in a comment that starts with `(*@` and follows that declaration. [Cameleer](https://github.com/ocaml-gospel/cameleer) translates the result to WhyML. `requires` is assumed in the body and proved at each call. `checks` is the same kind of formula, and it can also be monitored at run time.

```text
(* In the .mli. `r` names the result.
   `requires` is assumed in the body and proved at each call.
   `checks` is the same shape of formula, and it is also a check Cameleer
   can turn into a test: a precondition you are willing to monitor. *)
val maximum : int -> int -> int
(*@ r = maximum a b
    ensures r >= a
    ensures r >= b
    ensures r = a || r = b *)

(* `checks b > 0` excludes the divisor OCaml would trap on.
   With `a >= 0`, OCaml's `/` matches this division. *)
val divide : int -> int -> int
(*@ q = divide a b
    requires a >= 0
    checks b > 0
    ensures q * b <= a
    ensures a < (q + 1) * b *)

(* In the .ml. The header binds the names the clauses use.
   Gospel integers are Why3's mathematical integers. This contract does
   not, by itself, say anything about OCaml's wrapping overflow. *)
let maximum a b =
  if a >= b then a else b
(*@ r = maximum a b
    ensures r >= a
    ensures r >= b
    ensures r = a || r = b *)
```
