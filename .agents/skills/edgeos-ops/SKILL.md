---
name: edgeos-ops
description: GitOps-first procedures for inspecting, diffing, safely applying (commit-confirm), smoke-testing, and recovering EdgeOS router configuration via netops/.
---

# EdgeOS Router Operations

GitOps-first runbook for managing the EdgeOS router defined in `netops/inventory/hosts.yaml` and `netops/roles/edgeos-config/templates/edgeos-rtr01.cfg.j2`.

## Core Safety Rules
1. **Git is the source of truth:** Declare configuration changes in `netops/roles/edgeos-config/templates/edgeos-rtr01.cfg.j2` (and `netops/inventory/hosts.yaml`) on a branch/PR **first**, diff against the live router, then apply only the reviewed delta.
2. **Never push legacy `netops/rtr.yaml` blindly:** The legacy Ansible `edgeos_config` role does not support `commit-confirm`. Use `netops/edgeos.py` instead.
3. **Always back up before mutating:** Ensure an off-router backup of `/config/config.boot` exists before changing firewall, interface, SSH, NAT, or DHCP settings. Never commit `/config/config.boot` or plaintext secrets to Git.
4. **Always use `commit-confirm`:** Never run bare `vyatta-cfg-cmd-wrapper commit` for firewall, SSH, interface, DNS, or NAT changes.
5. **Never change LAN interface IPs, DHCP subnets, SSH `listen-address`, or router firmware remotely** without explicit user approval and physical access available.

---

## Standard GitOps Workflow

Use `netops/edgeos.py` (reads router IP and variables directly from `netops/inventory/hosts.yaml`):

### 1. Check Drift (Read-Only)
```bash
uv run netops/edgeos.py render
uv run netops/edgeos.py diff
```
*(Secret fields are automatically redacted during `render`/`diff` when `SOPS_AGE_KEY_FILE` is unset. Pass `--ssh-host <alias>` if using a custom SSH config entry.)*

### 2. Preview & Apply a Reviewed Delta (`--dry-run` → `commit-confirm` + Smoke Tests)
Put the exact reviewed `set`/`delete` commands derived from your Git change into a temporary file (e.g., `/tmp/edgeos-changes.cfg`) and preview first:

```bash
# Preview EdgeOS's own context diff without committing
uv run netops/edgeos.py apply --commands-file /tmp/edgeos-changes.cfg --dry-run

# Apply with 5-minute commit-confirm rollback + automated smoke tests
uv run netops/edgeos.py apply --commands-file /tmp/edgeos-changes.cfg --minutes 5
```

What `netops/edgeos.py apply` enforces automatically:
1. Saves a timestamped `0600` pre-change backup to `~/.config/edgeos/backups/`.
2. Aborts if another `commit-confirm` is already pending, then arms EdgeOS's auto-rollback timer via PTY (`ssh -tt` + `/opt/vyatta/sbin/vyatta-config-mgmt.pl --action=commit-confirm`) before running `vyatta-cfg-cmd-wrapper commit` (and disarms the timer if `commit` itself fails).
3. Runs post-commit smoke tests (fresh `BatchMode` SSH session, outbound HTTPS egress, direct UDP DNS query to `<router-ip>:53`, and WAN interface UP).
4. Runs `confirm` and `save` **only if all smoke tests pass**; otherwise aborts and lets the timer revert the router automatically.

### 3. Direct Read-Only Inspection (When Needed)
Non-interactive SSH on EdgeOS requires `/opt/vyatta/bin/vyatta-op-cmd-wrapper` for `show` commands:
```bash
ssh admin@<router-ip> '/opt/vyatta/bin/vyatta-op-cmd-wrapper show version'
ssh admin@<router-ip> '/opt/vyatta/bin/vyatta-op-cmd-wrapper show interfaces ethernet eth0'
```

---

## Recovery Ladder

1. **Locked out before `confirm`:** Wait for the `commit-confirm` timer (default 5 minutes) — EdgeOS automatically reboots back to the last saved `/config/config.boot`.
2. **Still have SSH/GUI, but broke connectivity:** Roll back from `/config/archive/` (`commit-revisions 50`):
   ```text
   show system commit
   configure
   rollback 1
   commit
   save
   ```
3. **Saved a broken config and lost LAN access:** Physically factory-reset the EdgeRouter (hold Reset ~10s until LED flashes and goes solid → defaults to `192.168.1.1`, `ubnt`/`ubnt` on `eth0`), connect a laptop with `192.168.1.2/24` to `eth0`, and restore the off-router `config.boot` backup.
