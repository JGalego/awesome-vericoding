#!/usr/bin/env bash
# Check the Isabelle primer with Isabelle2026.
#
# The official Linux bundle (with its own Java, Poly/ML and a prebuilt HOL heap)
# is downloaded, checked against a pinned SHA-256, and unpacked under
# $PRIMER_CACHE/isabelle. The download is 1.4 GB and unpacks to 2.7 GB. Its
# Java needs the fontconfig library, which the script installs if it is missing.
#
# The file is renamed after its theory and built as a session on top of HOL
# with `isabelle build`. The check passes when the build succeeds. The session
# sets quick_and_dirty = false, so `sorry` is an error, and the script rejects
# `oops` outside comments, since Isabelle accepts it without proving anything.
set -euo pipefail

version=Isabelle2026
sha256=858c995b32216b3876bf395c3be843147d1f1eee404bc6c958d7534ee335e48d
cache="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/isabelle"
isabelle_home="$cache/$version"
# Mirrors listed on the Isabelle site, all over HTTPS. TUM's plain /dist
# redirects to HTTP, which some networks block, so use its versioned path.
mirrors=(
  "https://www.cl.cam.ac.uk/research/hvg/Isabelle/dist"
  "https://mirror.clarkson.edu/isabelle/dist"
  "https://isabelle.in.tum.de/website-$version/dist"
)

if [ ! -x "$isabelle_home/bin/isabelle" ]; then
  echo "Installing $version into $isabelle_home"
  mkdir -p "$cache"
  tmp=$(mktemp -d "$cache/tmp.XXXXXX")
  tarball="$tmp/${version}_linux.tar.gz"
  # A stalled download gives up after a minute and tries the next mirror.
  for mirror in "${mirrors[@]}"; do
    if curl -fsSL --retry 3 --connect-timeout 30 --speed-limit 50000 --speed-time 60 -o "$tarball" "$mirror/${version}_linux.tar.gz" \
      && echo "$sha256  $tarball" | sha256sum -c -; then
      break
    fi
    rm -f "$tarball"
  done
  [ -f "$tarball" ] || { echo "could not download $version" >&2; exit 1; }
  tar xzf "$tarball" -C "$tmp"
  rm -rf "$isabelle_home"
  mv "$tmp/$version" "$isabelle_home"
  rm -rf "$tmp"
fi

# Isabelle's Java stops with "Fontconfig head is null" without libfontconfig1.
if ! ldconfig -p | grep 'libfontconfig\.so\.1 ' > /dev/null; then
  echo "Installing libfontconfig1"
  sudo apt-get update -qq
  sudo apt-get install -y -qq libfontconfig1 > /dev/null
fi

file=$1
theory=$(sed -n 's/^theory[[:space:]]\{1,\}\([A-Za-z0-9_]\{1,\}\).*/\1/p' "$file" | head -n 1)
if [ -z "$theory" ]; then
  echo "no theory header in $file" >&2
  exit 1
fi

# Isabelle comments are (* ... *); drop them before looking for `oops`.
if perl -0777 -pe 's/\(\*.*?\*\)//gs' "$file" | grep -nw oops; then
  echo "the file abandons a proof with oops" >&2
  exit 1
fi

mkdir -p session
cp "$file" "session/$theory.thy"
cat > session/ROOT <<EOF
session Primer = HOL +
  options [quick_and_dirty = false, document = false, timeout = 900]
  theories $theory
EOF

# USER_HOME keeps Isabelle's settings, logs and build database out of $HOME.
mkdir -p isabelle-home
USER_HOME="$PWD/isabelle-home" "$isabelle_home/bin/isabelle" build -v -D session
