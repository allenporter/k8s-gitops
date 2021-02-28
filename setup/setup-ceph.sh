#!/bin/bash
# Fetchs the external cluster configuration over ssh from a host that already
# has been bootstrapped with access.
#
# See https://rook.io/docs/rook/v1.5/ceph-cluster-crd.html#external-cluster

set -e

if [ -z $1 ]; then
  echo "Usage: $0 <ceph hostname>"
  exit 1
fi

CEPH_HOST=$1
NAMESPACE="rook-ceph"
ROOK_EXTERNAL_FSID=$(ssh ${CEPH_HOST} sudo ceph fsid)
# Pick the first monitor
ROOK_EXTERNAL_CEPH_MON_DATA=$(ssh ${CEPH_HOST} sudo ceph mon dump | egrep "^[0-9]: " | sed 's/.*v1:\(.*:6789\).*] mon.\(.*\)/\2=\1/' | tr '\n' ',' | sed 's/,$//')

SECRET=$(ssh ${CEPH_HOST} sudo ceph auth get-key client.admin)

# Based on discussion in https://github.com/rook/rook/issues/6089, instead of
# setting ROOK_EXTERNAL_ADMIN_SECRET set each part manually. For now not
# creating a separate user with just the minimum privledges given this is a
# private cluster.
ROOK_EXTERNAL_USERNAME=client.admin
ROOK_EXTERNAL_USER_SECRET=${SECRET}
CSI_RBD_NODE_SECRET_SECRET=${SECRET}
CSI_RBD_PROVISIONER_SECRET=${SECRET}
CSI_CEPHFS_NODE_SECRET=${SECRET}
CSI_CEPHFS_PROVISIONER_SECRET=${SECRET}

#ROOK_EXTERNAL_ADMIN_SECRET

echo "ROOK_EXTERNAL_FSID=${ROOK_EXTERNAL_FSID}"
echo "ROOK_EXTERNAL_CEPH_MON_DATA=${ROOK_EXTERNAL_CEPH_MON_DATA}"

source <(curl -s https://raw.githubusercontent.com/rook/rook/master/cluster/examples/kubernetes/ceph/import-external-cluster.sh)
