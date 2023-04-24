#!/bin/bash

FLUX=flux

if [ -z "${ENV}" ]; then
  echo "Required env ENV not set"
  exit 1
fi

if [ -z "${GITHUB_USER}" ]; then
  echo "Required env GITHUB_USER not set"
  exit 1
fi

if [ -z "${GITHUB_TOKEN}" ]; then
  echo "Required env GITHUB_TOKEN not set"
  exit 1
fi

if [ -z "${GITHUB_REOP}" ]; then
  echo "Required env GITHUB_REOP not set"
  exit 1
fi

which ${FLUX}
if [ $? != 0 ]; then
  curl -s https://toolkit.fluxcd.io/install.sh | sudo bash
  . <(flux completion bash)
fi

echo
echo "Checking flux pre-reqs"
${FLUX} check --pre
if [ $? != 0 ]; then
    echo "Cluster does not satisfy pre-reqs"
    exit 1
fi

echo
echo "Flux bootstrap"
${FLUX} bootstrap github \
    --context="${ENV}-context" \
    --owner=${GITHUB_USER} \
    --repository=${GITHUB_REPO} \
    --branch=main \
    --personal \
    --private=false \
    --path=clusters/${ENV}
