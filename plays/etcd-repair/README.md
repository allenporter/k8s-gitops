# etcd

Everything in this project is related to provisioning etcd.  This should
be a one-time event, then etcd can be used for kubernets, a terraform backend
or whatever.

# Replace

This is for replacing an entire node with a new machine.

See instructions at [Runtime reconfiguration](https://etcd.io/docs/v3.3.12/op-guide/runtime-configuration/#cluster-reconfiguration-operations)
to repair/replace a failed node.

1. Remove a member, e.g. `etcdctl member remove ...`
1. Turn down the old by removing from terraform
1. Allocate a hostname
1. Update dns e.g. cfg01 to point to new host
1. Provision a new vm with terraform
1. Configure the host with ansible e.g. `$ ansible-playbook plays/cfg.yml -l xxxx.prod` to install the services
1. Generate the join command e.g. `$ ansible-playbook plays/cfg-provision.yml -l xxxx.prod` which will print out the commannd e.g. `etcdctl member add ...` to run

# Repair in place

This is for repairing a node that is crashing, with a new database.

See instructions at [Runtime reconfiguration](https://etcd.io/docs/v3.3.12/op-guide/runtime-configuration/#cluster-reconfiguration-operations)

1. `etcdctl member list` to list the current set of members
1. `etcdctl endpoint status` to config the busted node
1. Wipe and replace the downed node
```
$ HOST=cfg01.prod
$ TARGET=afe353c38c8793b5
$ ansible-playbook rebuild-etcd.yml -l ${HOST} --extra-vars "target=${TARGET}"
```
1. Should be all good!


# Replace cluster

This is how to replace a node when the cluster entirely fails and can't get
quorom. This requires one host is still active. Every host must be replaced.

```
ACTIVE_HOST=cfg01.prod:2379
etcd-snapshot.sh ${ACTIVE_HOST}
```
The script reports the name of the snapshot.

Distribute the snapshot to the host to repair. Start with the host you just copied the snapshot from.
```
RESTORE_HOST=cfg01.prod
TOKEN=some-cluster-token

# Copy snapshot
etcd-distribute-snapshot.sh /some/file ${RESTORE_HOST}

# Run the output command the script tells you
ssh ${RESTORE_HOST} sudo ./etcd-restore-snapshot.sh file ${TOKEN}
```

