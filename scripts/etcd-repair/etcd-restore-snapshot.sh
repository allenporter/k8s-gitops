#!/bin/bash

set -e

if [ -z $2 ]; then
    echo "Usage: $0 <snapshot file> <cluster token>"
    exit 1
fi

source /etc/default/etcd

if [ -z "${ETCD_NAME}" ]; then
    echo "Unable to determine ETCD_NAME"
    exit 1
fi
if [ -z "${ETCD_INITIAL_CLUSTER}" ]; then
    echo "Unable to determine ETCD_INITIAL_CLUSTER"
    exit 1
fi
if [ -z "${ETCD_INITIAL_CLUSTER_TOKEN}" ]; then
    echo "Unable to determine ETCD_INITIAL_CLUSTER_TOKEN"
    exit 1
fi
if [ -z "${ETCD_INITIAL_ADVERTISE_PEER_URLS}" ]; then
    echo "Unable to determine ETCD_INITIAL_ADVERTISE_PEER_URLS"
    exit 1
fi

SNAPSHOT_BASENAME=$(basename $1)
TOKEN=$2
if [ ${ETCD_INITIAL_CLUSTER_TOKEN} != ${TOKEN} ]; then
  echo "Cluster token ETCD_INITIAL_CLUSTER_TOKEN=${ETCD_INITIAL_CLUSTER_TOKEN} did not match ${TOKEN}"
  exit 1
fi

export ETCD_INITIAL_CLUSTER_TOKEN="$2"
export ETCDCTL_API="3"
export ETCD_INITIAL_CLUSTER_STATE="existing"

TMP_DIR=$(mktemp -d -t etcd-XXXXXXXXXX)
RESTORE_DIR="${TMP_DIR}/restore"
ETCD_DIR="/var/lib/etcd"
ETCD_BACKUP_DIR="${ETCD_DIR}.$$"

echo "Stopping etcd"
systemctl stop etcd

SNAPSHOT_DIR="/tmp/etcd-repair"
SNAPSHOT_FILE="${SNAPSHOT_DIR}/${SNAPSHOT_BASENAME}"

echo "Restoring snapshot to ${RESTORE_DIR}"
RESTORE_NODE_DIR="${RESTORE_DIR}/${ETCD_NAME}/"
etcdctl snapshot restore ${SNAPSHOT_FILE} \
  --name ${ETCD_NAME} \
  --initial-cluster ${ETCD_INITIAL_CLUSTER} \
  --initial-cluster-token ${ETCD_INITIAL_CLUSTER_TOKEN} \
  --initial-advertise-peer-urls ${ETCD_INITIAL_ADVERTISE_PEER_URLS} \
  --data-dir ${RESTORE_DIR}

echo "Backup ${ETCD_DIR} to ${ETCD_BACKUP_DIR}"
sudo cp -rp ${ETCD_DIR} ${ETCD_BACKUP_DIR}

echo "Removing ${ETCD_DIR}"
sudo rm -fr ${ETCD_DIR}

echo "Copying ${RESTORE_DIR} to ${ETCD_DIR}"
sudo cp -r ${RESTORE_DIR} ${ETCD_DIR}

echo "Fixing permissions"
sudo chown -R etcd ${ETCD_DIR}
sudo chgrp -R etcd ${ETCD_DIR}

echo "Double check /etc/default/etcd first, then you may restart the node when ready, e.g."
echo "  systemctl start etcd"

