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

## Secret Configuration

external-dns requires a key shared with the DNS server. set the key for external-dns with:

```
$ kubectl create secret generic external-dns-key -n external-dns --from-literal="tsigSecret=MY-SECRET"
```
