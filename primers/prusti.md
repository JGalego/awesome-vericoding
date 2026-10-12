---
name: Prusti
filename: learnprusti.rs
contributors:
    - ["JGalego"]
title: Learn Prusti in Y Minutes
---

[Prusti](https://prusti.github.io/prusti/) verifies Rust by translation to Viper. Contracts are attributes. Ownership is not written out again: Prusti takes it from the borrow checker, which is the difference from a Viper program written by hand. A loop invariant is `body_invariant!`, and it has to be the first statement in the body.

```text
use prusti_contracts::*;

#[ensures(result >= a && result >= b)]
#[ensures(result == a || result == b)]
fn maximum(a: i32, b: i32) -> i32 {
    if a >= b { a } else { b }
}

#[requires(i < xs.len())]
#[ensures(result == xs[i])]
fn get(xs: &[i32], i: usize) -> i32 {
    xs[i]
}

// First statement in the body. It holds each time the guard is tested,
// so when the guard fails, `i <= n` and `!(i < n)`.
#[requires(n >= 0)]
#[ensures(result == n)]
fn count(n: i32) -> i32 {
    let mut i = 0;
    while i < n {
        body_invariant!(0 <= i && i <= n);
        i += 1;
    }
    i
}
```
