---
name: Kani
filename: learnkani.rs
contributors:
    - ["JGalego"]
title: Learn Kani in Y Minutes
---

[Kani](https://model-checking.github.io/kani) is a bit-precise model checker for Rust, built on CBMC. A proof is a harness. `kani::any` is an arbitrary value of its type, bounded by that type, and `kani::assert` is the claim. `proof_for_contract` checks a function's `requires` and `ensures` without a second copy of them in the harness.

```text
// `kani::any` is an arbitrary value of the type. The proof is bounded by that
// type: every `u32` is included, and nothing else is.
#[kani::proof]
fn maximum_is_one_of_them() {
    let a: u32 = kani::any();
    let b: u32 = kani::any();
    let r = if a >= b { a } else { b };
    kani::assert(r == a || r == b, "maximum returns an argument");
}

#[kani::requires(b != 0)]
#[kani::ensures(|result: &u32| *result <= a)]
fn div(a: u32, b: u32) -> u32 {
    a / b
}

// `proof_for_contract` builds the harness. Kani assumes `requires` and
// asserts `ensures`. Writing those again here would be a second copy.
#[kani::proof_for_contract(div)]
fn div_contract() {
    div(kani::any(), kani::any());
}
```
