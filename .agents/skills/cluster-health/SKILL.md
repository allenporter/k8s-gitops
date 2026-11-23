---
name: cluster-health
description: Procedures, runbooks, and diagnostic command chains for inspecting Kubernetes cluster health, Flux GitOps status, Ceph storage, and Alertmanager alerts.
---

# Cluster Health Review Runbook

Use this skill when asked to review, audit, or report on cluster health, active alerts, or degraded workloads.

## 0. Environment & Tooling Defaults
- **Kubeconfig:** If `kubectl config current-context` is unset (e.g., when invoked from another workspace), set `KUBECONFIG=/workspaces/k8s-gitops/kubeconfig`.
- **Talosconfig:** Generated cluster configs live under `/workspaces/k8s-gitops/bootstrap/talos/clusterconfig/` (or `~/.talos/config` if configured).
- **GitHub API:** Prefer `gh api` over unauthenticated `curl` to `api.github.com` to avoid rate limits.

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
- **Worktree-safe PR merging:** Use `gh pr merge <num> --squash` without `--delete-branch` when merging PRs whose branches may be checked out in another local worktree (GitHub auto-deletes remote branches; `--delete-branch` exits non-zero if a local worktree holds the branch).
- **Verify reconciliation completion:** Wait for `flux reconcile` / rollout commands to complete before reporting final status.

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

### Ceph Stale Crash Reports (`CephDaemonCrash`)
- If `CephDaemonCrash` or `CephHealthWarning` is firing due to already-recovered daemon crashes (e.g., a monitor failover that Rook already replaced), inspect and archive them after confirming storage/quorum health:
  ```bash
  kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph crash ls-new
  kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph crash info <crash-id>
  # After confirming root cause and user approval:
  kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph crash archive-all
  ```

### Stale DevPod Cleanup
- Standalone pods in the `devpod` namespace terminated by node reboots (`Pod was terminated in response to imminent node shutdown`) remain in `Error` state indefinitely.
- Safely delete failed pods using:
  ```bash
  kubectl -n devpod delete pod --field-selector=status.phase=Failed
  ```
  Their associated PersistentVolumeClaims remain `Bound` and preserved.

### Prometheus TSDB `ENOSPC` Compaction Deadlock
- If Prometheus alerts on `PrometheusTSDBCompactionsFailing` / `PrometheusNotIngestingSamples` with `no space left on device` on its PVC:
  1. Ensure `retentionSize` is set below PVC capacity in `kubernetes/monitoring/prod/kube-prometheus-stack/release.yaml` (via GitOps PR + Flux reconciliation).
  2. Live config reload alone may not break an active `ENOSPC` compaction deadlock; restart the pod once the config is applied so startup TSDB retention pruning frees space:
     ```bash
     kubectl -n monitoring delete pod prometheus-kube-prometheus-stack-prometheus-0
     kubectl -n monitoring rollout status sts/prometheus-kube-prometheus-stack-prometheus --timeout=3m
     ```
