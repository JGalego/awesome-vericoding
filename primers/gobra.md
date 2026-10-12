---
name: Gobra
filename: learngobra.go
contributors:
    - ["JGalego"]
title: Learn Gobra in Y Minutes
---

[Gobra](https://www.pm.inf.ethz.ch/research/gobra.html) verifies Go. Specifications are `// @` comments, which the Go compiler never sees. A contract can talk about permission to a heap location as well as about the value stored there.

```text
package learn

// Negating the minimum int32 does not fit in int32.
// @ requires x != -2147483648
// @ ensures res >= 0 && (res == x || res == -x)
func Abs(x int32) (res int32) {
	if x < 0 {
		return -x
	}
	return x
}

// The for-loop initializer happens before the invariant must hold.
// At the exit, Gobra has the invariant and the negation of the guard.
// @ requires 0 <= n
// @ ensures c == n
func Count(n int) (c int) {
	c = 0
	// @ invariant 0 <= i && i <= n
	// @ invariant c == i
	// @ decreases n - i
	for i := 0; i < n; i++ {
		c = c + 1
	}
	return
}

// `acc(&s[k])` is permission for one cell. The quantifier is the slice.
// `old` is the value on entry to the function, including inside the invariant.
// @ requires forall k int :: 0 <= k && k < len(s) ==> acc(&s[k])
// @ ensures forall k int :: 0 <= k && k < len(s) ==> acc(&s[k])
// @ ensures forall k int :: 0 <= k && k < len(s) ==> s[k] == old(s[k]) + 1
func IncrAll(s []int) {
	// @ invariant 0 <= i && i <= len(s)
	// @ invariant forall k int :: 0 <= k && k < len(s) ==> acc(&s[k])
	// @ invariant forall k int :: i <= k && k < len(s) ==> s[k] == old(s[k])
	// @ invariant forall k int :: 0 <= k && k < i ==> s[k] == old(s[k]) + 1
	for i := 0; i < len(s); i++ {
		s[i] = s[i] + 1
	}
}
```
