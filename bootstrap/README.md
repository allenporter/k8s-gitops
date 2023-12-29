# bootstrap

Configuration needed for bootstrapping the cluster. This directory is for
deploying a clustering following the [Kairos High Availability](https://kairos.io/docs/examples/ha/)
example.

## Initialization

### Build images

See [Network booting](https://kairos.io/docs/installation/netboot/#use-auroraboot) for more details
on Auroraboot.

```bash
$ docker run --rm -ti -p 8080:8080 \
    -v ${PWD}/bootstrap/kairos:/config \
    -v ${PWD}/bootstrap/kairos/build:/tmp/build \
    -v kairos-tmp:/tmp \
    quay.io/kairos/auroraboot:v0.2.7 \
    --debug \
    --cloud-config /config/cloud-config.yaml \
    /config/auroraboot.yaml
```

### Prepare netboot

```bash
$ TFTP_DIR=/Volumes/platform-images/
$ docker container create --name dummy -v kairos-tmp:/tmp hello-world
$ docker cp dummy:/tmp/netboot/kairos-initrd ${TFTP_DIR}/netboot/kairos-initrd
$ docker cp dummy:/tmp/netboot/kairos-kernel ${TFTP_DIR}/netboot/kairos-kernel
$ docker cp dummy:/tmp/netboot/kairos.squashfs ${TFTP_DIR}/netboot/kairos.squashfs
$ docker rm dummy
$ cp bootstrap/kairos/boot.ipxe ${TFTP_DIR}/netboot/
```