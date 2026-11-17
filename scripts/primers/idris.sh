#!/usr/bin/env bash
# Check the Idris 2 primer with Idris 2 0.8.0.
#
# Runs the ghcr.io/joshuanianji/idris-2-docker/base image for v0.8.0, pinned by
# digest; it builds Idris 2 from the v0.8.0 tag with Chez Scheme. The file is
# passed on stdin and checked inside the container, as <Module>.idr because
# Idris wants the file name to match the module name. It is checked with
# --total; it passes when the check exits 0, the REPL's :metavars reports no
# holes, and the code does not use believe_me, assert_total, assert_smaller or
# idris_crash.
set -euo pipefail

IMAGE=ghcr.io/joshuanianji/idris-2-docker/base:v0.8.0@sha256:11b43faf3ee16c35077e318ffe9f5eab74f85b090f2a0e5193f80ac6b4b8aa8f

file="$1"
module=$(sed -n 's/^module \([A-Za-z0-9_]*\)[[:space:]]*$/\1/p' "$file" | head -n 1)
if [ -z "$module" ]; then
  echo "error: no top-level 'module <Name>' line in $file" >&2
  exit 1
fi

if grep -v '^[[:space:]]*--' "$file" | grep -wqE 'believe_me|assert_total|assert_smaller|idris_crash'; then
  echo "error: the file uses believe_me, assert_total, assert_smaller or idris_crash" >&2
  exit 1
fi

docker run --rm -i "$IMAGE" bash -euo pipefail -c '
  mkdir -p /tmp/check && cd /tmp/check && cat > "$1.idr"
  idris2 --version
  idris2 --no-color --total --check "$1.idr"
  holes=$(echo ":metavars" | idris2 --no-color --no-banner --total "$1.idr")
  echo "$holes"
  if ! echo "$holes" | grep -q "No holes"; then
    echo "error: the file has holes" >&2
    exit 1
  fi
' bash "$module" < "$file"
