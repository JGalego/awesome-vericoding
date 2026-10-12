---
name: Idris 2
filename: learnidris.idr
contributors:
    - ["JGalego"]
title: Learn Idris 2 in Y Minutes
---

[Idris 2](https://www.idris-lang.org) is a dependently typed functional language. With `%default total`, a missing case or a recursion that is not on a structurally smaller argument is a type error. The length of a `Vect` is an index of the type, so an append that builds the wrong length does not typecheck.

```text
module Learn

%default total

-- `length (xs ++ ys) = length xs + length ys` is a function. `Refl` is its
-- body when both sides compute to the same term. `rewrite` substitutes the
-- recursive proof, which is the induction hypothesis.
length' : List a -> Nat
length' [] = 0
length' (_ :: xs) = S (length' xs)

lengthAppend : (xs, ys : List a) -> length' (xs ++ ys) = length' xs + length' ys
lengthAppend [] _ = Refl
lengthAppend (_ :: xs) ys = rewrite lengthAppend xs ys in Refl

-- The length is an index, not a value the function has to check.
-- `append` is only well-typed because `n + m` is the length of the result.
data Vect : Nat -> Type -> Type where
  VNil : Vect Z a
  VCons : a -> Vect n a -> Vect (S n) a

append : Vect n a -> Vect m a -> Vect (n + m) a
append VNil ys = ys
append (VCons x xs) ys = VCons x (append xs ys)
```
