---
name: edgeos-ops
description: Safe inspection, commit-confirm mutation, smoke-testing, and recovery procedures for the Ubiquiti EdgeRouter X (mineral / 10.10.1.1) running EdgeOS.
---

# EdgeOS Router Operations (`mineral` / `10.10.1.1`)

Runbook for inspecting and safely mutating the EdgeRouter X (`mineral`, `10.10.1.1`) without causing lockouts or losing connectivity.

## Core Safety Rules
1. **Never push `netops/rtr.yaml` blindly:** The legacy Ansible `edgeos_config` role does not use `commit-confirm` and may overwrite live router drift. Always inspect live config first and apply small, targeted changes.
2. **Always back up before mutating:** Ensure a recent copy of `/config/config.boot` exists off-router (e.g., on the user's laptop) before touching firewall, interface, SSH, NAT, or DHCP settings. Never commit `/config/config.boot` or plaintext secrets to Git.
3. **Always arm `commit-confirm` before `commit`:** Never run bare `vyatta-cfg-cmd-wrapper commit` for firewall, SSH, interface, DNS, or NAT changes.
4. **Never change `switch0` IP (`10.10.1.1/16`), DHCP, SSH `listen-address`, or firmware remotely** without explicit user approval and physical access available.
5. **Sync `netops/roles/edgeos-config/templates/edgeos-rtr01.cfg.j2`** in Git after any confirmed live change.

---

## Read-Only Inspection

Non-interactive SSH on EdgeOS requires `/opt/vyatta/bin/vyatta-op-cmd-wrapper` for operational (`show`) commands:

```bash
ssh mineral '/opt/vyatta/bin/vyatta-op-cmd-wrapper show version'
ssh mineral '/opt/vyatta/bin/vyatta-op-cmd-wrapper show interfaces ethernet eth0'
ssh mineral '/opt/vyatta/bin/vyatta-op-cmd-wrapper show configuration commands' \
  | grep -E '^(set firewall|set interfaces ethernet eth0|set port-forward|set service (gui|ssh|snmp)|set vpn|set system package)'
```

---

## Safe Mutation Procedure (`commit-confirm 5` + Smoke Tests)

> **Important EdgeOS detail:** `/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper` does **not** implement `commit-confirm`. Instead, `commit-confirm` is handled by `/opt/vyatta/sbin/vyatta-config-mgmt.pl --action=commit-confirm --minutes=5`, which requires a PTY (`ssh -tt`) for its `Proceed? [yes]` prompt.

### Step 1: Stage, Arm 5-Minute Rollback, and Commit
Upload a small script to `/tmp/edgeos-change.sh` on `mineral` and run it with `ssh -tt`:

```bash
ssh mineral 'cat > /tmp/edgeos-change.sh' <<'REMOTE'
#!/bin/bash
set -euo pipefail
sg vyattacfg -c '
set -euo pipefail
CMD=/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper
export CMD_WRAPPER_SESSION_ID=$$

$CMD begin
trap "$CMD end || true" EXIT

# --- Place targeted $CMD set / $CMD delete lines here ---

# Arm 5-minute auto-rollback before committing
sudo sg vyattacfg "/opt/vyatta/sbin/vyatta-config-mgmt.pl --action=commit-confirm --minutes=5"
$CMD commit
'
REMOTE
printf 'y\n' | ssh -tt mineral 'bash /tmp/edgeos-change.sh && rm -f /tmp/edgeos-change.sh'
```

### Step 2: Run Automated Smoke Tests *Before* Confirming
Only run `confirm` + `save` if **all** checks pass (guarded by `set -euo pipefail`; if any check fails, do **not** confirm — let the 5-minute timer revert automatically):

```bash
set -euo pipefail
# 1. Fresh SSH session
ssh -o ConnectTimeout=5 mineral 'echo SSH_OK'

# 2. Outbound internet HTTPS
WAN_IP="$(curl -fsS --max-time 5 https://checkip.amazonaws.com | tr -d '[:space:]')"
: "${WAN_IP:?Internet egress check failed}"

# 3. Internal DNS / cluster service
curl -fsS -o /dev/null https://registry.k8s.mrv.thebends.org/v2/

# 4. Assert expected config state via show configuration commands
# ...

# 5. Cancel rollback timer and persist to /config/config.boot
ssh mineral 'sudo sg vyattacfg "/opt/vyatta/sbin/vyatta-config-mgmt.pl --action=confirm" && sudo sg vyattacfg "/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper save"'
```

---

## Recovery Ladder

1. **Locked out before `confirm`:** Wait 5 minutes — EdgeOS automatically reboots back to the last saved `/config/config.boot`.
2. **Still have SSH/GUI, but broke internet/DNS/firewall:** Roll back using the 50 archived revisions in `/config/archive/`:
   ```text
   show system commit
   configure
   rollback 1
   commit
   save
   ```
3. **Saved a broken config and lost LAN access:** Physically hold the ER-X Reset button for ~10s until `eth4` flashes and goes solid (factory default `192.168.1.1`, `ubnt`/`ubnt` on `eth0`), connect a laptop with `192.168.1.2/24` to `eth0`, and restore the backed-up `config.boot`.
