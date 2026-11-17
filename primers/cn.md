---
name: CN
filename: learncn.c
contributors:
    - ["JGalego"]
title: Learn CN in Y Minutes
---

[CN](https://github.com/rems-project/cn) checks C for undefined behavior and for specifications of ownership and functional behavior. `take` moves a resource into the function. If the postcondition does not put one back, the caller may not use the pointer.

```text
/* `*p + 1` overflows when `v` is the largest `int`, which is undefined
   behavior, so the precondition rules that value out. */
int incr(int *p)
/*@
  requires
    take v = RW(p);
    v < MAXi32();
  ensures
    take v2 = RW(p);
    v2 == v + 1;
    return == v + 1;
@*/
{
  *p = *p + 1;
  return *p;
}

/* `each` is one `RW` per index. `array_shift` is the pointer to that cell.
   `A[i]` indexes the resource CN took, which is what `return` is compared to.
   CN does not look inside an `each` by itself. `focus` takes out the `RW` for
   index `i`, which reading `p[i]` needs, and `instantiate i` is the hint at
   the same index that proving `return == A[i]` needs. */
unsigned int read_at(unsigned int *p, unsigned int n, unsigned int i)
/*@
  requires
    take A = each (integer j; 0 <= j && j < n) {
      RW<unsigned int>(array_shift<unsigned int>(p, j))
    };
    i < n;
  ensures
    take A_post = each (integer j; 0 <= j && j < n) {
      RW<unsigned int>(array_shift<unsigned int>(p, j))
    };
    A_post == A;
    return == A[i];
@*/
{
  /*@ focus RW<unsigned int>, i; @*/
  /*@ instantiate i; @*/
  return p[i];
}
```
