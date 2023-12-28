# bootstrap

Configuration needed for bootstrapping the cluster. This directory is for
deploying a clustering following the [Kairos High Availability](https://kairos.io/docs/examples/ha/)
example.

## Initialization

### Auroraboot

Auroraboot can deploy new Kairos nodes with zero-touch configuration, booting
nodes over the network. See [Network booting](https://kairos.io/docs/installation/netboot/#use-auroraboot) for more details
on Auroraboot.

Run an AuroraBoot container in the same network as the boxes with these arguments:

```
docker run --rm  -ti \
    -v ${PWD}/bootstrap/kairos:/config \
    -v ${PWD}/bootstrap/kairos/tmp:/tmp \
    quay.io/kairos/auroraboot \
    --cloud-config /config/cloud-config.yaml \
    /config/auroraboot-nuc.yaml
```
