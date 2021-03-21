# k8s-gitops

## Introduction

This is a Flux/Gitops managed k8s cluster following the model used by [k8s@home](https://github.com/k8s-at-home). This repository defines the cluster and flux watches for updates and pushes them.

## Cluster

The kubernetes containers managed in this repo run within a larger cluster provisioned via [Terraform](https://www.terraform.io/) and configured via [Ansible](https://www.ansible.com/) on bare metal on [Ubuntu Server](https://ubuntu.com/server). That bootstrap process as well as the k8s worker nodes are all configured via a private git repository, not included here.

<img src="https://docs.google.com/drawings/d/e/2PACX-1vQSdj_iQgONocRCS5xzm-SGVDlHUF5PFnhRMoef2jgxjehC9hKFuafqKDzUIznGV9FOEWNEFlnstKSt/pub?w=579&h=507" width="579" height"507" align="right">

Additional cluster setup not included in this repo includes:

  - [etcd](https://etcd.io/) with 3 nodes managed via ansible
  - [kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/) provisioned via ansible
  - [haproxy](http://www.haproxy.org/) for load balancing kubernetes API via ansible
  - [calico](https://docs.projectcalico.org/about/about-calico) for cluster internal networking via ansible

This repository manages everything else running within the k8s cluster (e.g. containers, load balancers, applications, etc). See setup/ flux bootstrap.

## Motivation

The cluster has multiple existing helm charts which are manually installed, and are being moved into this repository to automate deployment. I was effectively managing per environment kustomization myself via separate helm values files.

## Resources

  - https://github.com/fluxcd/flux2-kustomize-helm-example
  - https://github.com/k8s-at-home/awesome-home-kubernetes
