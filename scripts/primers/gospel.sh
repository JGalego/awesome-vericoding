#!/usr/bin/env bash
# Check the Gospel primer with Cameleer (commit d9899b8e, March 2026), Why3
# 1.8.2 and Alt-Ergo 2.6.4.
#
# Cameleer has no release, so it is built from that commit with opam 2.5.2
# (the static binary from the opam releases) in an OCaml 4.14.2 switch under
# $PRIMER_CACHE/gospel, from a pinned opam-repository commit, together with
# Why3 and the Gospel commit Cameleer pins. Cameleer's opam file also asks for
# why3-ide and lablgtk3, which only its interactive mode uses, so those two
# lines are dropped to avoid building GTK bindings. Alt-Ergo is the static
# binary from its GitHub release. A cold build compiles OCaml, Why3, Gospel and
# Cameleer, which takes 10 to 35 minutes depending on the machine (OPAMJOBS
# sets the parallelism, by default the number of CPUs). It needs gcc, make,
# autoconf, libgmp-dev and zlib1g-dev; missing Debian packages are installed
# with sudo apt-get. The switch holds absolute paths, so $PRIMER_CACHE must not
# move between runs.
#
# The primer passes when `cameleer --batch --prover alt-ergo`, which runs
# `why3 prove -a split_vc` through the Cameleer plugin, exits 0 and reports
# every goal as Valid. Why3 exits 2 when a goal fails; counting the results as
# well makes a run that proves no goal at all fail.
set -euo pipefail

file=$1
cache=${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/gospel
opam_version=2.5.2
opam_sha256=edfca2630c373b44b7ee1c2f81cd8dcf67468d0db57d6c02158de553ac63dbd4
opam_repository=2ffc3518756432a5bea7cda8ae467ea8b4e0362a
compiler=ocaml-base-compiler.4.14.2
why3=why3.1.8.2
gospel=c20125aeb2154b3853e0e5411c4548f568541096
cameleer=d9899b8e87680acc1611d91937c515b54ced1e0b
alt_ergo=v2.6.4
alt_ergo_sha256=80d41dd9cf4b024be7412e499f81960ddc63978f5d78a29311a05aaab125681a
version="opam $opam_version, opam-repository $opam_repository, $compiler $why3 cmdliner<2.0, gospel $gospel, cameleer $cameleer, alt-ergo $alt_ergo"

export OPAMROOT="$cache/opam" OPAMYES=1 OPAMCOLOR=never OPAMNODEPEXTS=1
export OPAMJOBS=${OPAMJOBS:-$(nproc)}
opam="$cache/bin/opam"

if [[ $(cat "$cache/installed" 2>/dev/null) != "$version" ]]; then
  rm -rf "$cache"
  mkdir -p "$cache/bin"
  missing=()
  for package in gcc make patch unzip bzip2 m4 autoconf pkg-config libgmp-dev zlib1g-dev; do
    dpkg -s "$package" >/dev/null 2>&1 || missing+=("$package")
  done
  if ((${#missing[@]})); then
    sudo apt-get update -q
    sudo apt-get install -y -q "${missing[@]}"
  fi
  curl -fsSL --retry 3 --retry-all-errors -o "$cache/bin/alt-ergo" \
    "https://github.com/OCamlPro/alt-ergo/releases/download/$alt_ergo/alt-ergo-$alt_ergo-x86_64-linux-musl"
  echo "$alt_ergo_sha256  $cache/bin/alt-ergo" | sha256sum -c -
  chmod +x "$cache/bin/alt-ergo"
  curl -fsSL --retry 3 --retry-all-errors -o "$opam" "https://github.com/ocaml/opam/releases/download/$opam_version/opam-$opam_version-x86_64-linux"
  echo "$opam_sha256  $opam" | sha256sum -c -
  chmod +x "$opam"
  mkdir "$cache/repository" "$cache/cameleer"
  curl -fsSL --retry 3 --retry-all-errors "https://github.com/ocaml/opam-repository/archive/$opam_repository.tar.gz" |
    tar -xz -C "$cache/repository" --strip-components=1
  "$opam" init --bare --no-setup --disable-sandboxing default "$cache/repository"
  rm -rf "$cache/repository"
  "$opam" switch create default "$compiler"
  curl -fsSL --retry 3 --retry-all-errors "https://github.com/ocaml-gospel/cameleer/archive/$cameleer.tar.gz" |
    tar -xz -C "$cache/cameleer" --strip-components=1
  sed -i -e '/"why3-ide"/d' -e '/lablgtk3/d' "$cache/cameleer/cameleer.opam"
  "$opam" pin add --no-action gospel.dev "git+https://github.com/ocaml-gospel/gospel.git#$gospel"
  "$opam" pin add --no-action cameleer.dev "$cache/cameleer"
  # This Gospel commit does not build against cmdliner 2.
  "$opam" install "$why3" gospel cameleer 'cmdliner<2.0'
  rm -rf "$cache/cameleer"
  "$opam" clean --all-switches --download-cache --logs --repo-cache
  echo "$version" > "$cache/installed"
fi

# Only the switch's own binaries, so a Why3 or Alt-Ergo elsewhere on PATH is not used.
export PATH="$cache/bin:$OPAMROOT/default/bin:/usr/bin:/bin"
export WHY3CONFIG="$PWD/why3.conf"
: > "$WHY3CONFIG"
why3 config detect >/dev/null
why3 --version
alt-ergo --version
cameleer --version

cd "$(dirname "$file")"
cameleer --batch --prover alt-ergo "$(basename "$file")" | tee cameleer.log
total=$(grep -c 'Prover result is:' cameleer.log || true)
valid=$(grep -c 'Prover result is: Valid' cameleer.log || true)
echo "$valid of $total goals valid"
[[ $total -gt 0 && $valid -eq $total ]]
