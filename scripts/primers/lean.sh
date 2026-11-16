#!/usr/bin/env bash
# Check the Lean 4 primer with Lean 4.34.1.
#
# elan v4.2.4 is downloaded from its GitHub release and installs the pinned
# toolchain, both under $PRIMER_CACHE/lean. The file passes when `lean` exits
# 0 and no declaration uses `sorry`, which Lean reports only as a warning.
set -euo pipefail

ELAN_VERSION=v4.2.4
TOOLCHAIN=leanprover/lean4:v4.34.1

file="$1"
cache="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/lean"
export ELAN_HOME="$cache/elan"
elan="$ELAN_HOME/bin/elan"

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

output=$(mktemp)
status=0
"$elan" run "$TOOLCHAIN" lean "$file" 2>&1 | tee "$output" || status=$?
if grep -q "declaration uses .sorry" "$output"; then
  echo "error: a declaration uses sorry" >&2
  status=1
fi
rm -f "$output"
exit "$status"
