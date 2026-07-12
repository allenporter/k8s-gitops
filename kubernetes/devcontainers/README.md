# Kubernetes-Native Devcontainers

This directory manages lightweight, persistent development environments running directly inside your Kubernetes cluster. It completely replaces Devpod by using standard SSH access over your local network/Tailscale, combined with Cilium LoadBalancer IP assignment and `k8s-gateway` DNS integration.

---

## 1. Local Mac SSH Setup

To connect to your cluster devcontainers, you need to configure SSH on your local Mac.

1.  Open or create your SSH configuration file on your Mac:
    ```bash
    nano ~/.ssh/config
    ```

2.  Add the following wildcard configuration block. This ensures that any SSH connection matching the `.devcontainers` cluster subdomain automatically uses the correct username, port, and key:
    ```text
    Host *.devcontainers.k8s.mrv.thebends.org
      User vscode
      Port 22
      IdentityFile ~/.ssh/id_ed25519
      StrictHostKeyChecking no
      UserKnownHostsFile /dev/null
    ```

---

## 2. Connecting in VS Code

1.  Install the **Remote - SSH** extension in Visual Studio Code on your Mac.
2.  Press `F1` (or click the green remote connection icon in the bottom-left corner of the window).
3.  Select **Remote-SSH: Connect to Host...**.
4.  Type the hostname of the workspace you want to open:
    *   `ws-google-health-api.devcontainers.k8s.mrv.thebends.org`
    *   `ws-ring-keypad.devcontainers.k8s.mrv.thebends.org`
    *   `home-assistant-core.devcontainers.k8s.mrv.thebends.org`
5.  VS Code will connect over SSH, install the remote server agent inside the container, and open a terminal.
6.  Select **Open Folder** and navigate to your workspace directory (e.g. `/workspaces/python-google-health-api`).

---

## 3. First-Time Project Setup (Cloning & Autostart)

When you deploy a new workspace, the persistent volume (`local-hostpath` SSD) is initialized empty.

1.  **Clone the Repo**: Once you SSH into the container for the first time, open the VS Code terminal and clone your project into the target directory:
    ```bash
    git clone https://github.com/allenporter/python-google-health-api.git /workspaces/python-google-health-api
    ```
2.  **Auto-Initialization**: A background loop inside the pod watches your workspace folder. The moment you clone the repository and `.devcontainer/devcontainer.json` appears, the container will automatically run the official Dev Container CLI hooks:
    ```bash
    devcontainer run-user-commands --workspace-folder /workspaces/python-google-health-api
    ```
    This natively triggers all your `postCreateCommand` scripts (like installing `requirements.txt` dependencies or system dependencies) automatically.
3.  **Persistence**: Because the volume is persistent, all installed dependencies, python virtual environments, and configuration files are preserved on the node's local SSD. You only run this setup once per workspace.

---

## 4. How to Add a New Workspace

To add a new project workspace to GitOps, you have two options depending on your preference:

### Option A: Dry Kustomize Overrides (Recommended)
This approach avoids copy-pasting raw YAML manifests by inheriting from the shared `/kubernetes/devcontainers/base/workspace-template` configuration.

1.  Create a new folder: `kubernetes/devcontainers/prod/workspaces/my-new-repo/`.
2.  Create a `kustomization.yaml` that applies a `namePrefix` (which dynamically renames the PVC, Service, and Deployment) and binds the selector labels:
    ```yaml
    ---
    apiVersion: kustomize.config.k8s.io/v1beta1
    kind: Kustomization
    resources:
      - ../../../base/workspace-template
    namePrefix: my-new-repo-
    labels:
      - pairs:
          app: my-new-repo-workspace-temp
    patches:
      - path: patch.yaml
    ```
3.  Create a `patch.yaml` containing only the overrides:
    ```yaml
    ---
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: workspace-temp
    spec:
      template:
        spec:
          containers:
          - name: workspace
            image: mcr.microsoft.com/devcontainers/python:3.14-bookworm
            workingDir: /workspaces/my-new-repo
            args:
            - |
                if ! command -v sshd >/dev/null 2>&1; then
                  echo "sshd not found. Installing openssh-server..."
                  sudo apt-get update && sudo apt-get install -y openssh-server
                fi
                sudo mkdir -p /home/vscode/.ssh
                sudo cp /tmp/ssh-keys/authorized_keys /home/vscode/.ssh/authorized_keys
                sudo chown -R vscode:vscode /home/vscode/.ssh
                sudo chmod 700 /home/vscode/.ssh
                sudo chmod 600 /home/vscode/.ssh/authorized_keys
                sudo ssh-keygen -A
                sudo mkdir -p /var/run/sshd
                sudo /usr/sbin/sshd -D -p 2222
            lifecycle:
              postStart:
                exec:
                  command:
                  - /bin/sh
                  - -c
                  - |
                    (
                      if ! command -v devcontainer >/dev/null 2>&1; then
                        echo "Installing devcontainer CLI..."
                        npm install -g @devcontainers/cli || true
                      fi
                      while [ ! -f /workspaces/my-new-repo/.devcontainer/devcontainer.json ]; do
                        sleep 10
                      done
                      echo "devcontainer.json found! Running user commands..."
                      devcontainer run-user-commands --workspace-folder /workspaces/my-new-repo
                    ) >/tmp/devcontainer-init.log 2>&1 &
            volumeMounts:
            - name: workspace-volume
              mountPath: /workspaces/my-new-repo
            - name: ssh-keys
              mountPath: /tmp/ssh-keys
              readOnly: true
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: workspace-temp-service
      annotations:
        coredns.io/hostname: my-new-repo.devcontainers.k8s.mrv.thebends.org
    spec:
      selector:
        app: my-new-repo-workspace-temp
    ```
4.  Add the directory reference to the `resources:` list inside `kubernetes/devcontainers/prod/kustomization.yaml`.

### Option B: Explicit Manifests
If your project requires heavily customized Pod specifications (such as adding GPUs, custom environment variables, or distinct volumes), copy the directory `kubernetes/devcontainers/prod/workspaces/google-health-api/`, rename the files, and customize the YAML specs directly.
