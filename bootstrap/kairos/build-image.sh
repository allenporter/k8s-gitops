#!/bin/bash

KAIROS_DIR="${PWD}/bootstrap/kairos"

: ${CONFIG:="auroraboot.yaml"}
: ${BUILD_DIR:="${KAIROS_DIR}/build"}

docker run --rm -ti \
    -v ${KAIROS_DIR}:/config \
    -v ${BUILD_DIR}:/tmp/build \
    -v kairos-tmp:/tmp \
    quay.io/kairos/auroraboot:v0.2.7 \
    --debug \
    /config/${CONFIG}
