#!/bin/bash
#
# Script to run `kustomize localize` on all needed kustomization.yaml files in
# the repo.

set -e

LOCALIZE_DIR="hack/localize"

rm -fr kubernetes/crds
kustomize localize ${LOCALIZE_DIR}/crds kubernetes/crds

rm -fr kubernetes/storage/prod/snapshot-controller
kustomize localize ${LOCALIZE_DIR}/snapshot-controller kubernetes/storage/prod/snapshot-controller

rm -fr kubernetes/compute/prod/system-upgrade-controller
kustomize localize ${LOCALIZE_DIR}/system-upgrade-controller kubernetes/compute/prod/system-upgrade-controller

# rm -fr kubernetes/monitoring/base/flux-monitoring/dashboards
# kustomize localize ${LOCALIZE_DIR}/flux-monitoring kubernetes/monitoring/base/flux-monitoring/dashboards
