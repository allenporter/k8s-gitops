# Kubernetes-Native Devcontainers Architecture & Operations Guide

This directory manages lightweight, persistent, multi-repository development environments running directly inside your Kubernetes cluster. It leverages GitOps (Flux), an internal private registry (Zot), native internal Ingress (`nginx-internal`), and direct SSH access.

---

## 🌐 1. Grouped Workspaces & Web UI Access

Workspaces are organized into domain-focused environments. Each workspace is exposed over clean, port-free HTTPS with valid Let's Encrypt TLS certificates via your internal Ingress controller (`nginx-internal` on `10.10.102.3`):

| Workspace | Purpose / Grouped Repositories | Direct Internal HTTPS Access URL | Node |
| :--- | :--- | :--- | :--- |
| **`ws-home-automation`** | `home-assistant-core`, `google-health-api`, `pyrainbird`, `home-assistant-ring-keypad`, `python-roborock`, `python-google-nest-sdm`, `gcal_sync`, `python-google-photos-library-api`, `icaldav`, `ical`, `home-assistant-datasets` | 👉 **[https://ws-home-automation.k8s.mrv.thebends.org/](https://ws-home-automation.k8s.mrv.thebends.org/)** | `kapi01` |
| **`ws-harness-dev`** | `adk-coder`, ADK harness framework, custom HA-ADK integration components | 👉 **[https://ws-harness-dev.k8s.mrv.thebends.org/](https://ws-harness-dev.k8s.mrv.thebends.org/)** | `kube01` |
| **`ws-journal-notes`** | `journal-assistant`, `supernote` parser | 👉 **[https://ws-journal-notes.k8s.mrv.thebends.org/](https://ws-journal-notes.k8s.mrv.thebends.org/)** | `kapi03` |
| **`ws-platform`** | `k8s-gitops`, `devcontainer-features`, `repo-conformance` | 👉 **[https://ws-platform.k8s.mrv.thebends.org/](https://ws-platform.k8s.mrv.thebends.org/)** | `kapi02` |
| **`ws-home-assistant-llm`** | `home-assistant-datasets`, `home-assistant-synthetic-home`, `home-assistant-google-adk`, `home-assistant-rulebook`, `hass-openai-custom-conversation` | 👉 **[https://ws-home-assistant-llm.k8s.mrv.thebends.org/](https://ws-home-assistant-llm.k8s.mrv.thebends.org/)** | `kapi02` |
| **`ws-home-assistant-llm-gpu`** | `home-assistant-datasets` (NVIDIA GTX 1070 GPU accelerated) | 👉 **[https://ws-home-assistant-llm-gpu.k8s.mrv.thebends.org/](https://ws-home-assistant-llm-gpu.k8s.mrv.thebends.org/)** | `kube01` |
| **`ws-personal`** | General purpose personal workspace & scratchpad | 👉 **[https://ws-personal.k8s.mrv.thebends.org/](https://ws-personal.k8s.mrv.thebends.org/)** | `kapi03` |

---

## 🔑 2. Authentication & Credential Storage

### Isolated Persistent Storage
* Each workspace pod maintains its persistent configuration and OAuth tokens under `/workspaces/.persistent/` mounted directly to `/home/vscode/.gemini`, `/home/vscode/.config`, and `/home/vscode/.local/share/keyrings`.
* This ensures all login sessions, CLI configurations, and state survive pod restarts and rollouts.

### Google Account Login Workflow (`agy auth login`)

All workspaces run the `antigravity-remote-control` feature bundling the native `agy` CLI (`/usr/local/bin/agy`) alongside the Language Server Web Hub daemon:

1. **Log in directly via `agy auth login`**:
   ```bash
   KUBECONFIG=./kubeconfig kubectl exec -it -n devcontainers deployment/ws-home-automation -c workspace -- agy auth login
   ```
2. **Authorize in Browser**:
   * Open the printed `https://accounts.google.com/o/oauth2/auth?...` URL in your browser and authorize your account.
   * Paste the verification code back into the terminal prompt.
3. **Automatic Synchronization**:
   * The OAuth token is saved to `~/.gemini/antigravity-cli/antigravity-oauth-token` and automatically synchronized with the background Language Server daemon (`~/.gemini/antigravity/`).
   * The Web Hub and Google Remote Control ([https://antigravity.google](https://antigravity.google)) will immediately connect.

---

## 🛠 3. System Architecture & Ingress Setup

```
+---------------------------------------------------------------------------------+
| INGRESS & NETWORKING LAYER                                                      |
|                                                                                 |
|  - Controller: Ingress-Nginx Internal (ingressClassName: nginx-internal)        |
|  - VIP Address: 10.10.102.3                                                     |
|  - Domain Wildcard: *.k8s.mrv.thebends.org (Let's Encrypt TLS Validated)        |
|  - TLS / HTTP2: SSL termination at edge; upstream proxy to port 52425 (HTTP)    |
|  - Header Rewriting: nginx.ingress.kubernetes.io/upstream-vhost: "localhost:52425"|
+---------------------------------------------------------------------------------+
                                      ||
                                      \/
+---------------------------------------------------------------------------------+
| WORKSPACE POD RUNTIME                                                           |
|                                                                                 |
|  - Storage: 40Gi local-hostpath NVMe SSD mounted at /workspaces                 |
|  - Daemon: Antigravity language_server listening on 127.0.0.1:52424            |
|  - Bridging: socat listening on 0.0.0.0:43635 -> 127.0.0.1:52424                |
|  - SSH: OpenSSH daemon listening on port 2222                                    |
+---------------------------------------------------------------------------------+
```

### Ingress & Port Mapping
* **Clean Single-Level Domains**: Browsers access `https://ws-*.k8s.mrv.thebends.org/` over port `443`.
* **Zero SSL Warnings**: Single-level subdomain `ws-*.k8s.mrv.thebends.org` natively matches your cluster's Let's Encrypt wildcard certificate!
* **HTTP/2 Multiplexing**: Infinite concurrent SSE streams (`SubscribeToSidecars`, `JetboxSubscribeToState`, etc.) over a single TLS socket.
* **Header Rewriting**: Uses `nginx.ingress.kubernetes.io/upstream-vhost: "localhost:52425"` for native Host header compliance without snippet security errors.

---

## 📁 4. Multi-Repository Storage Setup

Each workspace deployment mounts a 40Gi local NVMe volume at **`/workspaces`**. The Helm chart (`devcontainer-workspace` `v0.3.1`) automatically clones the primary repository and any extra repositories into subfolders under `/workspaces/`:

### Example HelmRelease Configuration (`ws-home-automation-release.yaml`):
```yaml
values:
  workspaceName: home-automation
  git:
    url: https://github.com/home-assistant/core.git
    directory: home-assistant-core
    extraRepos:
      - url: https://github.com/allenporter/google-health-api.git
        directory: google-health-api
      - url: https://github.com/allenporter/pyrainbird.git
        directory: pyrainbird
      - url: https://github.com/allenporter/home-assistant-ring-keypad.git
        directory: home-assistant-ring-keypad
      - url: https://github.com/allenporter/python-roborock.git
        directory: python-roborock
      - url: https://github.com/allenporter/python-google-nest-sdm.git
        directory: python-google-nest-sdm
      - url: https://github.com/allenporter/gcal_sync.git
        directory: gcal_sync
      - url: https://github.com/allenporter/python-google-photos-library-api.git
        directory: python-google-photos-library-api
      - url: https://github.com/allenporter/icaldav.git
        directory: icaldav
      - url: https://github.com/allenporter/ical.git
        directory: ical
      - url: https://github.com/allenporter/home-assistant-datasets.git
        directory: home-assistant-datasets
```

---

## 🔧 5. Maintenance & Operations Commands

### Useful Taskfile & Kube Commands

* **Check Pods & Ingress Status**:
  ```bash
  KUBECONFIG=./kubeconfig kubectl get pods,ingress -n devcontainers
  ```
* **Check Auth / CLI Status**:
  ```bash
  KUBECONFIG=./kubeconfig kubectl exec -it -n devcontainers deployment/ws-home-automation -c workspace -- agy auth status
  ```
* **Log In to Antigravity**:
  ```bash
  KUBECONFIG=./kubeconfig kubectl exec -it -n devcontainers deployment/ws-home-automation -c workspace -- agy auth login
  ```
* **Inspect Antigravity Daemon Logs**:
  ```bash
  KUBECONFIG=./kubeconfig kubectl exec -n devcontainers deployment/ws-home-automation -- tail -n 50 /home/vscode/.gemini/antigravity/language_server.log
  ```
* **Trigger Cluster Image Builder CronJob**:
  ```bash
  KUBECONFIG=./kubeconfig kubectl create job --from=cronjob/build-home-automation build-home-automation-manual -n devcontainers
  ```
* **Force Reconcile Flux GitOps**:
  ```bash
  KUBECONFIG=./kubeconfig flux reconcile kustomization devcontainers --with-source
  ```
