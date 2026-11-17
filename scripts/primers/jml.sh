#!/usr/bin/env bash
# Verify the JML primer with OpenJML 21.0.29 in extended static checking mode.
#
# The release zip for Ubuntu 24.04 carries its own JDK 21 and the SMT solvers
# OpenJML runs (Z3 5.1.0 by default). It is unpacked under
# $PRIMER_CACHE/jml on first use, leaving out the *.debuginfo files, which are
# more than half of the 1.3 GB it would otherwise take.
#
# javac wants a public class in a file of the same name, so the primer is
# checked as a copy named after its public class.
#
# Passing means OpenJML exits 0 and its summary counts every method as valid:
# none invalid, infeasible, timed out, failed with an error, or skipped.
set -euo pipefail

VERSION=21.0.29
CACHE="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/jml"
HOME_DIR="$CACHE/openjml-$VERSION"

if [ ! -e "$HOME_DIR/.installed" ]; then
  mkdir -p "$CACHE"
  tmp=$(mktemp -d "$CACHE/tmp.XXXXXX")
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL --retry 3 -o "$tmp/openjml.zip" \
    "https://github.com/OpenJML/OpenJML/releases/download/$VERSION/openjml-ubuntu-24.04-$VERSION.zip"
  rm -rf "$HOME_DIR"
  mkdir -p "$HOME_DIR"
  unzip -q "$tmp/openjml.zip" -x '*.debuginfo' -d "$HOME_DIR"
  touch "$HOME_DIR/.installed"
fi

class=$(sed -nE 's/^public (final |abstract )?class ([A-Za-z_][A-Za-z0-9_]*).*/\2/p' "$1" | head -1)
if [ -z "$class" ]; then
  echo "error: no public class in $1" >&2
  exit 1
fi
if [ "$(basename "$1")" != "$class.java" ]; then
  cp "$1" "$class.java"
fi

"$HOME_DIR/openjml" --version
log=openjml.log
status=0
"$HOME_DIR/openjml" --esc --progress "$class.java" 2>&1 | tee "$log" || status=$?
[ "$status" -eq 0 ] || exit "$status"

for field in Invalid Infeasible Timeout Error Skipped; do
  if ! grep -qE "^ +$field: +0$" "$log"; then
    echo "error: OpenJML did not report 0 for $field" >&2
    exit 1
  fi
done
if ! grep -qE '^ +Valid: +[1-9]' "$log"; then
  echo "error: OpenJML did not report any valid method" >&2
  exit 1
fi
