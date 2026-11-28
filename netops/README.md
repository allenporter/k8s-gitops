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

*(Pass `--ssh-host <user@host>` if you use a custom SSH host alias or user.)*

## Updating DHCP hosts

1. Update `machinedb/machines-catalog.yaml` and enter mac address
2. Manually update DNS server (for now) w/ forward and reverse records
