# netops

Tooling and declarative configuration for the EdgeOS perimeter router.

## GitOps Workflow (`netops/edgeos.py`)

Router host/IP and variables live in `netops/inventory/hosts.yaml`, and desired configuration lives in `netops/roles/edgeos-config/templates/edgeos-rtr01.cfg.j2`.

```bash
# 1. Render desired config from Git (masks secrets if SOPS_AGE_KEY_FILE is unset)
uv run netops/edgeos.py render

# 2. Diff live router configuration against Git desired state
uv run netops/edgeos.py diff

# 3. Apply a reviewed file of set/delete commands with 5-minute commit-confirm + smoke tests
uv run netops/edgeos.py apply --commands-file /tmp/changes.cfg --minutes 5
```

### How `commit-confirm` Works
`edgeos.py apply` uses EdgeOS's built-in `commit-confirm` dead-man's switch to prevent lockouts:
1. **Back up** the live config locally before making any changes.
2. **Arm a rollback timer** (`--minutes 5`) on the router *before* committing — if the timer expires without confirmation, the router automatically reboots back into its last saved `/config/config.boot`.
3. **Commit** the staged `set`/`delete` changes to the running config (without saving to flash yet).
4. **Run automated smoke tests** (fresh SSH login, outbound HTTPS egress, and internal DNS/WAN checks).
5. **Confirm & save** only if every smoke test passes (canceling the reboot timer and persisting to `/config/config.boot`). If any test fails or connectivity drops, the script stops and lets the router auto-revert.

*(Pass `--ssh-host <user@host>` if you use a custom SSH host alias or user.)*

## Updating DHCP hosts

1. Update `machinedb/machines-catalog.yaml` and enter mac address
2. Manually update DNS server (for now) w/ forward and reverse records
