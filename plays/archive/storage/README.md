
# Ceph

1. Configure the network
1. Provision the storage
1. Create the osd rules

```
$ ceph osd crush rule create-replicated "default-hdd-rule" "default" "host" "hdd"
$ ceph osd pool set "kube-pool" crush_rule "default-hdd-rule"
```


