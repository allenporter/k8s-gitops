#!/bin/bash

set -e

function get_secret() {
  if [ "${CONTEXT}" == "template" ]; then
    echo ""
    return 0
  fi
  secret_name=$1
  namespace=$2
  key=$3
  kubectl get secret ${secret_name} -n ${namespace} ${KUBECTL_FLAGS} -o jsonpath="{.data.${key}}" | base64 --decode
  return 0
}

SECRET_NAME="sops-gpg"
SECRET_NAMESPACE="flux-system"
SECRET_KEY="sops.asc"

SOPS_KEY_FP=$(get_secret "${SECRET_NAME}" "${SECRET_NAMESPACE}" "${SECRET_KEY}")
if [ "${SOPS_KEY_FP}" != "" ]; then
    echo Secret key already exists at "${SECRET_NAMESPACE}/${SECRET_NAME}"
    exit 0
fi

KEY_NAME="${ENV}.mrv.thebends.org"
KEY_COMMENT="flux secrets"

echo "Checking if ${KEY_NAME} exists"
ret=0
gpg --list-secret-keys "${KEY_NAME}" || ret=$?
if [ $ret -ne 0 ]; then
    gpg --batch --full-generate-key <<EOF
%no-protection
Key-Type: 1
Key-Length: 4096
Subkey-Type: 1
Subkey-Length: 4096
Expire-Date: 0
Name-Comment: ${KEY_COMMENT}
Name-Real: ${KEY_NAME}
EOF
    gpg --list-secret-keys "${KEY_NAME}"
fi


KEY_ID=$(gpg --list-secret-keys --keyid-format LONG  "${KEY_NAME}" | awk '/^      [A-Z0-9]{40}/{if (length($1) > 0) print $1}')
SOPS_KEY_FP=${KEY_ID##*/}

# Key can be imported with something like:
# kubectl get secret sops-gpg -n flux-system -o jsonpath="{.data.sops\.asc}" | base64 --decode | gpg --import /dev/stdin
gpg --export-secret-keys --armor "${SOPS_KEY_FP}" | kubectl create secret generic "${SECRET_NAME}" --namespace="${SECRET_NAMESPACE}" --from-file=${SECRET_KEY}=/dev/stdin
echo Exporting key id "${SOPS_KEY_FP}"
echo Secret key created at "${SECRET_NAMESPACE}/${SECRET_NAME}"
