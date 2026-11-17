#!/usr/bin/env bash
# Check the CN primer with CN from the rems-project/cn image built on
# 23 October 2026.
#
# CN runs from the official ghcr.io/rems-project/cn:release-ubuntu image, which
# bundles Z3. The project publishes only moving tags, so the image is pinned by
# digest. Nothing is installed under $PRIMER_CACHE; the image is about 1.3 GB
# to pull.
#
# The primer passes when `cn verify` exits 0, which it does only when every
# function in the file verifies.
set -euo pipefail

file=$1
image=ghcr.io/rems-project/cn@sha256:1372d74bb5232b5c5186d3d3e0853dbd902ba2bd9be1ef4d7bb85131a72c7fb5

# CN is installed in root's opam switch under /root, which no other user can
# enter, so the container runs as root. The directory is mounted read-only, so
# nothing in it ends up owned by root.
cd "$(dirname "$file")"
docker run --rm -e OPAMROOTISOK=1 -v "$PWD":/work:ro -w /work "$image" \
  cn verify "$(basename "$file")"
