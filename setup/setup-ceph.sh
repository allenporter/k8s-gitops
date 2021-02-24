#!/bin/bash
# Fetches the ceph-admin-secret from the cluster over ssh.

set -e

NAMESPACE="storage"
SECRET_NAME="ceph-admin-secret"
SECRET_TYPE="kubernetes.io/rbd"

if [ -z $1 ]; then
  echo "Usage: $0 <ceph hostname>"
  exit 1
fi

CEPH_HOST=$1
SECRET_DATA=$(ssh ${CEPH_HOST} sudo ceph auth get-key client.admin)

kubectl create secret generic ${SECRET_NAME} --from-literal=key="${SECRET_DATA}" --type="${SECRET_TYPE}" --namespace=${NAMESPACE}

kubectl get secrets ${SECRET_NAME} --namespace=${NAMESPACE}
