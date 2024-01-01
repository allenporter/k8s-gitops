# kairos

Configuration needed for bootstrapping the cluster. This directory is for
deploying a clustering following the [Kairos High Availability](https://kairos.io/docs/examples/ha/)
example.

## Initialization

Bootstrapping the cluster requires the following steps:

- Hosts configured with mac address + ip assignments in the dhcp server.
- `cloud-config-seconary.yaml` updated with the ip address of the primary server.
- Install image images (see below)
- Ensure machine boot order & `reboot` flags are set as appropriate
- Boot up the primary server and configure
- Boot up the secondary servers and configure
- Boot up workers and configure

## Building cloud config isos

```
$ ansible-playbook -i localhost, --connection=local  bootstrap/kairos/build-cloud-config.yaml
```

## Plan

- [x] create a build directory for each host w/ ansible
- [ ] test each image in docker
- [ ] Prepare /dev/nvme0n1 for ceph
