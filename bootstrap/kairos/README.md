# Cluster Bootstrap: Kairos

Automation for bootstraping a 3+ node [k3s](http://k3s.io) cluster using [Kairos](https://kairos.io)
and [Ansible](https://www.ansible.com/).

The cluster foundation has the following attributes:
- [High Availability](https://kairos.io/docs/examples/ha/) k3s cluster with 3+ nodes
- Immutable node images that are [Upgradable from Kubernetes](https://kairos.io/docs/upgrade/kubernetes/)
- Automated initial secure join process using Ansible to distribute [SOPS](https://github.com/getsops/sops) and [Age](https://github.com/FiloSottile/age)
- High Availability control plane entrypoint using [kube-vip](https://kube-vip.io/)
- Simple to deploy networking using [Calico](https://docs.tigera.io/calico/latest/about/)

Once bootstraped, the cluster is managed by [Flux](https://fluxcd.io/) including handling
any updates of the above components. As a result, the bootstrap configuration is
minimal and not directly integrated with other parts of the cluster inventory.

References:
- [Trying out Kairos](https://tyzbit.blog/trying-out-kairos) as a starting point to learn about Kairos
- [flux-cluster-template](https://github.com/onedr0p/flux-cluster-template) for some technology and automation choices.

## Pre-requisites

Bootstrapping the cluster requires the following steps:

- Wipe any disks (e.g. ubuntu live boot and wipe)
- Ensure machine boot order is set (usb, disk, ...)
- Hosts configured with mac address + ip assignments in the dhcp server
- Download a standard (includes k3s) kairos iso (currently ubuntu) and put on usb

## Installation

The boostrap uses a "manual install" mode to keep the process of building and
distributing configuration files as simple as possible. The process is non-interactive.

1. Update `bootstrap/kairos/inventory/hosts.yaml` with ip and hardware labels (for future use).

1. Boot the node using the image, starting with primary control plane node.

1. Build the `cloud-config.yaml` for the node:
    ```
    $ task  --dir bootstrap/kairos/ build-cloud-config -- -l kapi01
    ```
1. Start a [Manual Installation](https://kairos.io/docs/installation/manual/), which is a non-interactive setup:
    ```
    # Login with a password of `kairos`. This takes around 3-4 minutes.
    $ ssh kairos@10.10.100.1 'sudo kairos-agent manual-install ./kapi01-cloud-config.yaml'
1. Remove the usb stick and rebot the node.
    ```
    $ ssh kairos@10.10.100.1 'sudo reboot -f'
    ```
1. Repeat for other control plane nodes, then other worker nodes. Note: The secondary nodes should wait for the primary to be setup before starting install.

## ML Acclerators

1. Copy `bootstrap/kairos/nvidia/100_nvida.yaml` to the node
1. Reboot the node.

## Control Plane

Access to the cluster control plane is organized through [kubeconfig Files](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/), which are generated using Ansible and
updated to use the kube-vip entry point:
```
$ export ANSIBLE_CONFIG=bootstrap/kairos/ansible.cfg
$ ANSIBLE_CONFIG=bootstrap/kairos/ansible.cfg ansible-playbook bootstrap/kairos/kubeconfig-env.yaml  -l kapi01
```

This sets up the kubeconfig file where the devcontainer enviroment is ready to access it, e.g.
```
$ export KUBECONFIG=~/.env/kubeconfig.yaml  # Already handled by devcontainer
$ kubectl get pods -A
NAMESPACE     NAME                                       READY   STATUS    RESTARTS     AGE
kube-system   calico-kube-controllers-5fc7d6cf67-qbgh5   1/1     Running   1 (9h ago)   9h
kube-system   calico-node-9xpxw                          1/1     Running   1 (9h ago)   9h
kube-system   calico-node-h7gzh                          1/1     Running   0            8h
kube-system   calico-node-kxt8w                          1/1     Running   2 (8h ago)   9h
kube-system   coredns-6799fbcd5-sg5zq                    1/1     Running   1 (9h ago)   9h
kube-system   kube-vip                                   1/1     Running   3 (8h ago)   9h
kube-system   local-path-provisioner-84db5d44d9-ghxn4    1/1     Running   1 (9h ago)   9h
kube-system   metrics-server-67c658944b-wtv27            1/1     Running   1 (9h ago)   9h
```

## Other references:

- [k3s: Network Options](https://docs.k3s.io/installation/network-options)
- [Quickstart for Calico on k3s](https://docs.tigera.io/calico/latest/getting-started/kubernetes/k3s/quickstart)
- [kube-vip: Static pods](https://kube-vip.io/docs/installation/static/)
- [Karios: Reset a node](https://kairos.io/docs/reference/reset/#remotely-via-command-line) for
instructions on remotely resetting from the command line back to the original image

## Troubleshooting

View kairos-agent logs with `journalctl -fu kairos-agent`
