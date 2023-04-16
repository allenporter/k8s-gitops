#!/bin/bash
#
# Starts the k8s-gitops-env environment, which is a hermetic environment for
# running operations on the client. This is an alternative to the previous
# approach of having bastion-like machines configured using ansible.

set -e

: "${IMAGE:=ghcr.io/allenporter/k8s-gitops-env}"
: "${VERSION:=latest}"
: "${NAME:=k8s-gitops-env}"
: "${SRC_DIR:=${HOME}}"

docker exec -it ${NAME} bash || docker run -it \
    --name ${NAME} \
    -v ${SRC_DIR}/k8s-gitops:/data/k8s-gitops \
    -v ${SRC_DIR}/homelab:/data/homelab \
    ${IMAGE}:${VERSION}
