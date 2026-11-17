#!/usr/bin/env bash
# Verify the Nagini primer with Nagini 1.3.1.
#
# Nagini is installed from PyPI into a virtual environment under
# $PRIMER_CACHE/nagini. The wheel bundles viperserver.jar (Silicon), and its
# pinned dependencies include z3-solver 4.8.7, the Z3 version Nagini asks for.
# Nagini needs Python 3.12 or newer (the runner's python3 is 3.12) and Java 11
# or newer from the PATH or JAVA_HOME.
#
# Passing means Nagini exits 0 and prints "Verification successful".
set -euo pipefail

VERSION=1.3.1
CACHE="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/nagini"
VENV="$CACHE/nagini-$VERSION"

if [ ! -e "$VENV/.installed" ]; then
  rm -rf "$VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --disable-pip-version-check "nagini==$VERSION"
  touch "$VENV/.installed"
fi

export Z3_EXE="$VENV/bin/z3"
if [ -z "${JAVA_HOME:-}" ]; then
  JAVA_HOME=$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")
  export JAVA_HOME
fi

"$VENV/bin/python" --version
log=nagini.log
status=0
"$VENV/bin/nagini" "$1" 2>&1 | tee "$log" || status=$?
[ "$status" -eq 0 ] || exit "$status"
grep -q '^Verification successful' "$log" || {
  echo "error: Nagini did not report success" >&2
  exit 1
}
