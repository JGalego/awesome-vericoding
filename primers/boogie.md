---
name: Boogie
filename: learnboogie.bpl
contributors:
    - ["JGalego"]
title: Learn Boogie in Y Minutes
---

[Boogie](https://github.com/boogie-org/boogie) is the intermediate language Dafny lowers to before an SMT solver sees the proof obligations. A procedure carries a contract and an imperative body. A function with no body is uninterpreted: the only facts about it are axioms, and those axioms are assumed, not proved.

```text
// A function with no body is uninterpreted. Axioms are the only meaning it has.
// They are assumed, not proved. A contradictory axiom makes later goals vacuous.
function Sum(s: [int]int, lo: int, hi: int): int;

axiom (forall s: [int]int, i: int :: Sum(s, i, i) == 0);
axiom (forall s: [int]int, lo: int, hi: int ::
  lo <= hi ==> Sum(s, lo, hi + 1) == Sum(s, lo, hi) + s[hi]);

procedure Max(a: int, b: int) returns (r: int)
  ensures r >= a && r >= b;
  ensures r == a || r == b;
{
  if (a >= b) {
    r := a;
  } else {
    r := b;
  }
}

// `b[i] := v` is the map update `b := b[i := v]`.
// The second invariant is the frame: an index the loop has not written
// still holds the input, which is what the second postcondition needs.
// `i <= j ==> b[j] == a[j]` would not cover the negative indexes.
procedure Fill(a: [int]int, n: int, v: int) returns (b: [int]int)
  requires 0 <= n;
  ensures (forall i: int :: 0 <= i && i < n ==> b[i] == v);
  ensures (forall i: int :: i < 0 || n <= i ==> b[i] == a[i]);
{
  var i: int;
  b := a;
  i := 0;
  while (i < n)
    invariant 0 <= i && i <= n;
    invariant (forall j: int :: 0 <= j && j < i ==> b[j] == v);
    invariant (forall j: int :: !(0 <= j && j < i) ==> b[j] == a[j]);
  {
    b[i] := v;
    i := i + 1;
  }
}
```
