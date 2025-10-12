# netops

Tooling for deploying the network.

## Updating

```bash
$ export ANSIBLE_CONFIG=netops/ansible.cfg
$ ansible-playbook netops/rtr.yaml
```

## Updating DHCP hosts

1. Update `machinedb/machines-catalog.yaml` and enter mac address
1. Manually update DNS server (for now) w/ forward and reverse records
