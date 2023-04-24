# Setup

## Flux

The k8s cluster itself is bootstrapped using ansible in another repo, where
this repo is used only for managing flux itself and other applications
running in kubernetes.

Flux setup is modeled after these guides:

  - https://github.com/fluxcd/flux2-kustomize-helm-example
  - https://github.com/billimek/k8s-gitops/tree/master/setup

See https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/ for more details on
multi-cluster kubernetes configuration.

```
# Set up the flux environment based on GITHUB_REPO, GITHUB_USER, GITHUB_TOKEN
$ scripts/setup-flux.sh
```

## Storage

Ceph is also currently configured externally, managed via ansible. This repo
just manages setup of ceph for use within kuberntes.

```
$ scripts/setup-ceph.sh
```
