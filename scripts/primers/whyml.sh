#!/usr/bin/env bash
# Check the WhyML primer with Why3 1.8.2 and Alt-Ergo 2.4.3.
#
# Neither tool publishes Linux binaries, so both are built from source with
# opam 2.5.2 (the static binary from the opam releases) in an OCaml 4.14.2
# switch under $PRIMER_CACHE/whyml, from a pinned opam-repository commit.
# A cold build takes about 10 minutes and needs gcc, make, libgmp-dev and
# zlib1g-dev; missing Debian packages are installed with sudo apt-get. The
# switch holds absolute paths, so $PRIMER_CACHE must not move between runs.
#
# The primer passes when `why3 prove -P alt-ergo -a split_vc` reports every
# goal as Valid. Why3 exits 0 when a goal fails, so the script reads its output.
set -euo pipefail

file=$1
cache=${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/whyml
opam_version=2.5.2
opam_sha256=edfca2630c373b44b7ee1c2f81cd8dcf67468d0db57d6c02158de553ac63dbd4
opam_repository=2ffc3518756432a5bea7cda8ae467ea8b4e0362a
compiler=ocaml-base-compiler.4.14.2
packages=(why3.1.8.2 alt-ergo.2.4.3)
version="opam $opam_version, opam-repository $opam_repository, $compiler ${packages[*]}"

export OPAMROOT="$cache/opam" OPAMYES=1 OPAMCOLOR=never OPAMNODEPEXTS=1
export OPAMJOBS=${OPAMJOBS:-2}
opam="$cache/bin/opam"

if [[ $(cat "$cache/installed" 2>/dev/null) != "$version" ]]; then
  rm -rf "$cache"
  mkdir -p "$cache/bin"
  missing=()
  for package in gcc make patch unzip bzip2 m4 pkg-config libgmp-dev zlib1g-dev; do
    dpkg -s "$package" >/dev/null 2>&1 || missing+=("$package")
  done
  if ((${#missing[@]})); then
    sudo apt-get update -q
    sudo apt-get install -y -q "${missing[@]}"
  fi
  curl -fsSL -o "$opam" "https://github.com/ocaml/opam/releases/download/$opam_version/opam-$opam_version-x86_64-linux"
  echo "$opam_sha256  $opam" | sha256sum -c -
  chmod +x "$opam"
  mkdir "$cache/repository"
  curl -fsSL "https://github.com/ocaml/opam-repository/archive/$opam_repository.tar.gz" |
    tar -xz -C "$cache/repository" --strip-components=1
  "$opam" init --bare --no-setup --disable-sandboxing default "$cache/repository"
  rm -rf "$cache/repository"
  "$opam" switch create default "$compiler"
  "$opam" install "${packages[@]}"
  "$opam" clean --all-switches --download-cache --logs --repo-cache
  echo "$version" > "$cache/installed"
fi

# Only the switch's own binaries, so a Why3 or Alt-Ergo elsewhere on PATH is not used.
export PATH="$OPAMROOT/default/bin:/usr/bin:/bin"
export WHY3CONFIG="$PWD/why3.conf"
why3 config detect >/dev/null
why3 --version
alt-ergo --version

why3 prove -P alt-ergo -a split_vc "$file" | tee why3.log
total=$(grep -c 'Prover result is:' why3.log || true)
valid=$(grep -c 'Prover result is: Valid' why3.log || true)
echo "$valid of $total goals valid"
[[ $total -gt 0 && $valid -eq $total ]]
