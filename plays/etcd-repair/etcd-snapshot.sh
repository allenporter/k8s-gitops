#!/bin/bash
# Take a snapshot first
# echo "Taking snapshot of ${ENDPOINT} to ${SNAPSHOT_FILE}"
# mkdir -p ${SNAPSHOT_DIR}
# etcdctl --endpoints ${ENDPOINT} snapshot save ${SNAPSHOT_FILE}

set -e

if [ -z $1 ]; then
    echo "Usage: $0 <host:2379>"
    exit 1
fi

ENDPOINT="$1"

NOW=$(date "+%s")
SNAPSHOT_DIR="${HOME}/etcd-repair"
SNAPSHOT_FILE="${SNAPSHOT_DIR}/snapshot.${NOW}.db"

echo "Creating ${SNAPSHOT_DIR}"
mkdir -p ${SNAPSHOT_DIR}

echo "Saving snapshot to ${SNAPSHOT_FILE}"
etcdctl --endpoints ${ENDPOINT} snapshot save ${SNAPSHOT_FILE}
