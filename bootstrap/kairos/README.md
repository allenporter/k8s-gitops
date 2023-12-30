# kairos

Configuration needed for bootstrapping the cluster. This directory is for
deploying a clustering following the [Kairos High Availability](https://kairos.io/docs/examples/ha/)
example.

## Initialization

### Build images

See [Network booting](https://kairos.io/docs/installation/netboot/#use-auroraboot) for more details on Auroraboot and building images (not netboot).

Build primary image:
```bash
$ CLOUD_CONFIG=cloud-config-primary.yaml CONFIG=auroraboot.yaml bootstrap/kairos/build-image.sh
$ ISO_DIR=/Volumes/platform-images/template/iso
$ cp bootstrap/kairos/build/kairos.iso.custom.iso ${ISO_DIR}/kairos-primary.iso
```

Build secondary image:
```bash
$ CLOUD_CONFIG=cloud-config-secondary.yaml CONFIG=auroraboot.yaml bootstrap/kairos/build-image.sh
$ ISO_DIR=/Volumes/platform-images/template/iso
$ cp bootstrap/kairos/build/kairos.iso.custom.iso ${ISO_DIR}/kairos-secondary.iso
```
