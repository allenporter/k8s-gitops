#!/usr/bin/env sh
#
# The script will either update or verify the manifest file. Pass the
# argument "generate" to update the manifest file. Pass the argument "validate"
# to verify the manifest file. The default with no argument is to generate.

COMMAND=${1:-generate}

MANIFEST_FILE=kubernetes/clusters/manifest.yaml
if [ ! -f "$MANIFEST_FILE" ]; then
  echo "Manifest file not found. Please run this script from the root of the repository."
  exit 1
fi

# Validate the existing manifest and fail if there are diffs
if [ "$COMMAND" = "validate" ]; then
  flux-local get cluster -o yaml --path kubernetes/clusters/prod | diff - ${MANIFEST_FILE}
  code=$?
  if [ ${code} -ne 0 ]; then
    echo "Manifest file is not up to date. Please run 'task update-manifest' to update it."
  fi
  exit $code
fi

# Update manifest
flux-local get cluster -o yaml --path kubernetes/clusters/prod > ${MANIFEST_FILE}
