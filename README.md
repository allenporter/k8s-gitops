# k8s-gitops

## Introduction

This is a Flux/Gitops managed k8s cluster following the model used by [k8s@home](https://github.com/k8s-at-home). This repository defines the cluster and flux watches for updates and pushes them.

## Cluster

The kubernetes containers managed in this repo run within a larger cluster provisioned via [Terraform](https://www.terraform.io/) and configured via [Ansible](https://www.ansible.com/) on bare metal on [Ubuntu Server](https://ubuntu.com/server). That bootstrap process as well as the k8s worker nodes are all configured via a private git repository, not included here.

<img
src="https://docs.google.com/drawings/d/e/2PACX-1vQSdj_iQgONocRCS5xzm-SGVDlHUF5PFnhRMoef2jgxjehC9hKFuafqKDzUIznGV9FOEWNEFlnstKSt/pub?w=433&amp;h=379"
align=right>

Additional cluster setup not included in this repo includes:

  - [etcd](https://etcd.io/) with 3 nodes managed via ansible
  - [kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/) provisioned via ansible
  - [haproxy](http://www.haproxy.org/) for load balancing kubernetes API via ansible
  - [calico](https://docs.projectcalico.org/about/about-calico) for cluster internal networking via ansible

This repository manages everything else running within the k8s cluster (e.g. containers, load balancers, applications, etc). See setup/ flux bootstrap.

The key infrastructure components running within the cluster and managed by this repo are:

  - [rook-ceph](https://rook.io/): Provides persistent volumes, allowing any application to use the external ceph storage cluster
  - [metallb](https://metallb.universe.tf/): A load balancer for bare metal kubernetes
  - [external-dns](https://github.com/kubernetes-sigs/external-dns): Creates DNS entries on an external dns server for all relevant ingress services in the cluster. This relies on an existing local dns server outside of the cluster.
  - [certmanager](https://cert-manager.io/docs/): Configured to create TLS certs for all ingress services automatically using LetsEncrypt, using DNS
   method and a DNS server run outside the cluster.
  - [haproxy](https://github.com/haproxytech/kubernetes-ingress): Used for proxying services through kubernetes ingress, exposing any service through the LoadBalancer with TLS.

This setup results in load balancing, TLS, ingress services for any application that needs it just by adding annotations.

## Motivation

The cluster has multiple existing helm charts which are manually installed, and are being moved into this repository to automate deployment. I was effectively managing per environment kustomization myself via separate helm values files.

## Resources

  - https://github.com/fluxcd/flux2-kustomize-helm-example
  - https://github.com/k8s-at-home/awesome-home-kubernetes
