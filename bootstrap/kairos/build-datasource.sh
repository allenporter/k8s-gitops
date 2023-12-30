#!/bin/bash

set -e

KAIROS_DIR="${PWD}/bootstrap/kairos"
: ${BUILD_DIR:="${KAIROS_DIR}/build"}

IMAGE="primary"
for image in primary secondary; do
    if [ ! -f ${KAIROS_DIR}/cloud-config-${image}.yaml ]; then
        echo "Could not find image ${image} in ${KAIROS_DIR}"
        exit 1
        IMAGE=${image}
        break
    fi
    WORK_DIR="${BUILD_DIR}/${IMAGE}"
    mkdir -p ${WORK_DIR}
    touch ${WORK_DIR}/meta-data
    cp -rfv ${KAIROS_DIR}/cloud-config-${IMAGE}.yaml ${WORK_DIR}/user-data
    ISO="${BUILD_DIR}/${IMAGE}.iso"
    echo "Building ${ISO}"
    mkisofs -output ${ISO} -volid cidata -joliet -rock ${WORK_DIR}/meta-data ${WORK_DIR}/user-data
done
