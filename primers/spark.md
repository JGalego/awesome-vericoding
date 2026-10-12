---
name: SPARK
filename: learnspark.ada
contributors:
    - ["JGalego"]
title: Learn SPARK in Y Minutes
---

[SPARK](https://github.com/AdaCore/spark2014) is the subset of Ada that GNATprove analyzes. A postcondition is only part of the proof: every arithmetic operation also has to be shown free of overflow. The listing is two compilation units, the package specification and the package body.

```text
-- learn.ads
package Learn with SPARK_Mode is

   function Maximum (A, B : Integer) return Integer
     with Post => Maximum'Result >= A
                  and then Maximum'Result >= B
                  and then (Maximum'Result = A or else Maximum'Result = B)
   is (if A >= B then A else B);

   -- `Natural` is `Integer` from 0 up. The postcondition is functional.
   -- The body still has to show that `Acc + 1` cannot exceed `Natural'Last`.
   procedure Count (N : Natural; C : out Natural)
     with Post => C = N;

end Learn;

-- learn.adb
package body Learn with SPARK_Mode is

   procedure Count (N : Natural; C : out Natural) is
      Acc : Natural := 0;
   begin
      for I in 1 .. N loop
         -- At the start of iteration I, Acc = I - 1. The assignment stores I.
         -- The iteration I = N is the one that stores N. I is not in scope after the loop.
         pragma Loop_Invariant (Acc = I - 1);
         Acc := Acc + 1;
      end loop;
      C := Acc;
   end Count;

end Learn;
```
