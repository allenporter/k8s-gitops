# k8s-gitops

## Introduction

This is a Flux/Gitops managed k8s cluster following the model used by [k8s@home](https://github.com/k8s-at-home). This repository defines the cluster and flux watches for updates and pushes them.

## Cluster

The servers that make up the cluster are provisioned via [Terraform](https://www.terraform.io/) and configured via [Ansible](https://www.ansible.com/) on bare metal on [Ubuntu Server](https://ubuntu.com/server). That bootstrap process as well as the k8s worker nodes are all configured via a private git repository, not included here.

Initial cluster setup not included here includes:

  - [etcd](https://etcd.io/) with 3 nodes managed via ansible
  - [kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/) provisioned via ansible
  - [haproxy](http://www.haproxy.org/) for load balancing kubernetes API via ansible
  - [calico](https://docs.projectcalico.org/about/about-calico) for cluster internal networking via ansible
  - [haproxy k8s ingress](https://github.com/haproxytech/kubernetes-ingress) for providing `ingress` for the cluster and tls keys via helm

This repository manages everything else running within the k8s cluster. See setup/ flux bootstrap.

## Motivation

The cluster has multiple existing helm charts which are manually installed, and are being moved into this repository to automate deployment. I was effectively managing per environment kustomization myself via separate helm values files.


## Progress

  [x] Bootstrapped flux and operators
  [x] podinfo example up and running
  [ ] ceph for persistent volume claims
  [ ] prometheus speed test


## Resources

  - https://github.com/fluxcd/flux2-kustomize-helm-example)
  - https://github.com/k8s-at-home/awesome-home-kubernetes

