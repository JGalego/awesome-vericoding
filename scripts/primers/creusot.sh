#!/usr/bin/env bash
# Check the Creusot primer with Creusot v0.14.0.
#
# Creusot has no binary releases. Its INSTALL script, run from a checkout of
# the v0.14.0 tag, builds cargo-creusot and creusot-rustc on the nightly
# toolchain in the tag's rust-toolchain file (nightly-2026-08-03), builds
# Why3 and Why3find in a local opam switch (OCaml 5.3.0 from source), and
# downloads the provers it names (Alt-Ergo, Z3, CVC4, CVC5). Everything goes
# under $PRIMER_CACHE/creusot: the toolchain through a RUSTUP_HOME there, opam
# 2.6.1 (the official static binary) with an OPAMROOT there, and Creusot's own
# files through the XDG directories. opam reads a pinned snapshot of
# opam-repository. The system packages the opam build needs (autoconf, bzip2,
# patch, rsync and the GMP and zlib headers) come from apt; GitHub runners have
# most of them. After the build, the downloads, the opam sources and the
# compiler components only the build uses are deleted, which halves the cache
# to about 1.6 GB.
#
# A cold install took 47 minutes when this was written: opam cloned Why3 from
# gitlab.inria.fr twice (why3 and why3-ide share a repository), which took 22
# of them, and building OCaml, Why3 and creusot-rustc on two cores took about
# 15. A check with the cache in place takes a minute or two, most of it
# compiling creusot-std. The primer becomes src/lib.rs of a package made by
# `cargo creusot new`, and it passes when `cargo creusot` proves every goal and
# exits 0.
set -euo pipefail

VERSION=v0.14.0
TOOLCHAIN=nightly-2026-08-03-x86_64-unknown-linux-gnu
OPAM=2.6.1
OPAM_REPOSITORY=2ffc3518756432a5bea7cda8ae467ea8b4e0362a
CACHE="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/creusot"
export RUSTUP_HOME="$CACHE/rustup"
export OPAMROOT="$CACHE/opam"
export XDG_DATA_HOME="$CACHE/data"
export XDG_CONFIG_HOME="$CACHE/config"
export XDG_CACHE_HOME="$CACHE/xdg-cache"
export CARGO_INSTALL_ROOT="$CACHE"
export PATH="$CACHE/bin:$PATH"
export OPAMYES=1 OPAMJOBS="${OPAMJOBS:-4}"

if [ ! -x "$CACHE/bin/cargo-creusot" ] || [ ! -x "$XDG_DATA_HOME/creusot/bin/why3find" ]; then
    if ! dpkg -s autoconf bzip2 libgmp-dev patch pkg-config rsync zlib1g-dev >/dev/null 2>&1; then
        sudo apt-get update -q
        sudo apt-get install -y -q --no-install-recommends \
            autoconf bzip2 libgmp-dev patch pkg-config rsync zlib1g-dev
    fi

    rustup toolchain install "$TOOLCHAIN" --profile minimal --no-self-update \
        --component rustfmt,rustc-dev,llvm-tools

    mkdir -p "$CACHE/bin"
    if [ ! -x "$CACHE/bin/opam" ]; then
        curl -fsSL --retry 3 -o "$CACHE/bin/opam" \
            "https://github.com/ocaml/opam/releases/download/$OPAM/opam-$OPAM-x86_64-linux"
        chmod +x "$CACHE/bin/opam"
    fi
    if [ ! -f "$OPAMROOT/config" ]; then
        rm -rf "$OPAMROOT" opam-repository
        mkdir opam-repository
        curl -fsSL --retry 3 \
            "https://github.com/ocaml/opam-repository/archive/$OPAM_REPOSITORY.tar.gz" \
            | tar -xz --strip-components=1 -C opam-repository
        opam init --bare --no-setup --disable-sandboxing default "$PWD/opam-repository"
        # Skip why3-ide, which needs GTK, as Creusot's own CI does.
        opam var --global in-creusot-ci=true
        rm -rf opam-repository
    fi

    rm -rf creusot-src "$XDG_DATA_HOME/creusot"
    git -c advice.detachedHead=false clone -q --depth 1 --branch "$VERSION" \
        https://github.com/creusot-rs/creusot creusot-src
    (cd creusot-src && ./INSTALL)
    rm -rf creusot-src

    rm -rf "$OPAMROOT/download-cache" "$XDG_CACHE_HOME/creusot" \
        "$XDG_DATA_HOME/creusot/_opam/.opam-switch/sources"
    rustup component remove --toolchain "$TOOLCHAIN" rustfmt rustc-dev llvm-tools
fi

# The rest of the output is cvc5's licence text.
cargo creusot version | sed -n '1,7p'
cargo creusot new primer
cp "$1" primer/src/lib.rs
cd primer
cargo creusot
