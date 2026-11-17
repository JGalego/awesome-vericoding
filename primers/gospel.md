---
name: Gospel
filename: learngospel.ml
contributors:
    - ["JGalego"]
title: Learn Gospel in Y Minutes
---

Gospel attaches a contract to an OCaml declaration in a comment that starts with `(*@` and follows that declaration. [Cameleer](https://github.com/ocaml-gospel/cameleer) translates the result to WhyML. `requires` is assumed in the body and proved at each call. `checks` is also a precondition, but when it is false the function raises `Invalid_argument` instead of behaving arbitrarily.

```text
(* A module type holds what an .mli would. `r` names the result.
   `requires` is assumed in the body and proved at each call. *)
module type S = sig
  val maximum : int -> int -> int
  (*@ r = maximum a b
      ensures r >= a
      ensures r >= b
      ensures r = a || r = b *)

  (* `checks` is a precondition too, but a call that breaks it is not
     faulty: the function raises Invalid_argument instead. Cameleer does not
     add that exception by itself, so the `raises` clause states it.
     With `a >= 0` and `b > 0`, OCaml's `/` matches this division. *)
  val divide : int -> int -> int
  (*@ q = divide a b
      requires a >= 0
      checks b > 0
      raises Invalid_argument _ -> b <= 0
      ensures q * b <= a
      ensures a < (q + 1) * b *)
end

(* `M : S` asks Cameleer to prove that each function in M meets its
   contract in S. The header binds the names the clauses use.
   Gospel integers are Why3's mathematical integers. This contract does
   not, by itself, say anything about OCaml's wrapping overflow. *)
module M : S = struct
  let maximum a b =
    if a >= b then a else b
  (*@ r = maximum a b
      ensures r >= a
      ensures r >= b
      ensures r = a || r = b *)

  let divide a b =
    if b <= 0 then invalid_arg "divide" else a / b
  (*@ q = divide a b
      requires a >= 0
      checks b > 0
      raises Invalid_argument _ -> b <= 0
      ensures q * b <= a
      ensures a < (q + 1) * b *)
end
```
