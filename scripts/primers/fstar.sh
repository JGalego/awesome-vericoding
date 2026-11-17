#!/usr/bin/env bash
# Check the F* primer with F* v2026.10.25.
#
# The official Linux release tarball from GitHub (about 240 MB) is unpacked
# under $PRIMER_CACHE/fstar. It bundles the Z3 binaries F* calls, so no other
# solver is needed.
#
# The primer passes when fstar.exe exits 0 and reports that all verification
# conditions were discharged.
set -euo pipefail

file=$1
cache=${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/fstar
version=v2026.10.25
sha256=a716153960545bc26b9d093f55614fedc716a202e4daa1665e5c63e4a2fb04e4
home="$cache/$version"

if [[ ! -e $home/installed ]]; then
  rm -rf "$cache"
  mkdir -p "$home"
  curl -fsSL --retry 3 --retry-all-errors -o "$cache/fstar.tar.gz" \
    "https://github.com/FStarLang/FStar/releases/download/$version/fstar-$version-Linux-x86_64.tar.gz"
  echo "$sha256  $cache/fstar.tar.gz" | sha256sum -c -
  tar -xzf "$cache/fstar.tar.gz" -C "$home" --strip-components=2
  rm "$cache/fstar.tar.gz"
  touch "$home/installed"
fi

"$home/bin/fstar.exe" --version
cd "$(dirname "$file")"
"$home/bin/fstar.exe" "$(basename "$file")" | tee fstar.log
grep -q 'All verification conditions discharged successfully' fstar.log
