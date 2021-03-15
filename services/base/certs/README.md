# Certificates

## Sync

In order to sync certs across namespaces, a one time setup is needed:

```
  annotations:
    kubed.appscode.com/sync: "cert-manager-tls=thebends-wildcard"
```
