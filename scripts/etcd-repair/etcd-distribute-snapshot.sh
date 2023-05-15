#!/bin/bash

set -e

if [ -z $2 ]; then
    echo "Usage: repair.sh <snapshot file> <host>"
    exit 1
fi

SNAPSHOT_FILE=$1
ETCD_HOST=$2
SNAPSHOT_BASENAME=$(basename ${SNAPSHOT_FILE})
SNAPSHOT_DIR="/tmp/etcd-repair"
SNAPSHOT_OUT="${SNAPSHOT_DIR}/${SNAPSHOT_BASENAME}"

echo "Copying $SNAPSHOT_FILE to ${ETCD_HOST}:${SNAPSHOT_OUT}"
ssh ${ETCD_HOST} "mkdir -p ${SNAPSHOT_DIR}"
scp ${SNAPSHOT_FILE} "${ETCD_HOST}:${SNAPSHOT_OUT}"

SCRIPT="etcd-restore-snapshot.sh"

echo "Copying ${SCRIPT} to server"
scp ${SCRIPT} "${ETCD_HOST}:${SCRIPT}"

echo "Run command to restore:"
echo "  ssh ${ETCD_HOST} sudo ./${SCRIPT} ${SNAPSHOT_BASENAME} <token>"

