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

---

## Kubernetes CA Rotation (`talosctl rotate-ca`)

### Blast Radius Warning
Running `talosctl rotate-ca --kubernetes=true` replaces `kube-root-ca.crt` with **only** the new CA once the final step removes the old CA. Long-running in-cluster controllers and pods load `/var/run/secrets/kubernetes.io/serviceaccount/ca.crt` into memory once at startup and do **not** reload it from disk. As soon as the old CA is dropped, those pods fail API server TLS verification (`x509: certificate signed by unknown authority`), which breaks Cilium networking/DNS watches, L2 announcements, CSI provisioners, ingress, monitoring, auth, CI, and device plugins until restarted.

### Required Post-Rotation Rolling Restarts
Immediately after `talosctl rotate-ca --kubernetes=true --dry-run=false` completes, restart in-cluster API clients starting with networking/DNS:
1. **Networking / DNS / Ingress:**
   - `kube-system`: `ds/cilium` (verify all nodes — delete/recreate any pod that didn't self-restart), `deploy/coredns`, `deploy/headlamp`
   - `k8s-gateway`: `deploy/k8s-gateway`
   - `nginx`: `deploy/nginx-internal-ingress-nginx-controller`, `deploy/nginx-external-ingress-nginx-controller`
   - `tailscale`: `deploy/operator`
2. **Storage / CSI:**
   - `rook-ceph`: `deploy/rook-ceph-operator`, `deploy/csi-cephfsplugin-provisioner`, `deploy/csi-rbdplugin-provisioner`
   - `kube-system`: `deploy/snapshot-controller`
   - `democratic-csi`: `ds/local-path-provisioner-node`
3. **Monitoring / Auth / Certs / CI / Device Plugins:**
   - `monitoring`: `sts/prometheus-kube-prometheus-stack-prometheus`, `deploy/kube-prometheus-stack-operator`, `deploy/kube-prometheus-stack-grafana`
   - `cert-manager`: `deploy/cert-manager`, `deploy/cert-manager-cainjector`, `deploy/cert-manager-webhook`
   - `dexidp`: `deploy/dex`
   - `arc-systems`: `deploy/gha-runner-scale-set-controller-gha-rs-controller`
   - `intel-device-plugin`: `deploy/inteldeviceplugins-controller-manager`
   - `nvidia-device-plugin`: `ds/nvidia-device-plugin`
   - `node-feature-discovery`: `deploy/node-feature-discovery-gc`, `deploy/node-feature-discovery-master`
   - `system-upgrade`: `deploy/system-upgrade-controller`

Verify afterward that 0 pods log `certificate signed by unknown authority` and that in-cluster and external DNS resolve cleanly.

### Safely Syncing `bootstrap/talos/talsecret.sops.yaml`
- **Never** assume Go `yq` syntax (`from_yaml`); macOS Homebrew often ships Python `yq` (a `jq` wrapper).
- **Always** guard `sops set` with `set -euo pipefail`, non-empty variable checks (`: "${VAR:?}"`), and X.509 decode/fingerprint validation before writing to `talsecret.sops.yaml`:
  ```bash
  set -euo pipefail
  # Works with Python yq (jq wrapper); for Go yq, use `.spec | from_yaml | .cluster.ca.{crt,key}`
  NEW_CRT="$(talosctl -n 10.10.100.1 -e 10.10.100.1 get machineconfig v1alpha1 -o yaml \
    | yq -r .spec | yq -sr '[.[] | select(.cluster != null)][0].cluster.ca.crt')"
  NEW_KEY="$(talosctl -n 10.10.100.1 -e 10.10.100.1 get machineconfig v1alpha1 -o yaml \
    | yq -r .spec | yq -sr '[.[] | select(.cluster != null)][0].cluster.ca.key')"

  : "${NEW_CRT:?NEW_CRT is empty — aborting}"
  : "${NEW_KEY:?NEW_KEY is empty — aborting}"
  printf '%s' "$NEW_CRT" | base64 -d | openssl x509 -noout -fingerprint -sha256

  sops set bootstrap/talos/talsecret.sops.yaml '["certs"]["k8s"]["crt"]' "\"$NEW_CRT\""
  sops set bootstrap/talos/talsecret.sops.yaml '["certs"]["k8s"]["key"]' "\"$NEW_KEY\""
  ```
- Regenerate `bootstrap/talos/clusterconfig/*` with `task --dir bootstrap/talos/ talhelper-genconfig` and verify `git diff bootstrap/talos/talsecret.sops.yaml` remains SOPS-encrypted.
