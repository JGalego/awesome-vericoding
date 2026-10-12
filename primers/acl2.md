---
name: ACL2
filename: learnacl2.lisp
contributors:
    - ["JGalego"]
title: Learn ACL2 in Y Minutes
---

[ACL2](https://www.cs.utexas.edu/~moore/acl2/) is an applicative dialect of Common Lisp with its theorem prover in the same session. A definition is admitted only after ACL2 proves that it terminates. A `defthm` with no `:hints` asks the waterfall to find the proof, including which induction to use.

```text
(in-package "ACL2")

;; `defun` is admitted only if ACL2 can prove that it terminates.
;; `endp` is the list test the prover wants: a non-cons is empty.
(defun sum (xs)
  (if (endp xs)
      0
    (+ (car xs) (sum (cdr xs)))))

(defun maximum (a b)
  (if (>= a b) a b))

;; Both theorems are stated with no `:hints`. `maximum-ge` is simplification.
;; `sum-append` is an induction the waterfall chooses from the definition of `sum`.
(defthm maximum-ge
  (and (>= (maximum a b) a)
       (>= (maximum a b) b)
       (or (equal (maximum a b) a)
           (equal (maximum a b) b))))

(defthm sum-append
  (equal (sum (append xs ys))
         (+ (sum xs) (sum ys))))
```
