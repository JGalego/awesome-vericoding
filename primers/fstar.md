---
name: "F*"
filename: learnfstar.fst
contributors:
    - ["JGalego"]
title: Learn F* in Y Minutes
---

[F*](https://fstar-lang.org) is a proof-oriented dialect of ML. A refinement on an argument is a precondition, discharged at the call site. A `Lemma` is a ghost function: when its body is `()`, the SMT solver is being asked to finish the proof, and when the body recurses, that call is the induction hypothesis.

```text
module Learn

(* A `Lemma` whose body is `()` is a proof obligation for the SMT solver.
   No tactic script. If Z3 cannot see the reason, the body is where an
   assertion or a recursive call goes. *)
let maximum (a b : int) : int = if a >= b then a else b

let maximum_spec (a b : int)
  : Lemma (ensures (maximum a b >= a /\ maximum a b >= b /\
                    (maximum a b = a \/ maximum a b = b)))
  = ()

(* The refinement is the precondition. A call with `b = 0` is rejected
   at the call site, and the body may divide. *)
let divide (a : int) (b : int{b <> 0}) : int = a / b

(* `Tot` is the effect of a function that terminates and does not diverge.
   `decreases` is the measure F* checks. On an inductive type the order is
   the subterm order, so the recursive argument has to be a piece of `xs`. *)
type lst =
  | Nil
  | Cons : int -> lst -> lst

let rec sum (xs : lst) : Tot int (decreases xs) =
  match xs with
  | Nil -> 0
  | Cons x xs' -> x + sum xs'

let rec append (xs ys : lst) : Tot lst (decreases xs) =
  match xs with
  | Nil -> ys
  | Cons x xs' -> Cons x (append xs' ys)

let rec sum_append (xs ys : lst)
  : Lemma (ensures (sum (append xs ys) = sum xs + sum ys))
          (decreases xs)
  = match xs with
    | Nil -> ()
    | Cons _ xs' -> sum_append xs' ys

(* A `val` is the specification. The following `let` is accepted only if its
   inferred type matches. Callers see the `val`, not the body. *)
val absolute (x : int) : y:int{y >= 0 /\ (y = x \/ y = -x)}
let absolute x = if x < 0 then -x else x
```
