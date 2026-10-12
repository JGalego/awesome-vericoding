---
name: Dafny
filename: learndafny.dfy
contributors:
    - ["JGalego"]
title: Learn Dafny in Y Minutes
---

[Dafny](https://dafny.org) checks every function and method against its contract and will not accept a program that fails to verify. `int` is unbounded. A `function` is compiled, and anything marked `ghost` exists only for the proof. The program below passes `dafny verify` on Dafny 4.11.

```text
// A `function` is compiled. `ensures` names the function: there is no `result`.
// `int` is mathematical. Overflow is a question only for a `newtype` you declare.
function Max(a: int, b: int): int
  ensures Max(a, b) >= a && Max(a, b) >= b
  ensures Max(a, b) == a || Max(a, b) == b
{
  if a >= b then a else b
}

// `ghost` is erased. The verifier still unfolds the body, up to a fuel limit,
// which is why a later lemma has to `assert` a fact that is just the definition.
ghost function Sum(s: seq<int>): int
  decreases |s|
{
  if |s| == 0 then 0 else s[0] + Sum(s[1..])
}

// A lemma is a ghost method. The `ensures` clause is the statement.
// `decreases` is checked, not trusted: each recursive call must be smaller.
lemma SumAppend(xs: seq<int>, ys: seq<int>)
  ensures Sum(xs + ys) == Sum(xs) + Sum(ys)
  decreases |xs|
{
  if xs == [] {
    // The definition is in scope. The solver does not always unfold it.
    assert xs + ys == ys;
    assert Sum(xs) == 0;
  } else {
    SumAppend(xs[1..], ys);
    // `calc` is an equational proof. A step's hint is an assertion, not a comment.
    calc {
      Sum(xs + ys);
    ==
      xs[0] + Sum((xs + ys)[1..]);
    == { assert (xs + ys)[1..] == xs[1..] + ys; }
      xs[0] + Sum(xs[1..] + ys);
    ==
      xs[0] + Sum(xs[1..]) + Sum(ys);
    ==
      Sum(xs) + Sum(ys);
    }
  }
}

ghost predicate All(a: array<int>, v: int)
  reads a
{
  forall i :: 0 <= i < a.Length ==> a[i] == v
}

// `modifies a` is the frame. Every heap location outside it is unchanged.
// `reads` on `All` is the corresponding frame for a specification expression.
method Fill(a: array<int>, v: int)
  modifies a
  ensures All(a, v)
{
  var i := 0;
  while i < a.Length
    invariant 0 <= i <= a.Length
    invariant forall j :: 0 <= j < i ==> a[j] == v
    decreases a.Length - i
  {
    a[i] := v;
    i := i + 1;
  }
}

// The postconditions are implications. Together they do not say the result is
// the only hit, and they do not have to: this contract is existence, not uniqueness.
// The invariant is that same fact, already true outside the open interval.
method BinarySearch(a: seq<int>, key: int) returns (r: int)
  requires forall i, j :: 0 <= i < j < |a| ==> a[i] <= a[j]
  ensures 0 <= r < |a| ==> a[r] == key
  ensures r == -1 ==> forall i :: 0 <= i < |a| ==> a[i] != key
{
  var lo, hi := 0, |a|;
  while lo < hi
    invariant 0 <= lo <= hi <= |a|
    invariant forall i :: 0 <= i < lo ==> a[i] != key
    invariant forall i :: hi <= i < |a| ==> a[i] != key
    decreases hi - lo
  {
    var mid := (lo + hi) / 2;
    if a[mid] < key {
      lo := mid + 1;
    } else if key < a[mid] {
      hi := mid;
    } else {
      return mid;
    }
  }
  return -1;
}
```
