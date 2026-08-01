# Kubernetes-Native Devcontainers Architecture & Operations Guide

This directory manages lightweight, persistent, multi-repository development environments running directly inside your Kubernetes cluster. It leverages GitOps (Flux), an internal private registry (Zot), shared CephFS keyring authentication, native internal Ingress (`nginx-internal`), and direct SSH access.

---

## 🌐 1. Grouped Workspaces & Web UI Access

Workspaces are organized into 4 domain-focused groups. Each workspace is exposed over clean, port-free HTTPS with valid Let's Encrypt TLS certificates via your internal Ingress controller (`nginx-internal` on `10.10.102.3`):

| Workspace | Purpose / Grouped Repositories | Direct Internal HTTPS Access URL |
| :--- | :--- | :--- |
| **`ws-home-automation`** | `home-assistant-core`, `google-health-api`, `pyrainbird`, `home-assistant-ring-keypad`, `python-roborock`, `python-google-nest-sdm`, `gcal_sync`, `python-google-photos-library-api`, `icaldav`, `ical`, `home-assistant-datasets` | 👉 **[https://ws-home-automation.k8s.mrv.thebends.org/](https://ws-home-automation.k8s.mrv.thebends.org/)** |
| **`ws-harness-dev`** | `adk-coder`, ADK harness framework, custom HA-ADK integration components | 👉 **[https://ws-harness-dev.k8s.mrv.thebends.org/](https://ws-harness-dev.k8s.mrv.thebends.org/)** |
| **`ws-journal-notes`** | `journal-assistant`, `supernote` parser | 👉 **[https://ws-journal-notes.k8s.mrv.thebends.org/](https://ws-journal-notes.k8s.mrv.thebends.org/)** |
| **`ws-platform`** | `k8s-gitops`, `devcontainer-features`, `repo-conformance` | 👉 **[https://ws-platform.k8s.mrv.thebends.org/](https://ws-platform.k8s.mrv.thebends.org/)** |

---

## 🔑 2. Authentication & Single Sign-On (Shared CephFS Keyring)

### Shared Keyring Architecture
* All 4 workspace pods mount a shared ReadWriteMany (RWX) CephFS Persistent Volume Claim (**`antigravity-shared-keyring-pvc`**) at `/home/vscode/.local/share/keyrings`.
* **Single Sign-On (SSO)**: Logging in **ONCE** on any workspace (e.g. `ws-home-automation`) saves `login.keyring` to CephFS, automatically authenticating all 4 DevContainers across all cluster nodes!

### Initial Google OAuth Setup Workflow

When authenticating a workspace for the first time:

1. **Click "Sign In"**:
   Open **[https://ws-home-automation.k8s.mrv.thebends.org/](https://ws-home-automation.k8s.mrv.thebends.org/)** in Chrome and click **Sign In**.

2. **Get the Active OAuth URL & Port**:
   Run the `agy-auth` helper command in your Mac terminal:
   ```bash
   KUBECONFIG=/Users/allen/Development/k8s-gitops/kubeconfig kubectl exec -n devcontainers deployment/ws-home-automation -- agy-auth
   ```

3. **Authorize & Port-Forward Callback**:
   * Open the printed `https://accounts.google.com/o/oauth2/auth?...` URL in Chrome and log in.
   * Note the callback port in `redirect_uri` (e.g. `41031`).
   * Forward that port from your Mac terminal:
     ```bash
     KUBECONFIG=/Users/allen/Development/k8s-gitops/kubeconfig kubectl port-forward -n devcontainers deployment/ws-home-automation <CALLBACK_PORT>:<CALLBACK_PORT>
     ```
   * Chrome will automatically redirect to `http://localhost:<CALLBACK_PORT>/auth/callback?...` and complete your login!

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
|  - Shared Keyring: ReadWriteMany CephFS PVC at /home/vscode/.local/share/keyrings|
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

Each workspace deployment mounts a 40Gi local NVMe volume at **`/workspaces`**. The Helm chart (`devcontainer-workspace` `v0.2.9`) automatically clones the primary repository and any extra repositories into subfolders under `/workspaces/`:

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
* **Check Logins / Auth URLs**:
  ```bash
  KUBECONFIG=./kubeconfig kubectl exec -n devcontainers deployment/ws-home-automation -- agy-auth
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
