#!/usr/bin/env bash
# Verify the Gobra primer with Gobra v26.09.
#
# Gobra runs from its official Docker image, pinned by tag and digest. The
# image carries Java, Z3, and gobra.jar; Docker pulls it on first use. The
# directory is mounted read-only, since Gobra does not need to write there.
# Gobra's default settings are used, so integer overflow is not checked
# (that needs --overflow).
#
# Passing means Gobra exits 0 and reports that it found 0 errors.
set -euo pipefail

IMAGE=ghcr.io/viperproject/gobra:v26.09@sha256:5e96431b06c2e6209aa767df9153bb4cf8b2620598598f1d7d3f3a74c09c14f9

dir=$(dirname "$1")
file=$(basename "$1")
log=gobra.log
status=0
docker run --rm -v "$dir":/work:ro "$IMAGE" -i "/work/$file" 2>&1 | tee "$log" || status=$?
[ "$status" -eq 0 ] || exit "$status"
grep -q 'Gobra found 0 errors\.' "$log" || {
  echo "error: Gobra did not report a clean run" >&2
  exit 1
}
