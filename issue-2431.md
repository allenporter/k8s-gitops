# Issue #2431: Upgrade Talos and Kubernetes

This file is a local record of the upgrade plans, roadmap, and progress tracking for Issue #2431.

## Cluster Information (Initial State)
- **Talos OS Version:** `v1.11.6`
- **Kubernetes Version:** `v1.33.6`
- **Control Plane Nodes:** `kapi01`, `kapi02`, `kapi03` (IPs: `10.10.100.1` - `10.10.100.3`)
- **Worker Nodes:** `kube01` (IP: `10.10.100.4`)

---

## Upgrade Roadmap

To upgrade safely without skipping major/minor releases, we will follow this path:

| Phase | Component | Action | Target Version | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | Talos OS | Upgrade OS | `v1.12.5` | [ ] Pending |
| **Phase 2** | Kubernetes | Upgrade Cluster | `v1.34.9` | [ ] Pending |
| **Phase 3** | Kubernetes | Upgrade Cluster | `v1.35.6` | [ ] Pending |
| **Phase 4** | Talos OS | Upgrade OS | `v1.13.6` | [ ] Pending |
| **Phase 5** | Kubernetes | Upgrade Cluster | `v1.36.2` | [ ] Pending |

---

## CRD Updates

Renovate has updated the source files under `hack/localize/` for:
- `external-snapshotter` to `v8.6.0`
- `prometheus-operator` to `v0.92.0`

We will run the localization script (`hack/localize/localize.sh`) to generate the corresponding files under `kubernetes/crds/` and commit them to Git.

---

## Progress Log

- **2026-07-11:** Initial research completed. Upgrades will start with Talos OS `v1.12.5`. Implementation plan generated and approved.
- **2026-07-11:** Created Git branch `upgrade/talos-v1.12`. Upgraded `talconf.yaml` to Talos `v1.12.5` and converted old JSON6902 patches to Strategic Merge Patches. Ran `talhelper genconfig` and localized updated CRDs (`external-snapshotter` to `v8.6.0`, `prometheus-operator` to `v0.92.0`). Ready for user diff review.
