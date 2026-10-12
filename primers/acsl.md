---
name: ACSL
filename: learnacsl.c
contributors:
    - ["JGalego"]
title: Learn ACSL in Y Minutes
---

ACSL is the specification language read by [Frama-C](https://frama-c.com)'s WP plugin. The annotations are comments, so a C compiler skips them and WP does not. A contract records what the caller must establish, which memory the function may assign, and what it returns.

```text
/* `assigns \nothing` is the frame: a caller keeps every fact it had about
   memory. `\valid(a + (0 .. n-1))` is the empty range when `n` is 0, which
   ACSL accepts. The "not found" result is `n`, so the result stays in `0 .. n`. */
/*@
  requires n >= 0;
  requires \valid(a + (0 .. n-1));
  assigns \nothing;
  ensures 0 <= \result <= n;
  ensures \result < n ==> a[\result] == v;
  ensures \result == n ==> \forall integer i; 0 <= i < n ==> a[i] != v;
*/
int find(int *a, int n, int v) {
  int i = 0;

  /* `loop assigns` is the frame of the body. The variant is an expression
     of type `integer` that is non-negative and decreases, which is how WP
     proves the loop ends. */
  /*@
    loop invariant 0 <= i <= n;
    loop invariant \forall integer j; 0 <= j < i ==> a[j] != v;
    loop assigns i;
    loop variant n - i;
  */
  while (i < n) {
    if (a[i] == v)
      return i;
    i++;
  }
  return i;
}
```
