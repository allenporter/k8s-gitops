#!/usr/bin/env sh
set -eu

MANIFEST_FILE=kubernetes/clusters/manifest.yaml

md5sum_before=$(md5sum ${MANIFEST_FILE}| awk '{print $1}')

# Update manifest
flux-local get cluster -o yaml --path kubernetes/clusters/prod > ${MANIFEST_FILE}

md5sum_after=$(md5sum ${MANIFEST_FILE} | awk '{print $1}')

# Fail if the manifest was updated
if [ "$md5sum_before" != "$md5sum_after" ]; then
  echo "Manifest was updated. Please commit the changes."
  exit 1
fi
