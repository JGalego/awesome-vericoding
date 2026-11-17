#!/usr/bin/env bash
# Verify the Boogie primer with Boogie 3.5.8 and Z3 4.11.2.
#
# Boogie is installed from NuGet as a .NET tool (it targets .NET 8, which the
# runner has; DOTNET_ROLL_FORWARD lets it run on a newer runtime elsewhere).
# Z3 4.11.2 is the version Boogie's own test suite uses, fetched from the Z3
# release page. Both go under $PRIMER_CACHE/boogie on first use.
#
# Boogie exits 0 even when a proof fails, so passing is read from its summary
# line: 0 errors, with no time outs, inconclusive results, or out-of-memory
# results. A procedure marked {:verify false} is skipped without a word, so the
# file must not contain one.
set -euo pipefail

VERSION=3.5.8
Z3_VERSION=4.11.2
CACHE="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/boogie"
TOOL_DIR="$CACHE/boogie-$VERSION"
Z3_DIR="$CACHE/z3-$Z3_VERSION"

export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_ROLL_FORWARD=Major

if [ ! -e "$TOOL_DIR/.installed" ]; then
  rm -rf "$TOOL_DIR"
  dotnet tool install Boogie --version "$VERSION" --tool-path "$TOOL_DIR"
  touch "$TOOL_DIR/.installed"
fi

if [ ! -x "$Z3_DIR/bin/z3" ]; then
  mkdir -p "$CACHE"
  tmp=$(mktemp -d "$CACHE/tmp.XXXXXX")
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL --retry 3 -o "$tmp/z3.zip" \
    "https://github.com/Z3Prover/z3/releases/download/z3-$Z3_VERSION/z3-$Z3_VERSION-x64-glibc-2.31.zip"
  unzip -q "$tmp/z3.zip" -d "$tmp"
  rm -rf "$Z3_DIR"
  mv "$tmp/z3-$Z3_VERSION-x64-glibc-2.31" "$Z3_DIR"
fi

if grep -n '{:verify false}' "$1"; then
  echo "error: the file turns verification off for part of itself" >&2
  exit 1
fi

"$Z3_DIR/bin/z3" --version
log=boogie.log
status=0
"$TOOL_DIR/boogie" /proverOpt:PROVER_PATH="$Z3_DIR/bin/z3" "$1" 2>&1 | tee "$log" || status=$?
[ "$status" -eq 0 ] || exit "$status"

# The summary looks like "Boogie program verifier finished with 2 verified, 0 errors".
# Time outs, inconclusive results, and out-of-memory results are appended to it.
summary=$(grep -E '^Boogie program verifier finished with' "$log" || true)
if [ -z "$summary" ] || ! grep -qE ', 0 errors$' <<<"$summary"; then
  echo "error: Boogie did not report a clean run" >&2
  exit 1
fi
