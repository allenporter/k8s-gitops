---
name: cluster-health
description: Procedures, runbooks, and diagnostic command chains for inspecting Kubernetes cluster health, Flux GitOps status, Ceph storage, and Alertmanager alerts.
---

# Cluster Health Review Runbook

Use this skill when asked to review, audit, or report on cluster health, active alerts, or degraded workloads.

---

## 1. Quick Health Audit Sequence

Run the following diagnostic steps in order:

### Step 1: Node & Pressure Status
Verify all nodes are `Ready` and have no pressure conditions:
```bash
kubectl get nodes -o wide
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.conditions[*]}{.type}={.status}{" "}{end}{"\n"}{end}'
```

### Step 2: Pod & Workload Health
Check for non-running pods or pods with unready containers:
```bash
# 1. Non-running or non-succeeded pods
kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded

# 2. Running pods with unready containers
kubectl get pods -A -o json | jq -r '.items[] | select(.status.containerStatuses != null) | select(any(.status.containerStatuses[]; .ready == false and .state.terminated == null)) | "\(.metadata.namespace)/\(.metadata.name)"'
```

### Step 3: GitOps Pipeline (Flux CD)
Ensure all Kustomizations, HelmReleases, and HelmRepositories are synced and ready:
```bash
flux get kustomizations
flux get helmreleases -A | grep -v "True"
flux get sources helm -A | grep -v "True"
```

### Step 4: Storage Health (Rook-Ceph & PVCs)
Inspect Ceph daemons, cluster health, and verify all PVCs are bound:
```bash
# 1. Ceph overall health via toolbox
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph status

# 2. CephObjectStore status
kubectl -n rook-ceph get cephobjectstore

# 3. Check for any unbound PVCs
kubectl get pvc -A | grep -v "Bound"
```

### Step 5: Active Alerts (Alertmanager & Prometheus)
Query Alertmanager directly from within the cluster, filtering out the standard `Watchdog` heartbeat:
```bash
# Alertmanager active problem alerts
kubectl -n monitoring exec alertmanager-kube-prometheus-stack-alertmanager-0 -c alertmanager -- \
  wget -qO- "http://localhost:9093/api/v2/alerts?filter=alertname!=Watchdog"

# Prometheus active alert state
kubectl -n monitoring exec alertmanager-kube-prometheus-stack-alertmanager-0 -c alertmanager -- \
  wget -qO- http://kube-prometheus-stack-prometheus:9090/api/v1/alerts
```

### Step 6: Certificate Health
Verify cert-manager TLS certificates:
```bash
kubectl get certificates -A | grep -v "True"
```

---

## 2. Operational Invariants & Guidelines

### Strict GitOps (Zero Out-of-Band Live Patches)
- **NEVER** apply ad-hoc or temporary mutations to workloads, Helm releases, or manifests directly via `kubectl apply` or `helm upgrade`.
- All configuration changes, version pins, and fixes **must** be made declaratively via Git (commit, push, PR, merge) and applied via Flux reconciliation (`flux reconcile ...`).
- Manual live edits are overwritten by Flux upon reconciliation and create split-brain state between Git and the live cluster.

### Renovate Automerge Protection
- Renovate is configured to automerge patch updates in `**/prod/**` after 1 day.
- When pinning a broken upstream package to an earlier version, you **must** also add an `ignoreVersions` rule to `.github/renovate.json5`:
  ```json5
  packageRules: [
    {
      description: 'Ignore broken package version',
      matchPackageNames: ['<package-name>'],
      ignoreVersions: ['<broken-version>'],
    },
  ]
  ```
  Without this rule, Renovate will automatically open and merge a bump back to the broken version within hours.

### Ceph RGW Multisite Commit Error 22
- If `CephObjectStore` fails reconciliation with `failed to commit RGW configuration period changes ... exit status 22`, check the zone/period metadata sync state.
- Resolve by committing the period with the override flag inside the toolbox pod:
  ```bash
  kubectl -n rook-ceph exec deploy/rook-ceph-tools -- \
    radosgw-admin period update --commit --rgw-realm=ceph-objectstore \
    --rgw-zonegroup=ceph-objectstore --rgw-zone=ceph-objectstore --yes-i-really-mean-it
  ```

### Stale DevPod Cleanup
- Standalone pods in the `devpod` namespace terminated by node reboots (`Pod was terminated in response to imminent node shutdown`) remain in `Error` state indefinitely.
- Safely delete failed pods using:
  ```bash
  kubectl -n devpod delete pod --field-selector=status.phase=Failed
  ```
  Their associated PersistentVolumeClaims remain `Bound` and preserved.
