#!/usr/bin/env bash
# Verify the Viper primer with Silicon from the Viper tools of the August 2026
# release (viper-ide tag v.26.08-release, ViperServer 3.1.0).
#
# ViperToolsLinux.zip carries viperserver.jar, which includes Silicon, and the
# Z3 build Silicon is tested with (4.16.0, which needs glibc 2.38 or newer, so
# Ubuntu 24.04). Only those two files are unpacked, under $PRIMER_CACHE/viper.
# Java comes from the PATH; the runner's Java 17 is enough.
#
# Passing means Silicon exits 0 and reports that it finished successfully.
# Silicon has no "unknown" result: a solver timeout is reported as an error.
set -euo pipefail

RELEASE=v.26.08-release
CACHE="${PRIMER_CACHE:-$HOME/.cache/awesome-vericoding}/viper"
HOME_DIR="$CACHE/$RELEASE"

if [ ! -e "$HOME_DIR/.installed" ]; then
  mkdir -p "$CACHE"
  tmp=$(mktemp -d "$CACHE/tmp.XXXXXX")
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL --retry 3 -o "$tmp/ViperToolsLinux.zip" \
    "https://github.com/viperproject/viper-ide/releases/download/$RELEASE/ViperToolsLinux.zip"
  rm -rf "$HOME_DIR"
  mkdir -p "$HOME_DIR"
  unzip -q "$tmp/ViperToolsLinux.zip" backends/viperserver.jar z3/bin/z3 -d "$HOME_DIR"
  chmod +x "$HOME_DIR/z3/bin/z3"
  touch "$HOME_DIR/.installed"
fi

java -version 2>&1 | head -1
"$HOME_DIR/z3/bin/z3" --version
log=silicon.log
status=0
java -Xss128m -cp "$HOME_DIR/backends/viperserver.jar" viper.silicon.SiliconRunner \
  --logLevel ERROR --z3Exe "$HOME_DIR/z3/bin/z3" "$1" 2>&1 | tee "$log" || status=$?
[ "$status" -eq 0 ] || exit "$status"
grep -q '^Silicon finished verification successfully' "$log" || {
  echo "error: Silicon did not report success" >&2
  exit 1
}
