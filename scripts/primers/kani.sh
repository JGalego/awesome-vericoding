#!/usr/bin/env bash
# Check the Kani primer with Kani 0.68.0.
#
# The kani-verifier crate (the `kani` and `cargo-kani` front ends) is built
# with `cargo install` into $PRIMER_CACHE/kani, and `cargo-kani setup` then
# downloads the official release bundle (kani-compiler, CBMC) into KANI_HOME
# there. The nightly toolchain the bundle names (nightly-2026-08-21) is
# installed by rustup into a RUSTUP_HOME in the same cache, so that it is
# cached with it.
#
# Function contracts are still unstable, so the file runs with
# -Z function-contracts. It passes when Kani exits 0 and every harness is
# reported as verified, with no failures.
set -euo pipefail

VERSION=0.68.0
CACHE="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/kani"

if [ ! -x "$CACHE/bin/kani" ]; then
    cargo install --locked --root "$CACHE" kani-verifier --version "$VERSION"
fi

export KANI_HOME="$CACHE/home"
export RUSTUP_HOME="$CACHE/rustup"
if [ ! -x "$KANI_HOME/kani-$VERSION/toolchain/bin/rustc" ]; then
    rm -rf "$KANI_HOME"
    # Without docs, clippy and rustfmt the toolchain is a third of the size.
    rustup set profile minimal
    "$CACHE/bin/cargo-kani" setup
fi

"$CACHE/bin/kani" --version
"$CACHE/bin/kani" -Z function-contracts "$1" 2>&1 | tee kani.log
grep -Eq '^Complete - [1-9][0-9]* successfully verified harnesses, 0 failures' kani.log
