#!/bin/bash
#
# Script to run `kustomize localize` on all needed kustomization.yaml files in
# the repo.

set -e

LOCALIZE_DIR="hack/localize"

rm -fr crds
kustomize localize ${LOCALIZE_DIR}/crds crds

rm -fr infrastructure/prod/calico
kustomize localize ${LOCALIZE_DIR}/calico/prod infrastructure/prod/calico

rm -fr monitoring/base/flux-monitoring/dashboards
kustomize localize ${LOCALIZE_DIR}/flux-monitoring monitoring/base/flux-monitoring/dashboards

rm -fr infrastructure/base/rook-ceph/snapshot-controller
kustomize localize ${LOCALIZE_DIR}/snapshot-controller infrastructure/base/rook-ceph/snapshot-controller

rm -fr home/base/teslamate/dashboards
kustomize localize ${LOCALIZE_DIR}/teslamate-monitoring home/base/teslamate/dashboards
