#!/bin/bash
# Generates a key for use with git (e.g. vscode)

set -e

if [ -z $2 ]; then
  echo "Usage: $0 <secret-name> <namespace>"
  exit 1
fi

SECRET_NAME=$1
NAMESPACE=$2

TMP_DIR=$(mktemp -d)
KEY_FILE=${TMP_DIR}/${SECRET_NAME}

echo "Generating ${KEY_FILE}"
ssh-keygen -t rsa -b 4096 -f ${KEY_FILE}

HOST=github.com
IP=$(getent hosts $HOST | awk '{ print $1 }')
KNOWN_HOSTS="${TMP_DIR}/known_hosts"
echo "Determining known hosts"
ssh-keyscan -t rsa $HOST $IP > ${KNOWN_HOSTS}

echo "Refreshing ${SECRET_NAME}"
kubectl delete secret ${SECRET_NAME} -n ${NAMESPACE} --ignore-not-found=true
kubectl create secret generic ${SECRET_NAME} -n ${NAMESPACE} --from-file=id_dsa=${KEY_FILE} --from-file=id_dsa.pub=${KEY_FILE}.pub --from-file=known_hosts=${KNOWN_HOSTS}
