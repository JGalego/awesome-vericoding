#!/usr/bin/env bash
# Check the ACL2 primer with ACL2 8.7 on SBCL 2.6.2.
#
# SBCL comes from its official binary release (2.6.2 was current when ACL2 8.7
# came out), and ACL2 is built from the 8.7 tag of github.com/acl2/acl2, with
# only the system sources and not the community books, which the primer does
# not use. Both go under $PRIMER_CACHE/acl2. The ACL2 build takes about four
# minutes the first time. The SBCL binary needs glibc 2.38 or newer, which
# ubuntu-latest has.
#
# The file is certified as a book with certify-book. The check passes only when
# ACL2 writes the .cert file, which it does only if every event in the book is
# admitted. A failed proof or definition stops the certification, and
# certify-book with its default options also rejects skip-proofs and defaxiom.
set -euo pipefail

acl2_version=8.7
sbcl_version=2.6.2
cache="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/acl2"
sbcl_home="$cache/sbcl-$sbcl_version"
acl2_home="$cache/acl2-$acl2_version"

mkdir -p "$cache"
if [ ! -x "$sbcl_home/bin/sbcl" ]; then
  echo "Installing SBCL $sbcl_version into $sbcl_home"
  tmp=$(mktemp -d "$cache/tmp.XXXXXX")
  curl -fsSL --retry 3 \
    "https://downloads.sourceforge.net/project/sbcl/sbcl/$sbcl_version/sbcl-$sbcl_version-x86-64-linux-binary.tar.bz2" \
    | tar xj -C "$tmp"
  (cd "$tmp/sbcl-$sbcl_version-x86-64-linux" && INSTALL_ROOT="$tmp/install" sh install.sh > /dev/null)
  rm -rf "$sbcl_home"
  mv "$tmp/install" "$sbcl_home"
  rm -rf "$tmp"
fi

if [ ! -x "$acl2_home/saved_acl2" ]; then
  echo "Building ACL2 $acl2_version into $acl2_home"
  rm -rf "$acl2_home"
  # A sparse checkout holds only the files at the top of the repository, which
  # are the ACL2 sources. The books/ directory is left out.
  git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$acl2_version" \
    --filter=tree:0 --sparse https://github.com/acl2/acl2.git "$acl2_home"
  if ! make -C "$acl2_home" LISP="$sbcl_home/bin/sbcl"; then
    tail -n 50 "$acl2_home/make.log"
    rm -f "$acl2_home/saved_acl2"
    exit 1
  fi
fi

file=$1
book=$(basename "$file" .lisp)
rm -f "$book.cert"

# ACL2_CUSTOMIZATION=NONE keeps ACL2 from loading a customization file from $HOME.
ACL2_CUSTOMIZATION=NONE "$acl2_home/saved_acl2" <<EOF
(certify-book "$book" ?)
EOF

if [ ! -f "$book.cert" ]; then
  echo "ACL2 did not certify $book.lisp" >&2
  exit 1
fi
echo "ACL2 certified $book.lisp."
