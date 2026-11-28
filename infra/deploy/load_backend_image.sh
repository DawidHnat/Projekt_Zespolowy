#!/usr/bin/env bash
# Verify the CI archive and the loaded image before starting a release.
set -euo pipefail

release=${1:?Set the extracted release path}
revision=${2:?Set the full release SHA}
[[ $revision =~ ^[0-9a-f]{40}$ ]]

archive="$release/backend-image.tar.gz"
for path in "$archive" "$release/backend-image-id" "$release/backend-image.sha256"; do
  [[ -f $path && ! -L $path ]]
done

expected_archive=$(cat "$release/backend-image.sha256")
expected_image=$(cat "$release/backend-image-id")
[[ $expected_archive =~ ^[0-9a-f]{64}$ && $expected_image =~ ^sha256:[0-9a-f]{64}$ ]]
actual_archive=$(sha256sum -- "$archive")
[[ ${actual_archive%% *} == "$expected_archive" ]] || {
  printf 'Backend image archive checksum mismatch.\n' >&2
  exit 1
}

docker load --input "$archive" >/dev/null
actual_image=$(docker image inspect --format '{{.Id}}' "fleet-flow-api:$revision")
[[ $actual_image == "$expected_image" ]] || {
  printf 'Loaded backend image ID does not match the scanned image.\n' >&2
  exit 1
}
printf '%s\n' "$actual_image"
