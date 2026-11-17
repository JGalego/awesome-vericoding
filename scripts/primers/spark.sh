#!/usr/bin/env bash
# Check the SPARK primer with GNATprove 16.1.0.
#
# GNATprove comes from the GNAT-FSF-builds release on GitHub, the binary Alire
# installs for its gnatprove crate (about 470 MB to download), unpacked under
# $PRIMER_CACHE/spark. It bundles the Ada runtime and the provers, so no GNAT
# compiler is needed. Its binaries need glibc 2.38 or later (Ubuntu 24.04 has
# 2.39). The listing holds the spec and the body of package Learn in one file,
# which the project file names as two units of that file.
#
# The primer passes when gnatprove, with --checks-as-errors=on and
# --warnings=error, exits 0: every check and postcondition is proved and
# there are no warnings.
set -euo pipefail

file=$1
cache=${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/spark
name=gnatprove-x86_64-linux-16.1.0-1
url=https://github.com/alire-project/GNAT-FSF-builds/releases/download/gnatprove-16.1.0-1/$name.tar.gz
sha256=82528bef29857e239373fcc36732837d743f5a00805d502c70455422ffc97191
home="$cache/$name"

if [[ ! -e $home/installed ]]; then
  rm -rf "$cache"
  mkdir -p "$home"
  curl -fsSL --retry 3 --retry-all-errors -o "$cache/gnatprove.tar.gz" "$url"
  echo "$sha256  $cache/gnatprove.tar.gz" | sha256sum -c -
  tar -xzf "$cache/gnatprove.tar.gz" -C "$home" --strip-components=1
  rm "$cache/gnatprove.tar.gz"
  touch "$home/installed"
fi

export PATH="$home/bin:/usr/bin:/bin"
gnatprove --version

cd "$(dirname "$file")"
source=$(basename "$file")
cat > learn.gpr <<EOF
project Learn is
   for Source_Dirs use (".");
   for Source_Files use ("$source");
   for Object_Dir use "obj";
   package Naming is
      for Spec ("Learn") use "$source" at 1;
      for Body ("Learn") use "$source" at 2;
   end Naming;
end Learn;
EOF
gnatprove -P learn.gpr -j2 --mode=all --checks-as-errors=on --warnings=error --report=all
