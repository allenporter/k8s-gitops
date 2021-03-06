# k8s-gitops

## Introduction

This is a Flux/Gitops managed k8s cluster following the model used by [k8s@home](https://github.com/k8s-at-home). This repository defines the cluster, and flux watches for updates and pushes them.

## Bare Metal

The kubernetes containers managed in this repo run within a larger cluster provisioned via [Terraform](https://www.terraform.io/) and configured via [Ansible](https://www.ansible.com/) on bare metal on [Ubuntu Server](https://ubuntu.com/server). That bootstrap process as well as the k8s worker nodes are all configured via a private git repository, not included here.

<img
src="https://docs.google.com/drawings/d/e/2PACX-1vQSdj_iQgONocRCS5xzm-SGVDlHUF5PFnhRMoef2jgxjehC9hKFuafqKDzUIznGV9FOEWNEFlnstKSt/pub?w=433&amp;h=379"
align=right>


Additional cluster setup not included in this repo includes:

  - [etcd](https://etcd.io/) with 3 nodes managed via ansible
  - [kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/) provisioned via ansible
  - [haproxy](http://www.haproxy.org/) for load balancing kubernetes API via ansible

The bare metal cluster follows best practices for a server [naming
scheme](https://mnx.io/blog/a-proper-server-naming-scheme/) including specifying a geograph, environment (`dev` and `prod`) and a purpose and serial number per machine (e.g. `sto01`, `cfg01`, etc). A local DNS server is shared by the k8s cluster.

## Environments

This repository manages everything else running within the k8s cluster (e.g. containers, load balancers, applications, etc). The repo follows the pattern in [flux2-kustomize-helm-example](https://github.com/fluxcd/flux2-kustomize-helm-example) where applications are specified with overrides for mtuliple environments which map to two seperate kubernetes clusters:

- `dev`: A separate instance for testing/validation for both new configuration and binary releases (e.g. nightly docker image builds)
- `prod`: A production environment with stable binaries and better tested configuration.

Running these environments in separate clusters simplifies overall configuration since the overlay point is within the top level flux configuration without needing to change names or namespaces. There is a down side of requiring additional cluster setup and resources, but automation with ansible and terraform makes that straight forward.

While this is not a high criticality system, having multiple environments makes it easier to move quickly and risk making mistakes in the dev environment first (then getting distracted and leaving it broken for a bit) without harming prod. See [kubernetes: Configure Access to Multiple Clusters](https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/) for details.

## Cluster Infrastructure

The key infrastructure components running within the cluster and managed by this repo are:

<img
src="https://docs.google.com/drawings/d/e/2PACX-1vSZh09V6luZjHGP7YWNVQM9tGQ69R7exD--vz7lknp6Z2OuMDItiVjTSJhjVN2Y-PPaoQoqx2x3D0Ey/pub?w=481&amp;h=374"
align=right>

  - [calico](https://docs.projectcalico.org/about/about-calico) for cluster internal networking
  - [rook-ceph](https://rook.io/): Provides persistent volumes, allowing any application to use the external ceph storage cluster.
  - [kasten k10](https://docs.kasten.io/latest/install/index.html): Provides snapshots and export of backup to external nfs. Requires `VolumeSnapshot` and kubernetes [Snapshot Controller](https://kubernetes-csi.github.io/docs/snapshot-controller.html) for `rook-ceph` snapshots.
  - [metallb](https://metallb.universe.tf/): A load balancer for bare metal kubernetes.
  - [haproxy](https://github.com/haproxytech/kubernetes-ingress): Used for proxying services through kubernetes ingress, exposing any service through the LoadBalancer with TLS.
  - [external-dns](https://github.com/kubernetes-sigs/external-dns): Creates DNS entries on an external dns server for all relevant ingress services in the cluster. This relies on an existing local dns server outside of the cluster.
  - [cert-manager](https://cert-manager.io/docs/): Creates TLS certs using LetsEncrypt for each service in the cluster. Uses `dns01` on a DNS server managed outside of the cluster.

This setup results in load balancing, TLS, ingress services for any application that needs it just by adding annotations.

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
- See [onedr0p's Schedule - Update Flux](https://github.com/onedr0p/home-cluster/blob/main/.github/workflows/flux-schedule.yaml)
  for an example of how to use a GitHub action to update flux itself. My copy is here: [Schedule - Update Flux](.github/workflows/update-flux-schedule.yaml)
- See [cubic3d's diff-hr-on-pr](https://gist.github.com/cubic3d/17b2c601549802501d4ca5a68dcc4db8) which will evaluate
  the diff of a `HelmRelease`, which is helpful for spotting breaking changes. My copy is here: [Diff HelmReleases](.github/workflows/diff-hr-on-pr.yaml)

## Resources

  - https://github.com/fluxcd/flux2-kustomize-helm-example
  - https://github.com/k8s-at-home/awesome-home-kubernetes
