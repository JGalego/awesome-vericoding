#!/usr/bin/env bash
# Check the PVS primer with PVS 8.1.3.
#
# PVS is installed from SRI's release tarball on GitHub (the SBCL build, which
# runs without Emacs) under $PRIMER_CACHE/pvs. The file goes through ProofLite's
# proveit, which ships with PVS: it typechecks the file, generates the
# type-correctness conditions (TCCs), and runs every proof it has.
#
# The primer keeps its proofs out of the file, the way a PVS project keeps them
# in a separate .prf file, so a LEMMA with no proof is reported as untried and
# does not fail the check. The check passes when the file parses and typechecks
# and every TCC, including the termination obligations, is proved by PVS's
# default TCC strategy. Any other unproved formula fails it.
set -euo pipefail

version=8.1.3
tarball=pvs8.1.3-20261028-linux-x86_64.tgz
cache="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/pvs"
pvs="$cache/pvs-$version"

if [ ! -x "$pvs/proveit" ]; then
  echo "Installing PVS $version into $pvs"
  mkdir -p "$cache"
  tmp=$(mktemp -d "$cache/tmp.XXXXXX")
  curl -fsSL --retry 3 "https://github.com/SRI-CSL/PVS/releases/download/pvs$version/$tarball" \
    | tar xz -C "$tmp"
  rm -rf "$pvs"
  mv "$tmp/pvs-8.1" "$pvs"
  rm -rf "$tmp"
fi

file=$1
name=$(basename "$file" .pvs)

# PVS writes a log under $HOME and reads ~/.pvs.lisp, so give it its own home.
mkdir -p pvs-home
status=0
HOME="$PWD/pvs-home" "$pvs/proveit" --clean --force --log "$file" || status=$?
echo "--- $name.log"
cat "$name.log" 2>/dev/null || true

# proveit exits 0 when every formula is proved, 142 when some are not, and
# anything else when the file does not parse or typecheck.
if [ "$status" -ne 0 ] && [ "$status" -ne 142 ]; then
  echo "proveit failed with exit code $status" >&2
  exit 1
fi
if [ ! -f "$name.summary" ]; then
  echo "proveit wrote no $name.summary" >&2
  exit 1
fi

# Summary lines look like "    sum_TCC1.........proved - complete   [shostak](0.00 s)".
formulas=$(sed -n 's/^ *\([A-Za-z0-9_?]*\)\.\.*\([a-z].*[a-z]\) *\[.*$/\1 \2/p' "$name.summary")
if [ -z "$formulas" ]; then
  echo "no formulas found in $name.summary" >&2
  exit 1
fi
failed=0
untried=()
while read -r formula state; do
  case "$state" in
    "proved - complete") ;;
    untried)
      if [[ "$formula" == *_TCC* ]]; then
        echo "TCC $formula was not tried" >&2
        failed=1
      else
        untried+=("$formula")
      fi
      ;;
    *)
      echo "$formula: $state" >&2
      failed=1
      ;;
  esac
done <<< "$formulas"

if [ "${#untried[@]}" -gt 0 ]; then
  echo "No proof in the file, not checked: ${untried[*]}"
fi
if [ "$failed" -ne 0 ]; then
  exit 1
fi
echo "PVS typechecked $name.pvs and proved all its TCCs."
