#!/usr/bin/env bash
# Check the Liquid Haskell primer with liquidhaskell 0.9.14.1.1 on GHC 9.14.1.
#
# GHC 9.14.1 (the only GHC this liquidhaskell supports) and cabal-install
# 3.16.1.0 come from their official binary distributions, and Z3 4.15.1 (the
# version Liquid Haskell's own CI uses) from its GitHub release. liquidhaskell
# is built from Hackage at a pinned index state into a cabal store and a GHC
# package environment, with libgmp-dev installed first if it is missing. All of
# it goes under $PRIMER_CACHE/liquid-haskell, separate from any ~/.ghcup or
# ~/.cabal. The first build takes about 25 minutes and leaves 1.9 GB.
#
# The module is compiled by GHC with the LiquidHaskell plugin. The check passes
# when it compiles, which the plugin allows only if every refinement type is
# verified. Totality and termination checking are on, as they are by default.
set -euo pipefail

ghc_version=9.14.1
cabal_version=3.16.1.0
z3_version=4.15.1
lh_version=0.9.14.1.1
index_state=2026-11-01T00:00:00Z
cache="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/liquid-haskell"
ghc_home="$cache/ghc-$ghc_version"
bin="$cache/bin"
env_file="$cache/liquidhaskell-$lh_version.env"
jobs=2

export PATH="$bin:$ghc_home/bin:$PATH"
export CABAL_DIR="$cache/cabal"
mkdir -p "$cache" "$bin"

if [ ! -f "$ghc_home/.installed" ]; then
  echo "Installing GHC $ghc_version into $ghc_home"
  rm -rf "$ghc_home"
  tmp=$(mktemp -d "$cache/tmp.XXXXXX")
  curl -fsSL --retry 3 \
    "https://downloads.haskell.org/~ghc/$ghc_version/ghc-$ghc_version-x86_64-ubuntu24_04-linux.tar.xz" \
    | tar xJ -C "$tmp"
  (
    cd "$tmp"/ghc-"$ghc_version"-*
    { ./configure --prefix="$ghc_home" && make install; } > install.log 2>&1 \
      || { tail -n 50 install.log; exit 1; }
  )
  rm -rf "$tmp"
  # The documentation and the profiling libraries are 2 GB that the check
  # does not use, and they would only make the cache bigger.
  rm -rf "$ghc_home/share/doc"
  find "$ghc_home" \( -name '*.p_hi' -o -name '*.p_dyn_hi' -o -name '*_p.a' \) -delete
  touch "$ghc_home/.installed"
fi

if [ ! -x "$bin/cabal" ]; then
  echo "Installing cabal-install $cabal_version into $bin"
  curl -fsSL --retry 3 \
    "https://downloads.haskell.org/~cabal/cabal-install-$cabal_version/cabal-install-$cabal_version-x86_64-linux-ubuntu24_04.tar.xz" \
    | tar xJ -C "$bin" cabal
fi

if [ ! -x "$bin/z3" ]; then
  echo "Installing Z3 $z3_version into $bin"
  tmp=$(mktemp -d "$cache/tmp.XXXXXX")
  curl -fsSL --retry 3 -o "$tmp/z3.zip" \
    "https://github.com/Z3Prover/z3/releases/download/z3-$z3_version/z3-$z3_version-x64-glibc-2.39.zip"
  unzip -q "$tmp/z3.zip" -d "$tmp"
  mv "$tmp/z3-$z3_version-x64-glibc-2.39/bin/z3" "$bin/z3"
  rm -rf "$tmp"
fi

if [ ! -f "$env_file" ]; then
  # GHC links against libgmp, and some dependencies link a Setup program while
  # they build, which needs libgmp.so from libgmp-dev.
  if ! echo 'int main(void) { return 0; }' | gcc -x c - -lgmp -o /dev/null 2> /dev/null; then
    echo "Installing libgmp-dev"
    sudo apt-get update -qq
    sudo apt-get install -y -qq libgmp-dev > /dev/null
  fi
  echo "Building liquidhaskell $lh_version into $CABAL_DIR"
  cabal update "hackage.haskell.org,$index_state"
  # The liquidhaskell package runs the plugin on its own specifications while
  # it builds, so Z3 has to be on PATH here as well.
  cabal install --lib "liquidhaskell-$lh_version" \
    --with-compiler="$ghc_home/bin/ghc" --index-state="$index_state" \
    --jobs="$jobs" --package-env="$env_file.tmp"
  mv "$env_file.tmp" "$env_file"
  # The package index and source tarballs are not needed once the store is
  # built.
  rm -rf "$CABAL_DIR/packages"
fi

file=$1
module=$(sed -n 's/^module[[:space:]]\{1,\}\([A-Za-z0-9_]\{1,\}\).*/\1/p' "$file" | head -n 1)
module=${module:-Main}
# GHC expects the file of module M to be M.hs.
mkdir -p lh
cp "$file" "lh/$module.hs"
cd lh
ghc -package-env "$env_file" -fplugin=LiquidHaskell -fforce-recomp -c "$module.hs"
