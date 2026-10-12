---
name: JML
filename: learnjml.java
contributors:
    - ["JGalego"]
title: Learn JML in Y Minutes
---

JML is the annotation language read by [OpenJML](https://www.openjml.org) and [KeY](https://www.key-project.org). The annotations are comments, and `\result` names the value returned. Arithmetic in a specification is mathematical even when the corresponding Java expression is a 32-bit `int`, which is why a true specification can still sit on top of an overflowing body.

```text
public class Learn {

    /*@ ensures \result >= a && \result >= b;
      @ ensures \result == a || \result == b;
      @*/
    public static /*@ pure @*/ int maximum(int a, int b) {
        if (a >= b) {
            return a;
        } else {
            return b;
        }
    }

    /* `n <= 46340` is a bound under which `n * (n + 1)` fits in a Java `int`.
       JML arithmetic is mathematical, so the precondition is what keeps the
       body inside that range. */
    /*@ requires 0 <= n && n <= 46340;
      @ ensures \result == n * (n + 1) / 2;
      @*/
    public static int sumTo(int n) {
        int i = 0;
        int s = 0;
        /*@ loop_invariant 0 <= i && i <= n;
          @ loop_invariant s == i * (i + 1) / 2;
          @ decreases n - i;
          @*/
        while (i < n) {
            i = i + 1;
            s = s + i;
        }
        return s;
    }
}
```
