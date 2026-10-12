---
name: Nagini
filename: learnnagini.py
contributors:
    - ["JGalego"]
title: Learn Nagini in Y Minutes
---

[Nagini](https://github.com/marcoeilers/nagini) verifies Python 3 by translating it to Viper. A contract is an ordinary call, so the interpreter treats it as a no-op and Nagini does not. `MustTerminate` is the variant used to prove that a loop ends.

```text
from nagini_contracts.contracts import Requires, Ensures, Result, Invariant
from nagini_contracts.obligations import MustTerminate


def maximum(a: int, b: int) -> int:
    Ensures(Result() >= a and Result() >= b)
    Ensures(Result() == a or Result() == b)
    if a >= b:
        return a
    return b


def count(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n)
    i = 0
    while i < n:
        # `MustTerminate` is the variant. The measure has to go down each iteration.
        Invariant(0 <= i and i <= n)
        Invariant(MustTerminate(n - i))
        i = i + 1
    return i
```
