#!/bin/bash
# This wipes everything created by https://raw.githubusercontent.com/rook/rook/master/cluster/examples/kubernetes/ceph/import-external-cluster.sh

set -e

NAMESPACE="rook-ceph"

MON_SECRET_NAME=rook-ceph-mon
MON_ENDPOINT_CONFIGMAP_NAME=rook-ceph-mon-endpoints
CSI_RBD_NODE_SECRET_NAME=rook-csi-rbd-node
CSI_RBD_PROVISIONER_SECRET_NAME=rook-csi-rbd-provisioner
CSI_CEPHFS_NODE_SECRET_NAME=rook-csi-cephfs-node
CSI_CEPHFS_PROVISIONER_SECRET_NAME=rook-csi-cephfs-provisioner

kubectl -n ${NAMESPACE} delete secret ${MON_SECRET_NAME}
kubectl -n ${NAMESPACE} delete configmap ${MON_ENDPOINT_CONFIGMAP_NAME}
kubectl -n ${NAMESPACE} delete secret ${CSI_RBD_NODE_SECRET_NAME}
kubectl -n ${NAMESPACE} delete secret ${CSI_RBD_PROVISIONER_SECRET_NAME}
kubectl -n ${NAMESPACE} delete secret ${CSI_CEPHFS_NODE_SECRET_NAME}
kubectl -n ${NAMESPACE} delete secret ${CSI_CEPHFS_PROVISIONER_SECRET_NAME}
