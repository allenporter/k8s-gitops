# Kubernetes-Native Devcontainers Architecture & Design Guide

This directory manages lightweight, persistent development environments running directly inside your Kubernetes cluster. It completely replaces external tools like Devpod by leveraging GitOps (Flux), your local private registry (Zot), and standard SSH access over your local network/Tailscale.

---

## 1. System Architecture (What We Have)

Our devcontainer ecosystem is divided into two distinct parts: **The Build Pipeline** and **The Workspace Runtime**.

```
+---------------------------------------------------------------------------------+
| BUILD PIPELINE (CronJob)                                                        |
|                                                                                 |
|  +--------------------------+                      +-------------------------+  |
|  | Builder Container        |                      | DinD Container          |  |
|  |                          |                      |                         |  |
|  | 1. git clone             |                      | Runs Docker daemon      |  |
|  | 2. devcontainer build    | ===[DOCKER_HOST]====>| performs layer builds   |  |
|  |    --cache-to type=inline|                      |                         |  |
|  +--------------------------+                      +-------------------------+  |
|               ||                                                                |
|               || [push image + cache]                                           |
+---------------+-----------------------------------------------------------------+
                ||
                \/
+--------------------------------------------+
| Zot Private Registry (Secure HTTPS)        |
| - URL: registry.k8s.mrv.thebends.org       |
+--------------------------------------------+
                ||
                || [pull pre-built image]
                \/
+---------------------------------------------------------------------------------+
| WORKSPACE RUNTIME (Deployment)                                                  |
|                                                                                 |
| - Image: registry.k8s.mrv.thebends.org/devcontainers/<repo>:latest              |
| - Storage: local-hostpath NVMe SSD (Persistent mount to /workspaces)            |
| - SSH: sshd running inside container namespace on port 2222                     |
| - LoadBalancer: Cilium assigns LAN IP; CoreDNS maps hostname                    |
+---------------------------------------------------------------------------------+
```

### A. The Build Pipeline
Instead of compiling Dockerfiles inside the workspace pod on boot, we use an asynchronous build pipeline in the cluster:
*   **Suspended CronJobs**: Each workspace folder includes a `builder-cronjob.yaml`. The CronJobs are defined with `suspend: true` so they never run on a schedule. Instead, they act as GitOps templates.
*   **Manual Trigger**: Rebuilds are triggered manually when you update a devcontainer configuration:
    ```bash
    kubectl create job build-ring-keypad-manual --from=cronjob/build-ring-keypad -n devcontainers
    ```
*   **Docker-in-Docker (DinD)**: The builder pod launches a standard Node.js image alongside a privileged `docker:dind` sidecar container. The builder clones the repository, installs the `@devcontainers/cli` natively, and runs the compilation.

### B. Shared Inline Caching
To avoid downloading packages and compilers (like Rust) from scratch every time:
*   We use BuildKit's **Inline Caching** (`--cache-to type=inline` / `--cache-from type=registry,...`). This embeds the layer caching metadata directly inside the main image tag.
*   **Cross-Project Reuse**: Caches are shared seamlessly across different projects. For example, building the `journal-assistant` devcontainer pulls the cached layers from the `ring-keypad` image, allowing the entire Rust compiler setup step to finish in exactly **1.8 seconds** instead of minutes.

### C. The Workspace Runtime
*   **Pre-Built Images**: The workspace Deployment pulls the fully compiled image directly from your Zot registry. Booting takes less than **0.1 seconds** because no setups or builds run on startup.
*   **Persistent Storage**: Workspaces mount a `local-hostpath` Persistent Volume Claim at `/workspaces`. Installed Python virtualenvs, dependencies, and configuration files are preserved permanently on the node's local NVMe SSD.
*   **sshd Entrypoint**: The container runs an entrypoint script that verifies if `sshd` is present. If missing, it installs it in 2 seconds via `apt-get` and launches the daemon on port `2222`. Your authorized keys are copied with strict `0600` permissions on startup.
*   **Cilium & CoreDNS Integration**: Each workspace has a dedicated `LoadBalancer` Service. Cilium assigns it a stable LAN IP (e.g. `10.10.102.7`), and the `k8s-gateway` CoreDNS plugin automatically registers it as `<workspace-name>.devcontainers.k8s.mrv.thebends.org` for direct access.

