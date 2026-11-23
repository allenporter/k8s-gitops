---
name: supernote-ops
description: Runbook for Open Private Cloud for Supernote operations in k8s-gitops — version checks, stable and local Zot dev-build updates, VolSync backup verification, and syncing upstream Prometheus rules and Grafana dashboards.
---

# Supernote Operations Runbook

Use this skill when checking Supernote versions, deploying stable or dev builds, verifying/triggering backups, or updating Prometheus rules and Grafana dashboards for Open Private Cloud for Supernote (`allenporter/supernote`).

All manifests live in `kubernetes/iot/prod/supernote/`. Ensure `KUBECONFIG` is set (defaults to `/workspaces/k8s-gitops/kubeconfig` if unset).

---

## 1. Check Current Version vs. Upstream

Compare the deployed image in Git, the running pod in-cluster, and the latest GitHub release/commits:

```bash
# 1. Configured image in Git
grep -A 2 'image:' kubernetes/iot/prod/supernote/release.yaml

# 2. Running image in-cluster
kubectl -n supernote get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'

# 3. Latest upstream release & recent commits on main
gh release view --repo allenporter/supernote --json tagName,publishedAt,url
gh api repos/allenporter/supernote/commits/main --jq '{sha: .sha[0:7], date: .commit.committer.date, message: (.commit.message | split("\n")[0])}'
```

---

## 2. Update to a Stable Release

1. Update `spec.values.controllers.main.containers.main.image` in `kubernetes/iot/prod/supernote/release.yaml`:
   ```yaml
   image:
     repository: ghcr.io/allenporter/supernote
     tag: vX.Y.Z
   ```
2. Commit on a branch, open a PR, and merge (strict GitOps — never patch the live deployment directly).
   - Note: In a git worktree, run `gh pr merge <num> --squash` without `--delete-branch` to avoid local branch-cleanup errors.
3. Reconcile Flux and verify rollout:
   ```bash
   flux reconcile kustomization iot --with-source
   flux reconcile helmrelease supernote -n supernote
   kubectl -n supernote rollout status deploy/supernote --timeout=2m
   ```

---

## 3. Build & Deploy a Local Dev Build (Zot Registry)

To test `allenporter/supernote` from `main` without cutting a GitHub release (see `kubernetes/iot/prod/supernote/README.md` for details):

1. **Trigger the in-cluster builder job** (builds `Dockerfile` from `GIT_REF`, default `main`, and pushes `:dev` and `:<short-sha>` to `registry.k8s.mrv.thebends.org/allenporter/supernote`):
   ```bash
   kubectl delete job build-supernote-manual -n supernote --ignore-not-found=true
   kubectl create job --from=cronjob/build-supernote build-supernote-manual -n supernote
   kubectl logs -n supernote job/build-supernote-manual -c builder -f
   ```
2. **Pin the `<short-sha>` tag** (preferred over mutable `dev`) in `kubernetes/iot/prod/supernote/release.yaml`:
   ```yaml
   image:
     repository: registry.${name_service_dns_domain}/allenporter/supernote
     tag: <short-sha>
   ```
3. Commit, open/merge a PR, and reconcile Flux (`iot` Kustomization and `supernote` HelmRelease).

---

## 4. Verify or Trigger Backups (VolSync)

Supernote data is backed up daily at `01:00` via VolSync `ReplicationSource/supernote-backup` (`kubernetes/iot/prod/supernote/backup.yaml`) to Restic/GCS (`supernote-restic-config`).

```bash
# Check last sync time, duration, next sync, and conditions
kubectl -n supernote get replicationsource supernote-backup -o wide
kubectl -n supernote describe replicationsource supernote-backup

# Check recent backup mover jobs/pods
kubectl -n supernote get jobs,pods -l app.kubernetes.io/created-by=volsync
```

To trigger an on-demand backup:
```bash
kubectl patch replicationsource supernote-backup -n supernote --type=merge \
  -p "{\"spec\":{\"trigger\":{\"manual\":\"manual-$(date +%Y%m%d%H%M)\"}}}"
```

---

## 5. Sync Upstream Monitoring (Prometheus Rules & Grafana Dashboard)

Monitoring assets are vendored in `kubernetes/iot/prod/supernote/` from `allenporter/supernote`:
- **Prometheus rules:** `kubernetes/iot/prod/supernote/prometheus-rules.yaml`
  - Must keep `metadata.labels.role: alert-rules` and `metadata.annotations["kustomize.toolkit.fluxcd.io/substitute"]: disabled` (so Flux does not try to expand PromQL `$labels` / `${...}`).
- **Grafana dashboard:** `kubernetes/iot/prod/supernote/supernote-dashboard.json`
  - Packaged via `configMapGenerator` in `kubernetes/iot/prod/supernote/kustomization.yaml` with `grafana_dashboard: "1"` and `kustomize.toolkit.fluxcd.io/substitute: disabled`.

After updating either file:
1. Validate with `kustomize build kubernetes/iot/prod/supernote > /dev/null`.
2. Commit, PR, merge, and reconcile `flux reconcile kustomization iot --with-source`.
3. Verify in-cluster:
   ```bash
   kubectl -n supernote get prometheusrule supernote-rules
   kubectl -n supernote get configmap -l grafana_dashboard=1
   ```
