#!/bin/bash
#
# Script to find wasted backup resources in proxmox.

VMS_FILE=$(mktemp /tmp/pve.vms.XXXXXXXX)
BACKUPS_FILE=$(mktemp /tmp/pve.backups.XXXXXXXX)

ssh allen@vmm01.prod -- "sudo pvesh get /cluster/resources --type vm --output-format json" \
    | jq --raw-output .[].id \
    | sed s'/qemu\///g' \
    > ${VMS_FILE}

ssh allen@vmm01.prod -- "sudo pvesm prune-backups vm-backup --dry-run" \
    | grep vm-backup: \
    | cut -f 2 -d '/' \
    | cut -f 3 -d '-' \
    | sort \
    | uniq \
    > ${BACKUPS_FILE}


echo "Backup files that may be waste:"
diff --unchanged-line-format= --old-line-format= --new-line-format='%L'  ${VMS_FILE} ${BACKUPS_FILE}
echo "You may cleanup with something like:"
echo "sudo pvesm prune-backups vm-backup --vmid <ID> --keep-last 1 --dry-run true"
echo
echo "VMS that may not have a backup:"
diff --unchanged-line-format= --old-line-format='%L' --new-line-format=  ${VMS_FILE} ${BACKUPS_FILE}
