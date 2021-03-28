# Certmanager

## Setup

This requires setup following the instructions in https://cert-manager.io/docs/configuration/acme/dns01/google/
namely creating a service account with dns admin permissions. Download the service account credentials as key.json
create that as a secret:

```
$ kubectl create secret generic clouddns-dns01-solver-svc-acct -n cert-manager --from-file=key.json
```
