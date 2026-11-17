#!/usr/bin/env bash
# Verify the Stainless primer with Stainless 0.10.4.
#
# The standalone release zip for Linux carries the Stainless jar, the Scala 3
# front end, and the Z3 and cvc5 binaries it calls; it is unpacked under
# $PRIMER_CACHE/stainless on first use. Stainless wants Java 17 from the PATH,
# which is the runner's default. The bundled Z3 needs glibc 2.38 or newer.
#
# Passing means Stainless exits 0 and its summary counts no invalid and no
# unknown verification conditions. The bundled Z3 binary is the solver, each
# proof attempt gets 30 seconds (as in the stainless.conf shipped with the
# release), no configuration file is read, and the VC cache is off so that
# every condition is proved on this run.
set -euo pipefail

VERSION=0.10.4
CACHE="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/stainless"
HOME_DIR="$CACHE/stainless-$VERSION"

if [ ! -e "$HOME_DIR/.installed" ]; then
  mkdir -p "$CACHE"
  tmp=$(mktemp -d "$CACHE/tmp.XXXXXX")
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL --retry 3 -o "$tmp/stainless.zip" \
    "https://github.com/epfl-lara/stainless/releases/download/v$VERSION/stainless-dotty-standalone-$VERSION-linux.zip"
  rm -rf "$HOME_DIR"
  mkdir -p "$HOME_DIR"
  unzip -q "$tmp/stainless.zip" -d "$HOME_DIR"
  touch "$HOME_DIR/.installed"
fi

# The Stainless jar has class files with non-ASCII names, which the Scala
# compiler cannot open under the POSIX locale.
export LC_ALL=C.UTF-8

java -version 2>&1 | head -1
log=stainless.log
status=0
"$HOME_DIR/stainless" --config-file=false --no-colors --solvers=smt-z3 --timeout=30 \
  --vc-cache=false "$1" 2>&1 | tee "$log" || status=$?
[ "$status" -eq 0 ] || exit "$status"
grep -qE 'invalid: 0 +unknown: 0' "$log" || {
  echo "error: Stainless did not report every verification condition as valid" >&2
  exit 1
}
