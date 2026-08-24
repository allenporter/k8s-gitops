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
