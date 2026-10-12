---
name: Stainless
filename: learnstainless.scala
contributors:
    - ["JGalego"]
title: Learn Stainless in Y Minutes
---

[Stainless](https://epfl-lara.github.io/stainless/) verifies a functional subset of Scala. `ensuring` is ordinary Scala. Stainless tries to prove the predicate, and when it cannot, it can return a counterexample instead of an unfinished goal.

```text
import stainless.collection._
import stainless.lang._

object Learn {

  def maximum(x: BigInt, y: BigInt): BigInt = {
    if x >= y then x else y
  }.ensuring(res =>
    x <= res && y <= res && (res == x || res == y)
  )

  def sum(xs: List[BigInt]): BigInt = xs match {
    case Nil() => BigInt(0)
    case Cons(h, t) => h + sum(t)
  }

  // The recursive call is the induction step. Stainless checks that `t` is
  // smaller than `xs`, and that the postcondition holds in both cases.
  def sumAppend(xs: List[BigInt], ys: List[BigInt]): Unit = {
    xs match {
      case Nil() => ()
      case Cons(_, t) => sumAppend(t, ys)
    }
  }.ensuring(_ => sum(xs ++ ys) == sum(xs) + sum(ys))
}
```

`BigInt` is the integer Stainless does not overflow-check. A Scala `Int` in the same place would add a verification condition for every arithmetic operation.
