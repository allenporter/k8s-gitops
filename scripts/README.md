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

## Bootstrapping the environment

The following commands will setup ~/.env/ with appropriate configuration for k8s-gitops-env iamge:
```
$ ENV_INVENTORY_ROOT=/workspaces/homelab/hosts
$ ansible-playbook plays/k8s-gitops-env.yaml -i ${ENV_INVENTORY_ROOT}/prod/inventory.yaml 
$ ansible-playbook plays/k8s-gitops-env.yaml -i ${ENV_INVENTORY_ROOT}/dev/inventory.yaml 
```

You must set `ENV_INVENTORY_ROOT` in your environment persistently since it will be used
by scripts to set up the environment when running `prod` or `dev`.

## Secrets

The following GCP secrets must be set with the gcloud role account set with `Secret Accessor`:

For provisioning VMs:
- dns-terraform-key
- proxmox-terraform-prov-api-key

For bootstrapping flux:
- flux-k8s-gitops-github-token

For bootstrapping out of cluster prometheus:
- proxmox-prometheus-pve-exporter-api-key
- alertmanager-gmail-secret

For anything that requires certs
- letsencrypt-account-key - this is a certbot private jwk key, but can be replaced with pem key if needed in the future (it is converted to pem in ansible role)

For network configuration:
- dyndns-login
- dyndns-password
- rtr01-encrypted-password