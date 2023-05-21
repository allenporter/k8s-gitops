#!/usr/bin/env sh
set -eu

flux-local get cluster -o yaml --path clusters/ > clusters/manifest.yaml
