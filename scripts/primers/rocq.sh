#!/usr/bin/env bash
# Check the Rocq primer with Coq 8.20.1.
#
# Runs the pinned coqorg/coq Docker image. The image runs as its own non-root
# user, which may not be able to read a bind-mounted temp dir, so the file is
# passed on stdin and compiled inside the container. `coqc` compiles it, then
# `coqchk -o` rechecks the .vo and prints a summary of what it assumes. The
# file passes when both exit 0 and every entry in that summary other than the
# theory is <none>: an `Admitted` proof or an `Axiom` is listed under axioms.
set -euo pipefail

IMAGE=coqorg/coq:8.20.1-ocaml-4.13.1-flambda

file="$1"
name=$(basename "$file" .v)

docker run --rm -i "$IMAGE" bash -euo pipefail -c '
  mkdir -p /tmp/check && cd /tmp/check && cat > "$1.v"
  coqc --version
  coqc -Q . Primer "$1.v"
  coqchk -silent -o -Q . Primer "Primer.$1" 2>&1 | tee summary
  if ! grep -q "^CONTEXT SUMMARY" summary \
     || grep "^\* " summary | grep -v "^\* Theory:" | grep -qv "<none>"; then
    echo "error: the file depends on axioms or admitted proofs" >&2
    exit 1
  fi
' bash "$name" < "$file"
