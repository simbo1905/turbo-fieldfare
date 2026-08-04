#!/usr/bin/env bash
# Install only the pinned Showboat release used by the public experiment note.
set -euo pipefail

showboat_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$showboat_script_dir/../../Package.swift" ]]; then
  showboat_root="$(cd -- "$showboat_script_dir/../.." && pwd)"
else
  showboat_root="$showboat_script_dir"
fi
showboat_bin_dir="${SHOWBOAT_BIN_DIR:-$showboat_root/.bin}"
showboat_version="v0.6.1"
showboat_asset="showboat-darwin-arm64.tar.gz"
showboat_sha256="92005313da37b534fa70845f32b544f40842f0cc909903b395bd571ccf296f74"
showboat_url="https://github.com/simonw/showboat/releases/download/${showboat_version}/${showboat_asset}"

case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) ;;
  *)
    echo "error: this installer is pinned to Darwin arm64, found $(uname -s)-$(uname -m)" >&2
    exit 2
    ;;
esac

mkdir -p "$showboat_bin_dir"
temporary_dir="$(mktemp -d)"
trap 'rm -rf "$temporary_dir"' EXIT
archive="$temporary_dir/$showboat_asset"

curl --fail --location --silent --show-error --retry 3 \
  --output "$archive" "$showboat_url"
actual_sha256="$(shasum -a 256 "$archive" | awk '{print $1}')"
if [[ "$actual_sha256" != "$showboat_sha256" ]]; then
  echo "error: Showboat archive SHA-256 mismatch" >&2
  exit 1
fi

tar -xzf "$archive" -C "$temporary_dir"
install -m 0755 "$temporary_dir/showboat" "$showboat_bin_dir/showboat"
"$showboat_bin_dir/showboat" --version
