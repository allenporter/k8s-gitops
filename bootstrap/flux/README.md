# Cluster bootstrap: Flux

## Pre-requisites

Before starting this step have:

- A working cluster, control plane
- Initialized devcontainer or development environment

## Initialize Flux

1. Create the namespace

    ```
    $ task create-namespace
    ```

1. Initialize secrets for SOPS. The current setup uses a key with age .
    ```
    $ task bootstrap-sops-key
    ```

1. Install flux. The following is equivalent to `flux install` plus creating the `flux-system`
Kustomization that points at `kubernetes/clusters/prod`:
    ```
    $ task install-flux
    ```

## References

- [Manage Kubernetes secrets with Mozilla SOPS](https://fluxcd.io/flux/guides/mozilla-sops/)