---

## 2. Design Choices & Rationale

*   **Local NVMe SSDs (`local-hostpath`) vs. Ceph**: Development activities (compilations, virtualenv creations, dependency resolutions) are highly disk-I/O intensive. Distributed network filesystems like Ceph introduce too much latency. Binding to the local SSD of the host node guarantees bare-metal performance.
*   **Secure HTTPS Registry vs. ClusterIP**: We route registry traffic through Zot's secure external ingress domain (`registry.k8s.mrv.thebends.org`). This ensures standard TLS validation (via cert-manager Let's Encrypt), meaning Talos nodes (`containerd`) and the builder pods can pull and push images securely without configuring complex insecure registry mirrors in Talos machine configurations.
*   **Inline Caching vs. Registry Cache Tags**: Pushing a separate cache tag using `--cache-to type=registry` utilizes custom OCI index schemas that many registries (including Zot) fail to write. Storing cache metadata inline inside the destination image is highly robust and universally compatible.
*   **Suspended CronJobs vs. Operators**: Using suspended CronJobs keeps the cluster configuration declarative and transparent. Rebuild templates are version-controlled in git alongside the deployment manifests, requiring no central controller database or API state.

---

## 3. Future Work & Boilerplate Reduction

While the current setup is highly resilient, we can consider the following enhancements:

### A. Pre-Baked Base Images (Strategy C)
Instead of having every workspace container run `apt-get install -y openssh-server` on boot, we can build a custom "homelab-base-developer" base image that pre-bakes `sshd`, Git, Node, and common toolchains. Individual workspaces will inherit from this image (`FROM registry.k8s.mrv.thebends.org/devcontainers/homelab-base:latest`), making runtime startup completely instant.

### B. Mutating Webhook (Boilerplate Injection)
Currently, our `pod.yaml` deployments contain boilerplate configurations for SSH key copying, sshd checks, volume mounts, and shell args.
*   **How it would work**: We could deploy a simple Mutating Admission Webhook (e.g. using Kyverno or a tiny Go controller).
*   **Boilerplate Elimination**: When a developer creates a minimal workspace Deployment, the webhook intercepts the API call and dynamically injects the sshd containers, volume mounts, env variables, and SSH keys. The git repository manifests would reduce to a clean, 10-line YAML.

### C. Helm Template Packaging
Alternatively, we can wrap the workspace specifications into a single, localized Helm Chart. Adding a workspace would then require only defining a small `values.yaml` file:
```yaml
workspaceName: journal-assistant
gitUrl: https://github.com/allenporter/home-assistant-journal-assistant.git
storageSize: 10Gi
```

---

## 4. Alternatives Investigated & Downsides

Before committing to this DIY GitOps model, we evaluated several popular devcontainer orchestration tools:

*   **Coder**
    *   *Downside*: Requires a heavy centralized control plane, PostgreSQL database, and licensing/enterprise boundaries. It bypassed GitOps, managing workspaces through imperative API calls and database states.
*   **Daytona**
    *   *Downside*: Tailored primarily for Virtual Machine and Cloud Provider backends (like AWS EC2/DigitalOcean). Its Kubernetes provider is immature and poorly documented, making it hard to integrate with local storage classes and native ingress controllers.
*   **DevWorkspace Operator (Eclipse Che)**
    *   *Downside*: Highly complex architecture requiring dozens of Custom Resource Definitions (CRDs). It enforces web-based IDE interfaces (like OpenShift Dev Spaces) and breaks native, direct SSH access over Tailscale/LAN.
*   **Our DIY GitOps Model**
    *   *Upside*: Extremely lightweight (zero additional controllers deployed). Workspace states and build configurations are fully declared in Git, managed by Flux, and leverage existing cluster infrastructure (Zot, Cilium, k8s-gateway, local SSDs).
