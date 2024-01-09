#!/bin/bash
#
# Script to run `kustomize localize` on all needed kustomization.yaml files in
# the repo.

set -e

LOCALIZE_DIR="hack/localize"

rm -fr kubernetes/crds
kustomize localize ${LOCALIZE_DIR}/crds kubernetes/crds

rm -fr kubernetes/cluster_network/prod/calico
kustomize localize ${LOCALIZE_DIR}/calico/prod kubernetes/cluster_network/prod/calico

rm -fr kubernetes/monitoring/base/flux-monitoring/dashboards
kustomize localize ${LOCALIZE_DIR}/flux-monitoring kubernetes/monitoring/base/flux-monitoring/dashboards

rm -fr kubernetes/storage/prod/snapshot-controller
kustomize localize ${LOCALIZE_DIR}/snapshot-controller kubernetes/storage/prod/snapshot-controller
