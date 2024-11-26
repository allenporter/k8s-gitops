# Cluster bootstrap: Flux

## Pre-requisites

Before starting this step have:

- A working cluster, control plane
- Initialized devcontainer or development environment

## Initialize Flux

1. Create the namespace

    ```
    $ task --dir bootstrap/flux/ create-namespace
    ```

1. Initialize secrets for SOPS. The current setup uses a key with age .
    ```
    $ task --dir bootstrap/flux/ bootstrap-sops-key
    ```

1. Install flux. The following is equivalent to `flux install`.
    ```
    $ task --dir bootstrap/flux/ install-flux
    ```
1. Bootstrap the flux-system kustomization which creates the Kustomization that points at `kubernetes/clusters/prod`:
    ```
    $ task --dir bootstrap/flux/ install-flux-system-ks
    ```

1. Once the cluster is built, handle any custom hardware cluster policies.
    ```
    $ task --dir bootstrap/flux install-gpu-policy
    ```

## References

- [Manage Kubernetes secrets with Mozilla SOPS](https://fluxcd.io/flux/guides/mozilla-sops/)

## Network

```bash
$ helm repo add cilium https://helm.cilium.io/
$ helm repo update
$ helm install \
    cilium \
    cilium/cilium \
    --version 1.15.6 \
    --namespace kube-system \
    --set ipam.mode=kubernetes \
    --set kubeProxyReplacement=false \
    --set securityContext.capabilities.ciliumAgent="{CHOWN,KILL,NET_ADMIN,NET_RAW,IPC_LOCK,SYS_ADMIN,SYS_RESOURCE,DAC_OVERRIDE,FOWNER,SETGID,SETUID}" \
    --set securityContext.capabilities.cleanCiliumState="{NET_ADMIN,SYS_ADMIN,SYS_RESOURCE}" \
    --set cgroup.autoMount.enabled=false \
    --set cgroup.hostRoot=/sys/fs/cgroup
```
