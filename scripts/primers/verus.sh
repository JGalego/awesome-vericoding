#!/usr/bin/env bash
# Check the Verus primer with Verus 0.2026.11.02.8bf68ee.
#
# The official release zip (the verus driver, vstd and the z3 it ships with)
# is unpacked under $PRIMER_CACHE/verus. Verus runs on a fixed Rust toolchain,
# 1.99.1 for this release, which rustup installs into a RUSTUP_HOME in the
# same cache so that it is cached with it.
#
# The file is verified as a library crate with --no-cheating, which rejects
# assume, admit, external_body and options that skip checks. It passes when
# Verus exits 0 and reports no errors.
set -euo pipefail

VERSION=0.2026.11.02.8bf68ee
TOOLCHAIN=1.99.1-x86_64-unknown-linux-gnu
CACHE="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/verus"
VERUS="$CACHE/verus-$VERSION"
export RUSTUP_HOME="$CACHE/rustup"

if [ ! -x "$VERUS/verus" ]; then
    rm -rf "$VERUS" "$VERUS.tmp"
    mkdir -p "$VERUS.tmp"
    curl -fsSL --retry 3 -o "$VERUS.tmp/verus.zip" \
        "https://github.com/verus-lang/verus/releases/download/release/$VERSION/verus-$VERSION-x86-linux.zip"
    unzip -q "$VERUS.tmp/verus.zip" -d "$VERUS.tmp"
    mv "$VERUS.tmp/verus-x86-linux" "$VERUS"
    rm -rf "$VERUS.tmp"
fi

if [ ! -x "$RUSTUP_HOME/toolchains/$TOOLCHAIN/bin/rustc" ]; then
    rustup toolchain install "$TOOLCHAIN" --profile minimal --no-self-update
fi

"$VERUS/verus" --version
"$VERUS/verus" --crate-type=lib --no-cheating "$1" 2>&1 | tee verus.log
grep -Eq '^verification results:: [1-9][0-9]* verified, 0 errors' verus.log
