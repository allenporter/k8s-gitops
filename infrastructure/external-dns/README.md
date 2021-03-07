# Routing

## Overview

Services here provide dns and ingress into the cluster, updating an external dns server with `rfc2136`. The local
router redirects DNS queries for the domain name back to the local dns server that happens to run on a Synology
server since it kind of acts like a lower level appliance in the cluster.

## External DNS

The external-dns job is an observer for services `ingress` resources with `external-dns`, then creates a `CNAME`
record based on annotations such as:
```
ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: haproxy-ext-prod
    external-dns.alpha.kubernetes.io/hostname: home-assistant.prod.mrv.thebends.org.
    external-dns.alpha.kubernetes.io/target: prx03.prod.mrv.thebends.org.
    thebends.org/prod-namespace: ""
```

The external-dns chart creates a secrete key that needs a one time registration with the DNS server. You can
list the keys with:

```
$ kubectl get secret -n routing
$ kubectl describe secret -n routing external-dns-dev-token-<xxx>
```

The decode a ke with
