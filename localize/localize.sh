#!/bin/bash
#
# Script to run `kustomize localize` on all needed kustomization.yaml files in
# the repo.

set -e

rm -fr infrastructure/dev/calico
kustomize localize localize/calico/dev infrastructure/dev/calico

rm -fr infrastructure/prod/calico
kustomize localize localize/calico/prod infrastructure/prod/calico

rm -fr home/base/teslamate/dashboards
kustomize localize localize/teslamate-monitoring home/base/teslamate/dashboards

rm -fr monitoring/base/flux-monitoring/dashboards
kustomize localize localize/flux-monitoring monitoring/base/flux-monitoring/dashboards

rm -fr crds
kustomize localize localize/crds crds

rm -fr infrastructure/base/rook-ceph/snapshot-controller
kustomize localize localize/snapshot-controller infrastructure/base/rook-ceph/snapshot-controller