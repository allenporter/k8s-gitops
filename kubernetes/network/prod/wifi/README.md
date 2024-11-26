# unifi

## Boostrap / Restore

1. Take down the helm release
1. Drop / re-create the PVC

1. Check restore jobs

```bash
$ kubectl get ReplicationDestination -n unifi
No resources found in unifi namespace.
```
1. Add a restore job e.g. uncomment `unifi-restore.yaml` and update the timestamp
1. Examine the replica status

```bash
$ kubectl get ReplicationDestination -n unifi unifi-restore-20241126
```
