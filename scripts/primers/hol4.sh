#!/usr/bin/env bash
# Check the HOL4 primer with HOL4 Trindemossen-2 on Poly/ML 5.9.2.
#
# There is no maintained HOL4 release image, so Poly/ML is built from its
# release source and HOL4 from its release tarball, both under
# $PRIMER_CACHE/hol4. HOL4 is built only up to bossLib (the kernel and core
# theories sequences), not the whole distribution, with at most two parallel
# jobs. The two builds take about 17 minutes the first time.
#
# The file is saved as <theory>Script.sml, after its new_theory call, and built
# with Holmake --qof, which stops at the first proof that fails. The check
# passes when Holmake builds the theory and none of the theorems it stores was
# proved with `cheat`.
set -euo pipefail

polyml_version=5.9.2
hol_version=trindemossen-2
cache="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/hol4"
poly_home="$cache/polyml-$polyml_version"
hol_home="$cache/hol-$hol_version"
jobs=2

export PATH="$poly_home/bin:$PATH"
export LD_LIBRARY_PATH="$poly_home/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p "$cache"

if [ ! -f "$poly_home/.installed" ]; then
  echo "Building Poly/ML $polyml_version into $poly_home"
  rm -rf "$poly_home"
  tmp=$(mktemp -d "$cache/tmp.XXXXXX")
  curl -fsSL --retry 3 "https://github.com/polyml/polyml/archive/refs/tags/v$polyml_version.tar.gz" \
    | tar xz -C "$tmp"
  (
    cd "$tmp/polyml-$polyml_version"
    ./configure --quiet --prefix="$poly_home"
    make -j"$jobs" > build.log 2>&1 || { tail -n 50 build.log; exit 1; }
    make install > /dev/null
  )
  rm -rf "$tmp"
  touch "$poly_home/.installed"
fi

if [ ! -f "$hol_home/.installed" ]; then
  echo "Building HOL4 $hol_version into $hol_home"
  rm -rf "$hol_home"
  mkdir -p "$hol_home"
  curl -fsSL --retry 3 \
    "https://github.com/HOL-Theorem-Prover/HOL/releases/download/$hol_version/hol-$hol_version.tar.gz" \
    | tar xz --strip-components=1 -C "$hol_home"
  (
    cd "$hol_home"
    poly < tools/smart-configure.sml
    printf '#include sequences/kernel\n#include sequences/core-theories\n' > tools/sequences/primers
    bin/build --nograph -j "$jobs" --seq=tools/sequences/primers
  )
  touch "$hol_home/.installed"
fi

file=$1
theory=$(sed -n 's/.*new_theory[[:space:]]*"\([A-Za-z0-9_]*\)".*/\1/p' "$file" | head -n 1)
if [ -z "$theory" ]; then
  echo "no new_theory call in $file" >&2
  exit 1
fi

# Holmake builds every .sml file in its directory, so build in a fresh one.
mkdir -p holmake
cp "$file" "holmake/${theory}Script.sml"
cd holmake
"$hol_home/bin/Holmake" --qof "${theory}Theory.uo"

# Holmake accepts a theorem proved with `cheat` and only marks it in the log,
# which lists every theorem the theory saved.
log=".hol/logs/${theory}Theory"
cat "$log"
if grep -E 'Saved (CHEAT|FAST-CHEAT|ORACLE thm)|\(used CHEAT\)' "$log"; then
  echo "the theory has theorems that were not proved" >&2
  exit 1
fi
