---
name: CN
filename: learncn.c
contributors:
    - ["JGalego"]
title: Learn CN in Y Minutes
---

[CN](https://github.com/rems-project/cn) checks C for undefined behavior and for specifications of ownership and functional behavior. `take` moves a resource into the function. If the postcondition does not put one back, the caller may not use the pointer.

```text
int incr(int *p)
/*@
  requires
    take v = RW(p);
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
   `A[i]` indexes the resource CN took, which is what `return` is compared to. */
unsigned int read_at(unsigned int *p, unsigned int n, unsigned int i)
/*@
  requires
    take A = each (u32 j; j < n) {
      RW<unsigned int>(array_shift<unsigned int>(p, j))
    };
    i < n;
  ensures
    take A_post = each (u32 j; j < n) {
      RW<unsigned int>(array_shift<unsigned int>(p, j))
    };
    A_post == A;
    return == A[i];
@*/
{
  return p[i];
}
```
