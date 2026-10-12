---
name: Liquid Haskell
filename: learnliquidhaskell.hs
contributors:
    - ["JGalego"]
title: Learn Liquid Haskell in Y Minutes
---

[Liquid Haskell](https://ucsd-progsys.github.io/liquidhaskell/) attaches predicates to Haskell types and checks them with an SMT solver. The compiler ignores the `{-@ @-}` comments. A measure copies a Haskell function into the refinement logic and ties its equations to the constructors of its argument, which is why the solver can use `llen` without an induction tactic.

```text
module Learn where

{-@ absolute :: x:Int -> {v:Int | v >= 0 && (v = x || v = 0 - x)} @-}
absolute :: Int -> Int
absolute x = if x >= 0 then x else 0 - x

{-@ type Nat = {v:Int | v >= 0} @-}

-- A measure is copied into the refinement logic and attached to the
-- constructors of its argument. The equation for `(:)` is then a fact
-- the solver can use without an induction tactic.
{-@ measure llen @-}
{-@ llen :: [a] -> Nat @-}
llen :: [a] -> Int
llen [] = 0
llen (_:xs) = 1 + llen xs

{-@ safeHead :: {xs:[a] | llen xs > 0} -> a @-}
safeHead :: [a] -> a
safeHead (x:_) = x
```
