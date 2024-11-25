# talos

See [talos: Getting Started](https://www.talos.dev/v1.8/introduction/getting-started/) and [talhelper: Getting Started](https://budimanjojo.github.io/talhelper/latest/getting-started/)
for the initial setup.

## Steps

1. Configure DHCP static map matching the `talconf.yaml`
1. Boot machines off the Talos Linux image
1. Remove the USB disk once its running in ram


## Generate the talos configuration

```bash
$ task --dir bootstrap/talos/ talhelper-genconfig
```

## Verify disks

Make any last minute adjustments if needed based on USB disk ordering.

```bash
$ talosctl -n 10.10.100.1 disks --insecure
```


## Apply configuration

```bash
$ talosctl apply-config --insecure -n 10.10.100.1 --file bootstrap/talos/clusterconfig/k8s-cluster-kapi01.yaml
$ talosctl apply-config --insecure -n 10.10.100.2 --file bootstrap/talos/clusterconfig/k8s-cluster-kapi02.yaml
$ talosctl apply-config --insecure -n 10.10.100.3 --file bootstrap/talos/clusterconfig/k8s-cluster-kapi03.yaml
```

## Kubernetes bootstrap

```bash
$ talosctl bootstrap --nodes 10.10.100.1 --endpoints 10.10.100.1 --talosconfig bootstrap/talos/clusterconfig/talosconfig
```

Install kubeconfig:
```bash
$ talosctl --talosconfig bootstrap/talos/clusterconfig/talosconfig -n 10.10.100.1 kubeconfig
```

## Verify Kubernetes health

If load balancer is not up, then need to manually modify the config to point to a single endpoint.

```bash
$ kubectl get nodes -A
NAME     STATUS   ROLES           AGE    VERSION
kapi01   Ready    control-plane   117s   v1.29.11
kapi02   Ready    control-plane   97s    v1.29.11
kapi03   Ready    control-plane   115s   v1.29.11
```

## Apply configuration to other nodes

```bash
$ talosctl apply-config --insecure -n 10.10.100.4 --file bootstrap/talos/clusterconfig/k8s-cluster-kube01.yaml
```

## Reboot

This will reboot all nodes:

```bash
$ talosctl reboot --talosconfig bootstrap/talos/clusterconfig/talosconfig
...
watching nodes: [10.10.100.1 10.10.100.2 10.10.100.3]
    * 10.10.100.1: post check passed
    * 10.10.100.2: post check passed
    * 10.10.100.3: post check passed
```
