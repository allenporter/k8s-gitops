# kairos

Configuration needed for bootstrapping the cluster. This directory is for
deploying a clustering following the [Kairos High Availability](https://kairos.io/docs/examples/ha/)
example.

## Initialization

Bootstrapping the cluster requires the following steps:

- Hosts configured with mac address + ip assignments in the dhcp server.
- `cloud-config-seconary.yaml` updated with the ip address of the primary server.
- Build images (see below)
- Ensure machine boot order & `reboot` flags are set as appropriate
- Boot up the primary server with the primary iso
- Boot up the secondary servers with the secondary iso

## Building contiainer isos

```
$ ansible-playbook -i localhost, --connection=local  bootstrap/kairos/build-container.yaml
```


## Building cloud config isos

```
$ ansible-playbook -i localhost, --connection=local  bootstrap/kairos/build-cloud-config.yaml
```
