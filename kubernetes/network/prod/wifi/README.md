# unifi

## Boostrap / Restore

1. Take down the helm release
1. Drop / re-create the PVC
1. Examine the replica status

```bash
$ kubectl get ReplicationDestination -n unifi unifi-restore-20241126
```
