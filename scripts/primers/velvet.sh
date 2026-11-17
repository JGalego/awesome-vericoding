#!/usr/bin/env bash
# Check the Velvet primer with Velvet at tag v4.35.0 (commit b2a349a) on Lean 4.35.0.
#
# elan v4.2.4 is downloaded from its GitHub release and installs the toolchain
# that Velvet's lean-toolchain names, both under $PRIMER_CACHE/velvet. Velvet
# does not depend on Mathlib, so it is cloned at the pinned commit and built
# from source there once, with `lake build Velvet`. The primer is checked by
# running `lake env lean` from that checkout, which puts Velvet and its
# dependency Plausible on the search path. The file passes when `lean` exits 0
# and no declaration uses `sorry`, which Lean reports only as a warning.
set -euo pipefail

ELAN_VERSION=v4.2.4
TOOLCHAIN=leanprover/lean4:v4.35.0
VELVET_REPO=https://github.com/verse-lab/velvet.git
VELVET_COMMIT=b2a349a57021b6d4e24ab403365b404db1ce7e08

file="$1"
cache="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/velvet"
export ELAN_HOME="$cache/elan"
elan="$ELAN_HOME/bin/elan"
velvet="$cache/velvet-$VELVET_COMMIT"

if [ ! -x "$elan" ]; then
  mkdir -p "$cache"
  download=$(mktemp -d)
  curl -fsSL --retry 3 -o "$download/elan.tar.gz" \
    "https://github.com/leanprover/elan/releases/download/$ELAN_VERSION/elan-x86_64-unknown-linux-gnu.tar.gz"
  tar -xzf "$download/elan.tar.gz" -C "$download"
  "$download/elan-init" -y --no-modify-path --default-toolchain none
  rm -rf "$download"
fi
if ! "$elan" toolchain list | grep -qF "$TOOLCHAIN"; then
  "$elan" toolchain install "$TOOLCHAIN"
fi

# The marker is written only after a complete build, so an interrupted build
# is started again from a fresh clone.
if [ ! -f "$velvet/.primer-built" ]; then
  rm -rf "$velvet"
  git init -q "$velvet"
  git -C "$velvet" fetch -q --depth 1 "$VELVET_REPO" "$VELVET_COMMIT"
  git -C "$velvet" checkout -q FETCH_HEAD
  if [ "$(tr -d '[:space:]' < "$velvet/lean-toolchain")" != "$TOOLCHAIN" ]; then
    echo "error: Velvet $VELVET_COMMIT wants $(cat "$velvet/lean-toolchain"), not $TOOLCHAIN" >&2
    exit 1
  fi
  (cd "$velvet" && "$elan" run "$TOOLCHAIN" lake build Velvet)
  touch "$velvet/.primer-built"
fi

output=$(mktemp)
status=0
(cd "$velvet" && "$elan" run "$TOOLCHAIN" lake env lean "$file") 2>&1 | tee "$output" || status=$?
if grep -q "declaration uses .sorry" "$output"; then
  echo "error: a declaration uses sorry" >&2
  status=1
fi
rm -f "$output"
exit "$status"
