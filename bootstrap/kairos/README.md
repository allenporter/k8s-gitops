# kairos

Configuration needed for bootstrapping the cluster. This directory is for
deploying a clustering following the [Kairos High Availability](https://kairos.io/docs/examples/ha/)
example.

## Initialization

Bootstrapping the cluster requires the following steps:

- Hosts configured with mac address + ip assignments in the dhcp server.
- `cloud-config-seconary.yaml` updated with the ip address of the primary server.
- Build images (see below)
- Boot up the primary server with the primary iso
- Boot up the secondary servers with the secondary iso


## Build images

See [AuroraBoot](https://kairos.io/docs/reference/auroraboot/) for more details on Auroraboot and building images (not using netboot).

Build primary image and copy to an iso directory:
```bash
$ ISO_DIR=/Volumes/platform-images/template/iso
# Build primary image
$ CLOUD_CONFIG=cloud-config-primary.yaml CONFIG=auroraboot.yaml BUILD_DIR=build/primary bootstrap/kairos/build-image.sh
$ cp bootstrap/kairos/build/primary/kairos.iso.custom.iso ${ISO_DIR}/kairos-primary.iso
# Build secondary image
$ CLOUD_CONFIG=cloud-config-secondary.yaml CONFIG=auroraboot.yaml BUILD_DIR=build/secondary  bootstrap/kairos/build-image.sh
$ cp bootstrap/kairos/build/secondary/kairos.iso.custom.iso ${ISO_DIR}/kairos-secondary.iso
```
