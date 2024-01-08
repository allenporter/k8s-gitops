# k8s-gitops

## Introduction

This is a Flux/Gitops managed k8s cluster following the model used by [k8s@home](https://github.com/k8s-at-home). This repository defines the cluster, and flux watches for updates and pushes them.

## Bare Metal

The cluster is provisioned as [Kairos](https://kairos.io) high availability [k3s](http://k3s.io) using [kube-vip](https://kube-vip.io/) and [Calico](https://docs.tigera.io/calico/latest/about/) for simple to deploy cluster networking.

The nodes have a mix of accelerators.

See [bootstrap](/bootstrap/kairos/) for more background on provisioning of bare
metal nodes.

## Development Toolchain

This repository contains a `.devcontainer` which is the environment used to manage the k8s cluster
from the CLI. The `.devcontainer` has some default mounts including the private terraform
inventory and `.env` which is a local directory for local secret storage. More detail on
bootstrapping can be found in `bootstrap/env` and `k8s-gitops-env.yaml` performs the secret setup.

## Network Operations

The cluster follows best practices for a server [naming scheme](https://mnx.io/blog/a-proper-server-naming-scheme/)
including specifying a geography, environment (`dev` and `prod`) and a purpose
and serial number per machine (e.g. `sto01`, `cfg01`, etc). DNS for machines are
managed outside of the cluster.

## Services & Naming

Reliable, secure, and discoverable services are provided by the following:
  - [metallb](https://metallb.universe.tf/): A load balancer for bare metal kubernetes.
  - [ingress-nginx](https://github.com/kubernetes/ingress-nginx): Used for proxying services through kubernetes ingress, exposing any service through the LoadBalancer with TLS.
  - [k8s_gateay](https://github.com/ori-edge/k8s_gateway): DNS server for all relevant ingress services in the cluster. This relies on an existing local dns server outside of the cluster to perform forwwarding.
  - [cert-manager](https://cert-manager.io/docs/): Creates TLS certs using LetsEncrypt for each service in the cluster. Uses `dns01` on a DNS server managed outside of the cluster.

## Storage

The key storage components running within the cluster are:

  - [rook-ceph](https://rook.io/): Provides persistent volumes, allowing any application to use the external ceph storage cluster.
  - [volsync](https://volsync.readthedocs.io/en/stable/): Backup and restore for persistent volumes.
  - [democratic-csi](https://github.com/democratic-csi/democratic-csi): For other non-standard
  volumes (local, nfs, smb, etc)

## Updates

Updates to the cluster are managed by Renovate and and a handful of github actions. Renovate will either apply updates
silently or send PRs to update packages to the latest versions, which are then automatically pushed to the cluster by
flux. Renovate has a bit of a learning curve, so here are the pieces i've put together following the patterns of the
k8s-at-home folks:

- See [Renovate Docs: GitHub app installation](https://docs.renovatebot.com/install-github-app/) for how to enable Renovate on a github repo
- See the [Renovate configuration](renovate.json5) for this cluster which has separate updates schedules for the `dev`
  and `prod` clusters. The `dev` cluster is updated silently, while the `prod` cluster has minor updates applied on
  weekends. This config is heavily documented given there are numerous [Configuration Options](https://docs.renovatebot.com/configuration-options/) that may be hard to piece together.
- See [Renovate Dashboard](https://app.renovatebot.com/dashboard) for visibility into what Renovate is doing behind the
  scenes. This is pretty useful if you start making configuration changes.
- See [Renovate Helm Releases](https://github.com/k8s-at-home/renovate-helm-releases) for a GitHub action that adds the
  neccessary annotations to a `HelmRelease` so that renovate knows how to manage it. In other words, renovate-helm-releases
  doesn't actually do any updating itself, just prep work to make Renovate work. You have to update your renovate
  configuration with a regexp, which is a simple solution to avoid adding special code in Renovate itself to support
  this. This runs as a nightly action to opt in any newly added `HelmRelease`.

## Resources

  - https://github.com/fluxcd/flux2-kustomize-helm-example
  - https://github.com/k8s-at-home/awesome-home-kubernetes
