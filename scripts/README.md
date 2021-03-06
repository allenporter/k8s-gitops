# Setup

## Flux

The k8s cluster itself is bootstrapped using ansible in another repo, where
this repo is used only for managing flux itself and other applications
running in kubernetes.

Flux setup is modeled after these guides:

  - https://github.com/fluxcd/flux2-kustomize-helm-example
  - https://github.com/billimek/k8s-gitops/tree/master/setup

## Storage

Ceph is also currently configured externally, managed via ansible. This repo
just manages setup of ceph for use within kuberntes.
