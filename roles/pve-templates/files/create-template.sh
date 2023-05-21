#!/usr/bin/bash

: ${TEMPLATE_ID:=9000}
: ${NAME:=ubuntu-template}
: ${IMAGE_FILE:=focal-server-cloudimg-amd64.img}
: ${STORAGE:=vm-pool}

IMAGE_DIR="/mnt/pve/platform-images/images"
IMAGE="${IMAGE_DIR}/${IMAGE_FILE}"

echo "Checking if VM already exists"
qm status ${TEMPLATE_ID}
if [ $? -eq 0 ];
then
  echo "VM template ${TEMPLATE_ID} already created."
  exit 0
fi

# Exit on failure
set -e

# create a new VM
echo "Creating new node"
qm create ${TEMPLATE_ID} --memory 2048 --net0 virtio,bridge=vmbr0 --scsihw virtio-scsi-pci

# import the downloaded disk to storage
#echo "Importing image to storage"
#qm importdisk ${TEMPLATE_ID} ${IMAGE} ${STORAGE} -format qcow2

# finally attach the new disk to the VM as scsi drive
echo "Attach disk as scsi drive"
qm set ${TEMPLATE_ID} --scsi0 ${STORAGE}:0,import-from=${IMAGE}

echo "Configuring cloud-init"
qm set ${TEMPLATE_ID} --ide2 ${STORAGE}:cloudinit

echo "Attach boot drive"
qm set ${TEMPLATE_ID} --boot c --bootdisk scsi0

echo "Naming template"
qm set ${TEMPLATE_ID} -name ${NAME}

echo "Creating template"
qm template ${TEMPLATE_ID}