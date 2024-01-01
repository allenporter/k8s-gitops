#!/usr/bin/env sh
set -eu

flux-local get cluster -o yaml --path kubernetes/clusters/prod > kubernetes/clusters/manifest.yaml
