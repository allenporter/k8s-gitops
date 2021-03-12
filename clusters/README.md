# Clusters

## Overview

This respository follows the pattern in [flux2-kustomize-helm-example](https://github.com/fluxcd/flux2-kustomize-helm-example) though modified for the usecases
of this cluster.

Applications in the cluster desire multiple environments:

- `dev`: A separate instance for testing/validation before release
- `prod`: A production environment with stable/better tested features

While this is not a high criticality system, it just makes it easier to move
quickly and risk making mistakes in the dev environment first (then getting
distracted and leaving it broken for a bit) without harming prod.

This document is in progress, evaluating these different approaches to use
flux, helm, and kustomize given the current state of the cluster.

## Multi-cluster

One simple approach is to setup multiple clusters, then run the same structure
in both clusters.

- Simplifies kustomization: The separation point happens within the flux-system
- Requires additional cluster setup and resources
- May be annoying to switch back and forth between dev and prod.

## Multi-namepsaces by env

Put all applications in a single `dev` or `prod` namespace:

- Simple
- No app organiation: Everything is in one namespace.
- Very messy! `kubectl get pods` becomes useless

## Multi-release within single env

Run separate release for each application, with different names: e.g. `prometheus-dev` vs `prometheus-prod`

- Allows use of namespaces for app organization, but not for environment organization

## Mutli-namespaces per app per env

Create applications in a namespace like `monitoring-dev` and `monitoring-prod` with a release name like `prometheus`.

- Effectively uses namespaces for app + environment organization together
- However may be more frustrating to keep track all the combinations.

## Resources

See https://github.com/fluxcd/flux2-multi-tenancy for a different example.
