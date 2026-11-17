#!/usr/bin/env bash
# Check the Flux primer with Flux at commit ef6af17f647c (2026-11-04).
#
# Flux has no releases, so the pinned commit is built from source with
# `cargo xtask install`, as its install guide says. That puts `flux` under
# $PRIMER_CACHE/flux/bin and the Flux sysroot (flux-driver and its libraries)
# under FLUX_HOME there. The build uses the nightly toolchain in the commit's
# rust-toolchain.toml, nightly-2026-10-22, which rustup installs into a
# RUSTUP_HOME in the same cache; the components only the build needs are
# removed afterwards, which takes the toolchain from 1.6 GB to 0.6 GB. Flux
# also needs liquid-fixpoint and z3 on PATH: fixpoint from the dated
# nightly-2026-10-14 release of liquid-fixpoint, and z3 4.15.3, the version
# Flux's own CI uses.
#
# A cold install, mostly the build, takes about seven minutes on two cores.
# The file is checked as a library crate. It passes when Flux exits 0 and its
# summary shows every function checked, none trusted and none ignored.
set -euo pipefail

COMMIT=ef6af17f647cf98c860e18e90c36d1f1b69849ff
TOOLCHAIN=nightly-2026-10-22-x86_64-unknown-linux-gnu
FIXPOINT=nightly-2026-10-14
Z3=4.15.3
CACHE="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/flux"
export RUSTUP_HOME="$CACHE/rustup"
export FLUX_HOME="$CACHE/home"
export PATH="$CACHE/bin:$PATH"
mkdir -p "$CACHE/bin"

if [ ! -x "$CACHE/bin/z3" ]; then
    curl -fsSL --retry 3 -o z3.zip \
        "https://github.com/Z3Prover/z3/releases/download/z3-$Z3/z3-$Z3-x64-glibc-2.39.zip"
    unzip -q -j z3.zip "z3-$Z3-x64-glibc-2.39/bin/z3" -d "$CACHE/bin"
    rm z3.zip
fi

if [ ! -x "$CACHE/bin/fixpoint" ]; then
    curl -fsSL --retry 3 \
        "https://github.com/ucsd-progsys/liquid-fixpoint/releases/download/$FIXPOINT/fixpoint-x86_64-linux-gnu.tar.gz" \
        | tar -xz -C "$CACHE/bin" fixpoint
    chmod +x "$CACHE/bin/fixpoint"
fi

if [ ! -x "$CACHE/bin/flux" ] || [ ! -x "$FLUX_HOME/sysroot/flux-driver" ]; then
    rustup toolchain install "$TOOLCHAIN" --profile minimal --no-self-update \
        --component rust-src,rustc-dev,llvm-tools,rustfmt,clippy
    rm -rf flux-src "$FLUX_HOME"
    git init -q flux-src
    git -C flux-src fetch -q --depth 1 https://github.com/flux-rs/flux "$COMMIT"
    git -C flux-src checkout -q FETCH_HEAD
    (cd flux-src && CARGO_INSTALL_ROOT="$CACHE" cargo xtask install)
    rm -rf flux-src
    # Running Flux needs only rustc and the standard library.
    rustup component remove --toolchain "$TOOLCHAIN" rust-src rustc-dev llvm-tools rustfmt clippy
fi

z3 --version
echo "fixpoint $(fixpoint --numeric-version)"
flux --version
flux --crate-type=lib "$1" 2>&1 | tee flux.log
sed 's/\x1b\[[0-9;]*m//g' flux.log \
    | grep -Eq '^summary\. ([0-9]+) functions processed: \1 checked; 0 trusted; 0 ignored\.'
