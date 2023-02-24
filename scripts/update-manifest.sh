#!/usr/bin/env sh
set -eu

flux-local get cluster -o yaml > clusters/manifest.yaml
