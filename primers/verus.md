---
name: Verus
filename: learnverus.rs
contributors:
    - ["JGalego"]
title: Learn Verus in Y Minutes
---

[Verus](https://github.com/verus-lang/verus) is an SMT-based verifier for Rust, including low-level systems code. Inside `verus!` there are three kinds of function. Executable code may call proof code, proof code may call specification code, and specification code may call neither of the other two.

```text
use vstd::prelude::*;

verus! {

// A spec function has no `requires`. Its body is the definition.
// A private spec function does not need `open` or `closed`; a `pub` one does,
// because that choice is the visibility of the body.
spec fn maximum_spec(a: int, b: int) -> int {
    if a >= b { a } else { b }
}

// The empty body is a proof. It sees `maximum_spec` because it is in the
// same module. A caller in another module would see only this `ensures`.
proof fn lemma_maximum(a: int, b: int)
    ensures
        maximum_spec(a, b) >= a && maximum_spec(a, b) >= b,
        maximum_spec(a, b) == a || maximum_spec(a, b) == b,
{
}

fn maximum(a: u64, b: u64) -> (r: u64)
    ensures
        r == maximum_spec(a as int, b as int),
{
    if a >= b { a } else { b }
}

fn count(n: u64) -> (c: u64)
    ensures
        c == n,
{
    let mut i: u64 = 0;
    while i < n
        invariant
            i <= n,
        decreases n - i,
    {
        i = i + 1;
    }
    i
}

} // verus!
```
