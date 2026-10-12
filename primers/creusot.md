---
name: Creusot
filename: learncreusot.rs
contributors:
    - ["JGalego"]
title: Learn Creusot in Y Minutes
---

[Creusot](https://creusot.rs) verifies Rust by translating Pearlite contracts into WhyML. A function marked `#[logic]` is not Rust that runs. It is a definition in the specification logic, and `@` is the view of a Rust value in that logic.

```text
use creusot_contracts::prelude::*;

#[logic]
fn maximum_logic(a: Int, b: Int) -> Int {
    if a >= b { a } else { b }
}

#[ensures(result@ == maximum_logic(a@, b@))]
pub fn maximum(a: i32, b: i32) -> i32 {
    if a >= b { a } else { b }
}

#[logic]
fn all_equal(s: Seq<i32>, v: Int) -> bool {
    pearlite! {
        forall<i: Int> 0 <= i && i < s.len() ==> s[i]@ == v
    }
}

#[ensures(all_equal(result@, 1))]
#[ensures(result@.len() == n@)]
pub fn ones(n: usize) -> Vec<i32> {
    creusot_std::vec![1; n]
}
```
