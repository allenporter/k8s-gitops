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
$ bootstrap/scripts/setup-flux.sh
```

## Secrets

The following GCP secrets must be set with the gcloud role account set with `Secret Accessor`:

For bootstrapping flux:
- flux-k8s-gitops-github-token

For anything that requires certs
- letsencrypt-account-key - this is a certbot private jwk key, but can be replaced with pem key if needed in the future (it is converted to pem in ansible role)

For network configuration:
- dyndns-login
- dyndns-password
- rtr01-encrypted-password

For sops:
- sops-k8s-gitops-dev
- sops-k8s-gitops-prod

# SOPS

See https://fluxcd.io/flux/guides/mozilla-sops/ for instructions on setting up.

Fetching sops secret keys from local store for backup:
```
$ KEY_NAME=dev.mrv.thebends.org
$ KEY_ID=$(gpg --list-secret-keys --keyid-format LONG  "${KEY_NAME}" | awk '/^      [A-Z0-9]{40}/{if (length($1) > 0) print $1}')
$ SOPS_KEY_FP=${KEY_ID##*/}
$ gpg --export-secret-keys --armor "${SOPS_KEY_FP}"
```
