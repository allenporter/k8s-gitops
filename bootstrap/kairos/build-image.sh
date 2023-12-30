#!/bin/bash

: ${CLOUD_CONFIG:="cloud-config.yml"}
: ${CONFIG:="auroraboot.yml"}
: ${BUILD_DIR:="build"}

BOOTSTRAP="${PWD}/bootstrap/kairos"

docker run --rm -ti \
    -v ${BOOTSTRAP}:/config \
    -v ${BOOTSTRAP}/${BUILD_DIR}:/tmp/build \
    -v kairos-tmp:/tmp \
    quay.io/kairos/auroraboot:v0.2.7 \
    --debug \
    --cloud-config /config/${CLOUD_CONFIG} \
    /config/${CONFIG}
