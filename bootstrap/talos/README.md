# talos

See [talos: Getting Started](https://www.talos.dev/v1.8/introduction/getting-started/) and [talhelper: Getting Started](https://budimanjojo.github.io/talhelper/latest/getting-started/)
for the initial setup.

## Steps

1. Configure DHCP static map matching the `talconf.yaml`
1. Boot machines off the Talos Linux image
1. Remove the USB disk once its running in ram
1. Environment should already be configured with
```bash
$ TALCONFIG=bootstrap/talos/clusterconfig/talosconfig
```

## Generate the talos configuration

```bash
$ task --dir bootstrap/talos/ talhelper-genconfig
```

## Verify disks

Make any last minute adjustments if needed based on USB disk ordering.

```bash
$ talosctl -n 10.10.100.1 get disks
```


## Apply configuration

```bash
$ talosctl apply-config -n 10.10.100.1 --file bootstrap/talos/clusterconfig/k8s-cluster-kapi01.yaml
$ talosctl apply-config -n 10.10.100.2 --file bootstrap/talos/clusterconfig/k8s-cluster-kapi02.yaml
$ talosctl apply-config -n 10.10.100.3 --file bootstrap/talos/clusterconfig/k8s-cluster-kapi03.yaml
$ talosctl apply-config -n 10.10.100.4 --file bootstrap/talos/clusterconfig/k8s-cluster-kube01.yaml
```

## Kubernetes bootstrap

```bash
$ talosctl bootstrap --nodes 10.10.100.1 --endpoints 10.10.100.1 
```

Install kubeconfig:
```bash
$ talosctl  -n 10.10.100.1 kubeconfig
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

## Maintenance

### Update config

```bash
$ task --dir bootstrap/talos/ talhelper-updateconfig
```

### Check manifests

```bash
$ talosctl get manifests -n 10.10.100.1
```

### Reboot

This will reboot all nodes:

```bash
$ talosctl reboot
...
watching nodes: [10.10.100.1 10.10.100.2 10.10.100.3]
    * 10.10.100.1: post check passed
    * 10.10.100.2: post check passed
    * 10.10.100.3: post check passed
```

### Upgrade

1. Edit `talconf.yaml` following suggested [upgrade paths](https://docs.siderolabs.com/talos/v1.12/configure-your-talos-cluster/lifecycle-management/upgrading-talos#supported-upgrade-paths)


2. Regenerate upgrade commands

    ```
    $ task --dir bootstrap/talos/ talhelper-gen-upgrade
    ```

3. Run each command

    ```
    $ talosctl upgrade --talosconfig=./bootstrap/talos/clusterconfig/talosconfig --nodes=10.10.100.1 --
    image=factory.talos.dev/metal-installer/f20a270363ef05e94cec3a1e50cef514e27ad5d593bce64adca56a9756b59134:v1.8.4;
    WARNING: 10.10.100.1: server version 1.8.3 is older than client version 1.12.0
    ◱ watching nodes: [10.10.100.1]
        * 10.10.100.1: waiting for actor ID
    ...
        * 10.10.100.1: post check passed
    ```


### Upgrade Kubernetes

1. Edit `talconf.yaml`

2. Regenerate upgrade commands

    ```
    $ task --dir bootstrap/talos/ talhelper-gen-upgrade-k8s
    ```

3. Run each command. Note this does not work for images with a custom installer like NVidia nodes.

    ```
    $ talosctl upgrade --talosconfig=./bootstrap/talos/clusterconfig/talosconfig --nodes=10.10.100.1 --
    image=factory.talos.dev/metal-installer/f20a270363ef05e94cec3a1e50cef514e27ad5d593bce64adca56a9756b59134:v1.8.4;
    WARNING: 10.10.100.1: server version 1.8.3 is older than client version 1.12.0
    ◱ watching nodes: [10.10.100.1]
        * 10.10.100.1: waiting for actor ID
    ...
    ```
