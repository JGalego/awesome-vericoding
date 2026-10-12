---
name: Flux
filename: learnflux.rs
contributors:
    - ["JGalego"]
title: Learn Flux in Y Minutes
---

[Flux](https://flux-rs.github.io/flux/) refines Rust types with predicates and sends those predicates to an SMT solver. Overflow checking stays on, so a fact that is true of mathematical integers can still be rejected for an `i32`.

```text
#[flux::sig(fn(a: i32, b: i32) -> i32{v: v >= a && v >= b && (v == a || v == b)})]
fn maximum(a: i32, b: i32) -> i32 {
    if a >= b { a } else { b }
}

// `i32[x + 1]` is equality, not a lower bound.
// The refinement on `x` is what makes the addition fit.
#[flux::sig(fn(x: i32{x < 2147483647}) -> i32[x + 1])]
fn incr(x: i32) -> i32 {
    x + 1
}

#[flux::sig(fn(x: i32) -> bool[x > 0])]
fn is_positive(x: i32) -> bool {
    x > 0
}
```
