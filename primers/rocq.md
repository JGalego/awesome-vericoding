---
name: Rocq
filename: learnrocq.v
contributors:
    - ["JGalego"]
title: Learn Rocq in Y Minutes
---

Rocq, the proof assistant formerly called Coq, checks Gallina programs together with proofs about them. The [Coq tour](https://learnxinyminutes.com/coq/) is a programming introduction. This file builds the datatypes it needs and proves a specification for them. `coqc` accepts it on Coq 8.20, and it does not depend on whether the standard library is named `Coq` or `Stdlib`.

```text
(* A self-contained development. `nat` and `list` here are ours, not the
   standard library's, so the file does not care whether the prelude is
   `Coq` or `Stdlib`. *)

Inductive nat : Type :=
  | O
  | S (n : nat).

Fixpoint plus (m n : nat) : nat :=
  match m with
  | O => n
  | S m' => S (plus m' n)
  end.

Notation "m + n" := (plus m n).

Inductive list (A : Type) : Type :=
  | nil
  | cons (x : A) (xs : list A).

Arguments nil {A}.
Arguments cons {A}.

Notation "x :: xs" := (cons x xs).
Notation "[ ]" := nil.

Fixpoint app {A : Type} (xs ys : list A) : list A :=
  match xs with
  | nil => ys
  | cons x xs' => cons x (app xs' ys)
  end.

Notation "xs ++ ys" := (app xs ys).

Fixpoint sum (xs : list nat) : nat :=
  match xs with
  | nil => O
  | cons x xs' => plus x (sum xs')
  end.

(* `reflexivity` closes a goal that computes to the same term on both sides.
   `induction` does not: it replaces the goal with one case per constructor,
   and only the recursive case receives an induction hypothesis. *)
Lemma plus_n_O : forall n, n + O = n.
Proof.
  induction n as [|n IH]; simpl.
  - reflexivity.
  - rewrite IH. reflexivity.
Qed.

Lemma plus_assoc : forall a b c, (a + b) + c = a + (b + c).
Proof.
  induction a as [|a IH]; intros b c; simpl.
  - reflexivity.
  - rewrite IH. reflexivity.
Qed.

(* `simpl` exposes `x + ...`. Associativity is not definitional, so the
   rewrite of the induction hypothesis leaves a goal that still needs it. *)
Lemma sum_app : forall xs ys, sum (xs ++ ys) = sum xs + sum ys.
Proof.
  induction xs as [|x xs IH]; intros ys; simpl.
  - reflexivity.
  - rewrite IH. rewrite plus_assoc. reflexivity.
Qed.

Lemma sum_app_nil : forall xs, sum (xs ++ []) = sum xs.
Proof.
  intros xs. rewrite sum_app. simpl. rewrite plus_n_O. reflexivity.
Qed.

(* `le` is a `Prop`: a proof of it is erased, and you do not pattern-match on
   it from a program. `nat` is a `Type`: its constructors are data. *)
Inductive le : nat -> nat -> Prop :=
  | le_n : forall n, le n n
  | le_S : forall m n, le m n -> le m (S n).

Lemma le_O : forall n, le O n.
Proof.
  induction n as [|n IH].
  - apply le_n.
  - apply le_S. exact IH.
Qed.
```
