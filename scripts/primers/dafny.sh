#!/usr/bin/env bash
# Verify the Dafny primer with Dafny 4.11.0.
#
# The release zip for Ubuntu is self-contained: it carries its own .NET runtime
# and the Z3 binaries Dafny expects, so nothing else is needed. It is unpacked
# under $PRIMER_CACHE/dafny on first use.
#
# Passing means `dafny verify` exits 0. Dafny exits non-zero on any error,
# failed proof, or timeout, and also on warnings (an `assume` without
# `{:axiom}`, for example) because --allow-warnings is not given.
set -euo pipefail

VERSION=4.11.0
CACHE="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/dafny"
HOME_DIR="$CACHE/dafny-$VERSION"

if [ ! -x "$HOME_DIR/dafny" ]; then
  mkdir -p "$CACHE"
  tmp=$(mktemp -d "$CACHE/tmp.XXXXXX")
  curl -fsSL --retry 3 -o "$tmp/dafny.zip" \
    "https://github.com/dafny-lang/dafny/releases/download/v$VERSION/dafny-$VERSION-x64-ubuntu-22.04.zip"
  unzip -q "$tmp/dafny.zip" -d "$tmp"
  rm -rf "$HOME_DIR"
  mv "$tmp/dafny" "$HOME_DIR"
  rm -rf "$tmp"
fi

"$HOME_DIR/dafny" --version
"$HOME_DIR/dafny" verify "$1"
