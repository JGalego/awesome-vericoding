#!/usr/bin/env bash
# Check the Prusti primer with Prusti v-2024-02-28-1817, the latest release
# that is not a nightly build (nightly builds are deleted after a while).
#
# The official release zip (prusti-rustc, the Viper back ends and the z3 they
# use) is unpacked under $PRIMER_CACHE/prusti. Prusti runs on the nightly
# toolchain named in the zip's rust-toolchain file, nightly-2023-09-15, which
# rustup installs into a RUSTUP_HOME in the same cache. The minimal profile is
# enough to run Prusti; rustc-dev is only needed to build it. Viper needs a
# JVM: Java 17 from $JAVA_HOME_17_X64 when that is set, as it is on GitHub's
# runners, and otherwise whatever `java` is on PATH.
#
# Overflow and panic checks are on, which is Prusti's default. The file passes
# when Prusti exits 0 and reports that every item verified.
set -euo pipefail

VERSION=v-2024-02-28-1817
TOOLCHAIN=nightly-2023-09-15-x86_64-unknown-linux-gnu
CACHE="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/prusti"
PRUSTI="$CACHE/prusti-$VERSION"
export RUSTUP_HOME="$CACHE/rustup"

if [ ! -x "$PRUSTI/prusti-rustc" ]; then
    rm -rf "$PRUSTI" "$PRUSTI.tmp"
    mkdir -p "$PRUSTI.tmp"
    curl -fsSL --retry 3 -o "$PRUSTI.tmp/prusti.zip" \
        "https://github.com/prusti/prusti/releases/download/$VERSION/prusti-release-ubuntu.zip"
    unzip -q "$PRUSTI.tmp/prusti.zip" -d "$PRUSTI.tmp"
    rm "$PRUSTI.tmp/prusti.zip"
    # The zip does not keep the executable bits.
    chmod +x "$PRUSTI.tmp"/prusti-* "$PRUSTI.tmp/cargo-prusti" "$PRUSTI.tmp/viper_tools/z3/bin/z3"
    mv "$PRUSTI.tmp" "$PRUSTI"
fi

if [ ! -x "$RUSTUP_HOME/toolchains/$TOOLCHAIN/bin/rustc" ]; then
    rustup toolchain install "$TOOLCHAIN" --profile minimal --no-self-update
fi

if [ -n "${JAVA_HOME_17_X64:-}" ]; then
    export JAVA_HOME="$JAVA_HOME_17_X64"
    export PATH="$JAVA_HOME/bin:$PATH"
fi
java -version

"$PRUSTI/prusti-rustc" --edition=2021 --crate-type=lib "$1" 2>&1 | tee prusti.log
grep -Eq '^Successful verification of [1-9][0-9]* items' prusti.log
