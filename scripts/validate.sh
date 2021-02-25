#!/bin/bash

set -e

KUSTOMIZE_CONFIG="kustomization.yaml"
KUSTOMIZE_FLAGS=""


find . -type f -name ${KUSTOMIZE_CONFIG} -print0 | while IFS= read -r -d $'\0' file;
  do
    echo "INFO - Validating kustomization ${file}"
#    echo "INFO - Validating kustomization ${file/%$KUSTOMIZE_CONFIG}"
    kustomize build "${file/%$KUSTOMIZE_CONFIG}" ${KUSTOMIZE_FLAGS}
    if [[ ${PIPESTATUS[0]} != 0 ]]; then
      exit 1
    fi
done

