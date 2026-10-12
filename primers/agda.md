---
name: Agda
filename: learnagda.agda
contributors:
    - ["JGalego"]
title: Learn Agda in Y Minutes
---

Agda is a dependently typed language in which a proof is a total function and the type checker is the proof checker. The [Agda tour](https://learnxinyminutes.com/agda/) covers the syntax. This file is a smaller, verification-shaped slice: associativity of addition, and a lookup that typechecks only when the index is in range. It depends on no library.

```text
module Learn where

data ℕ : Set where
  zero : ℕ
  suc  : ℕ → ℕ

_+_ : ℕ → ℕ → ℕ
zero  + n = n
suc m + n = suc (m + n)

-- Propositional equality is an indexed type. `refl` exists only when the
-- two indexes are the same term.
data _≡_ {A : Set} (x : A) : A → Set where
  refl : x ≡ x

cong : ∀ {A B : Set} (f : A → B) {x y : A} → x ≡ y → f x ≡ f y
cong _ refl = refl

-- The recursive call is the induction hypothesis. Agda accepts it because
-- `m` is structurally smaller than `suc m`. There is no separate termination prover.
+-assoc : ∀ m n p → (m + n) + p ≡ m + (n + p)
+-assoc zero    _ p = refl
+-assoc (suc m) n p = cong suc (+-assoc m n p)

-- `Fin n` has exactly n values. `zero` is not a constructor at type `Fin zero`.
data Fin : ℕ → Set where
  zero : ∀ {n} → Fin (suc n)
  suc  : ∀ {n} → Fin n → Fin (suc n)

data Vec (A : Set) : ℕ → Set where
  []  : Vec A zero
  _∷_ : ∀ {n} → A → Vec A n → Vec A (suc n)

-- The missing `[]` clause is not an incomplete match. `Fin zero` has no
-- constructor, so a vector of length zero is never paired with an index.
lookup : ∀ {A n} → Vec A n → Fin n → A
lookup (x ∷ _)  zero    = x
lookup (_ ∷ xs) (suc i) = lookup xs i
```
