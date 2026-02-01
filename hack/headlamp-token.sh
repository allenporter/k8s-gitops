#!/bin/bash

set -e

INGRESS="headlamp"
NAMESPACE="kube-system"
TOKEN_PREFIX="headlamp-admin"

HOSTNAME=$(kubectl get ingress ${INGRESS} -n ${NAMESPACE} -o 'jsonpath={.spec.rules[0].host}')
SECRET_NAME=$(kubectl get secret -n ${NAMESPACE} | grep ${TOKEN_PREFIX} | awk '{print $1}')
SECRET=$(kubectl get secret -n ${NAMESPACE} ${SECRET_NAME} -o 'jsonpath={.data.token}' | base64 --decode)


echo "Login token:"
echo "  ${SECRET}"
echo
echo "Dashboard URL:"
echo "  https://${HOSTNAME}"
