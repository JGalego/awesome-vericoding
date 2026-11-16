#!/usr/bin/env bash
# Check the Agda primer with Agda 2.9.0.
#
# The static Linux binary from the Agda GitHub release is unpacked under
# $PRIMER_CACHE/agda, which also holds the primitive modules it writes on first
# run. Agda wants the file name to match the top-level module, so the file is
# copied to <Module>.agda first. It is checked with --safe (no postulates) and
# --no-libraries; it passes when Agda exits 0, which it does not do when a hole
# or another meta is left unsolved.
set -euo pipefail

AGDA_VERSION=v2.9.0

file="$1"
cache="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/agda"
agda="$cache/$AGDA_VERSION/agda"
export XDG_DATA_HOME="$cache/data"

if [ ! -x "$agda" ]; then
  mkdir -p "$cache/$AGDA_VERSION"
  curl -fsSL --retry 3 -o "$cache/agda.tar.xz" \
    "https://github.com/agda/agda/releases/download/$AGDA_VERSION/Agda-$AGDA_VERSION-linux.tar.xz"
  tar -xJf "$cache/agda.tar.xz" -C "$cache/$AGDA_VERSION"
  rm -f "$cache/agda.tar.xz"
fi
"$agda" --version

module=$(sed -n 's/^module \([A-Za-z0-9_]*\) where.*/\1/p' "$file" | head -n 1)
if [ -z "$module" ]; then
  echo "error: no top-level 'module <Name> where' line in $file" >&2
  exit 1
fi
if [ "$(basename "$file")" != "$module.agda" ]; then
  cp "$file" "$module.agda"
fi

"$agda" --safe --no-libraries "$module.agda"
