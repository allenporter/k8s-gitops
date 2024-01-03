# kairos

Configuration needed for bootstrapping the cluster. This directory is for
deploying a clustering following the [Kairos High Availability](https://kairos.io/docs/examples/ha/)
example and [tyzbit's learnings](https://tyzbit.blog/trying-out-kairos)

## Initialization

Bootstrapping the cluster requires the following steps:

- Hosts configured with mac address + ip assignments in the dhcp server.
- Download a standard (includes k3s) kairos image (currently ubuntu)
- Wipe any disks (e.g. ubuntu live boot and wipe)
- Ensure machine boot order & `reboot` flags are set as appropriate
- Boot up the primary kapi server and configure
- Boot up the secondary kapi servers and configure
- Boot up kube workers and configure

Ansible is used to assign roles to nodes and share necessary secrets for building
a High Availability cluster. See `bootstrap/kairos/inventory/hosts.yaml`
for configuration, which is only used for initial cluster setup and not used for
maintenance given the cluster can be [Upgraded from Kubernetes](https://kairos.io/docs/upgrade/kubernetes/).

## Building cloud config

The boostrap uses a "manual install" mode to keep the process of building and
distributing configuration files as simple as possible. All templating is done
via ansible, rather than putting worker configuration template complexity into
the config itself to be evaluated by the node. We are using the simplest possible
configuration, where all other customization is handled after boot via Kubernetes.

Build and push `cloud-config.yaml` to a node then initiate a manual install:
```
$ ANSIBLE_CONFIG=bootstrap/kairos/ansible.cfg ansible-playbook bootstrap/kairos/build-cloud-config.yaml -l kapi01
...
# Perform manual install. Login with a password of `kairos`. This takes ~4 minutes at most.
$ ssh kairos@10.10.100.1 'sudo kairos-agent manual-install ./kapi01-cloud-config.yaml'
$ ssh kairos@10.10.100.1 'sudo reboot -f'
```
Note: The secondary nodes have to wait for the primary to be setup before starting install.

## Wipe a node

See [Reset a node](https://kairos.io/docs/reference/reset/#remotely-via-command-line) for
instructions on remotely resetting from the command line back to the original image.

## Plan

- [x] create a build directory for each host w/ ansible
- [ ] test each image in docker
- [ ] Prepare /dev/nvme0n1 for ceph

## Verify manifests & bundles

/var/lib/rancher/k3s/server/manifests/

## Boot record

- node 1) old install
- node 2) old install
- node 3) old install
