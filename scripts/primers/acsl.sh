#!/usr/bin/env bash
# Check the ACSL primer with Frama-C 32.1 (Germanium) and its WP plugin.
#
# Frama-C runs from the official framac/frama-c:32.1 Docker image, which
# bundles the provers WP uses. Nothing is installed under $PRIMER_CACHE; the
# image is about 2 GB to pull.
#
# The primer passes when WP, with -wp-rte so that the absence of runtime errors
# is proved as well, reports every goal as proved. Frama-C exits 0 when a goal
# fails, so the script reads the "Proved goals" summary.
set -euo pipefail

file=$1
image=framac/frama-c:32.1

# The image's entry point is `opam exec`, which only works as the image's own
# user. The container runs as the caller instead, so that it can read the
# directory it is given, and calls Frama-C from the opam switch directly. HOME
# stays /home/opam, where the image keeps its Why3 prover configuration.
switch=/home/opam/.opam/4.14
cd "$(dirname "$file")"
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/home/opam -e PATH="$switch/bin:/usr/bin:/bin" \
  -v "$PWD":/work -w /work --entrypoint "$switch/bin/frama-c" "$image" \
  -wp -wp-rte -wp-timeout 30 "$(basename "$file")" | tee frama-c.log

summary=$(grep -E '^\[wp\] Proved goals: +[0-9]+ / [0-9]+' frama-c.log || true)
[[ -n $summary ]] || { echo "no WP summary in the output"; exit 1; }
read -r proved total < <(sed -E 's/.*: +([0-9]+) \/ ([0-9]+).*/\1 \2/' <<<"$summary")
[[ $total -gt 0 && $proved -eq $total ]]
