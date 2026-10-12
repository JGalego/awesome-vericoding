---
name: Viper
filename: learnviper.vpr
contributors:
    - ["JGalego"]
title: Learn Viper in Y Minutes
---

[Viper](https://www.pm.inf.ethz.ch/research/viper.html) is the intermediate language behind Prusti, Nagini, and Gobra. A specification talks about permission as well as truth. `acc` is permission to read and write a field, and the same full permission cannot be held twice.

```text
field val: Int

method max(a: Int, b: Int) returns (r: Int)
  ensures r >= a && r >= b
  ensures r == a || r == b
{
  if (a >= b) {
    r := a
  } else {
    r := b
  }
}

// `acc(x.val)` is permission to read and write that field.
// Two full permissions to the same location cannot both be held, so `src != dst`
// is part of the precondition, not a style constraint.
// `old` is the value at the start of the method.
method transfer(src: Ref, dst: Ref)
  requires acc(src.val) && acc(dst.val)
  requires src != dst
  ensures acc(src.val) && acc(dst.val)
  ensures dst.val == old(dst.val) + old(src.val)
  ensures src.val == 0
{
  dst.val := dst.val + src.val
  src.val := 0
}

// `exhale` asserts the permission and then drops it.
// This method verifies, and its caller may not mention `x.val` afterwards.
method forget(x: Ref)
  requires acc(x.val)
{
  exhale acc(x.val)
}
```
