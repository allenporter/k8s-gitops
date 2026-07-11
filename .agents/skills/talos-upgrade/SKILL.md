---
name: talos-upgrade
description: Guidelines and procedures for upgrading Talos Linux and Kubernetes in the GitOps cluster using talhelper and talosctl.
---

# Talos OS and Kubernetes Upgrade Guide

This skill outlines how to perform minor version upgrades for Talos Linux and Kubernetes.

## Prerequisites

- **Client Tools:** Ensure `talosctl` and `talhelper` are installed and available in the environment.
- **SOPS Decryption:** Set `SOPS_AGE_KEY_FILE` pointing to `.env/k8s-gitops-age-key.txt` to decrypt environment variables during config generation.
- **Docker CLI:** Access to the `docker` command to verify target images before deploying.

---

## Upgrade Steps

### Step 1: Registry Verification
Always verify that the custom image with GPU/NVIDIA or special system extensions exists in the Sidero Image Registry before changing configurations:
```bash
docker manifest inspect factory.talos.dev/metal-installer/<schematic-id>:<target-version>
```
For `kube01` (NVIDIA node), the schematic ID is `26124abcbd408be693df9fe852c80ef1e6cc178e34d7d7d8430a28d1130b4227`.

### Step 2: Configuration Update
1. Modify `bootstrap/talos/talconf.yaml`.
2. Update `talosVersion` or `kubernetesVersion`.
3. If upgrading Talos OS, update the custom installer image patch for `kube01` and follow the historical comment tracking convention to document driver/tool versions.
4. Convert any legacy RFC6902 JSON patches (`op: add`, `path: ...`) to YAML Strategic Merge Patches, as JSON patches are unsupported for modern Talos multi-document configuration generation.

### Step 3: Config Compilation and Localization
1. Compile the config files:
   ```bash
   SOPS_AGE_KEY_FILE=.env/k8s-gitops-age-key.txt task --dir bootstrap/talos/ talhelper-genconfig
   ```
2. Pull down and localize the CRDs/manifests:
   ```bash
   ./hack/localize/localize.sh
   ```

### Step 4: Verification and PR
1. Run `git diff` to inspect changes.
2. Push changes to a branch and raise a GitHub PR.
3. Once the PR is merged to `main`, Flux will reconcile CRDs on the cluster.

### Step 5: Execute Upgrade
1. Apply updated configurations to the nodes:
   ```bash
   task --dir bootstrap/talos/ talhelper-updateconfig
   ```
2. Generate upgrade commands:
   - For Talos OS: `task --dir bootstrap/talos/ talhelper-gen-upgrade`
   - For Kubernetes: `task --dir bootstrap/talos/ talhelper-gen-upgrade-k8s`
3. Run the generated upgrade command on each node one-by-one (starting with control planes `kapi01` - `kapi03`, then worker `kube01`).
4. Monitor node reboots and API statuses via `talosctl -n <node-ip> dashboard` or `talosctl -n <node-ip> health`.

### Step 6: Post-Upgrade Health Checks
- Verify node ready status: `kubectl get nodes -o wide`
- Confirm all pods are healthy: `kubectl get pods -A | grep -v -E "Running|Completed"`
- Confirm Ceph storage health: `kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph status`
