# Antigravity Workspace Rules (k8s-gitops)

## 1. Storage & Persistence Safety (Zero Unverified Deletions)
- NEVER execute destructive deletion commands (`rm -rf`) on paths mounted to Persistent Volume Claims (PVCs), `/workspaces`, or home directories (`~/.gemini`, `~/.config`, `~/.local`).
- If deprecated directories or configuration need cleanup, move them to a timestamped backup directory (`mv <path> <path>.bak.<timestamp>`) instead of deleting them.

## 2. Symlink Verification Protocol
- Before modifying, replacing, or removing any directory or symlink, trace the symlink graph in both directions:
  - Verify what the target points to: `ls -la <path>` / `readlink -f <path>`
  - Verify if other paths point to this target: `find / -lname "*<path_basename>*" 2>/dev/null`
- Never assume an older path or directory is "abandoned duplicate data" without verifying active file descriptors and symlink targets.

## 3. Treat Execution Errors as Safety Interlocks
- Never bypass filesystem safety errors (e.g., `Directory not empty`, `Permission denied`) by escalating to `sudo rm -rf`.
- Treat every deletion failure as a warning that live files or subdirectories are present. Stop and inspect the tree before proceeding.

## 4. Single-Target Staging (Blast Radius Control)
- Never batch destructive or structural changes across all containers or environments in a single compound command.
- Apply and verify changes on a single isolated instance first before applying to others.

## 5. Strict GitOps Invariant (Zero Out-of-Band Cluster Mutations)
- NEVER apply ad-hoc or temporary mutations directly to workloads or configuration via `kubectl apply` or `helm upgrade`.
- All operational and configuration changes must be made declaratively via Git (commit, PR, merge) and applied via Flux reconciliation (`flux reconcile ...`).

## 6. Secret & Git Staging Hygiene
- NEVER stage changes with broad `git add .` or `git add -A` without inspecting `git status`; always stage explicit file paths and ensure `kubeconfig`, `*.kubeconfig`, and `*.log` are never committed.

## 7. Fail-Closed Shell Mutations & Blast-Radius Preflight
- **Validate before mutating:** Whenever running or suggesting shell commands that mutate secrets, configs, firewall rules, DNS, or cluster state from captured variables, ALWAYS use `set -euo pipefail` and explicitly assert that values are non-empty and well-formed (`: "${VAR:?}"`, schema/cert/syntax checks) before writing. Never let a failed subcommand or parser mismatch silently overwrite live state with empty or malformed data.
- **Verify CLI tool flavor:** Never assume tool variants or flags across Linux/macOS (e.g., Go `yq` vs Python `yq`, GNU vs BSD `sed`/`grep`) without checking first or using portable syntax.
- **State blast radius up front:** Before recommending or executing PKI, network, firewall, or control-plane mutations (e.g., CA rotations, CNI/DNS changes, router rules), explicitly call out downstream side effects such as in-memory credential caching, required pod restarts, transient downtime, or lockout risks.
