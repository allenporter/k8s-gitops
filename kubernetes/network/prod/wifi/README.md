# unifi

## Restore

1. Take down the helm release and have a clean pvc
1. Check restore jobs (not started yet)

    ```bash
    $ kubectl get ReplicationDestination -n unifi
    No resources found in unifi namespace.
    ```

1. Add a restore job e.g. uncomment `unifi-restore.yaml` and update the timestamp
1. Examine the replica status

    ```bash
    $ kubectl get ReplicationDestination -n unifi
    NAME                          LAST SYNC   DURATION   NEXT SYNC
    unifi-restore-20241126-0706
    $ kubectl get pvc -n unifi
    NAME                                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS     VOLUMEATTRIBUTESCLASS   AGE
    unifi-shelf                                 Bound    pvc-efc8e9ae-b089-4b71-8079-bd79e999982f   3Gi        RWO            local-hostpath   <unset>                 18m
    volsync-unifi-restore-20241126-0706-cache   Bound    pvc-646b6fdb-afca-41ab-82ea-451e765a154b   1Gi        RWO            local-hostpath   <unset>                 43s
    ```

1. Examine restore job status

    ```bash
    $ kubectl describe ReplicationDestination -n unifi
    ...
    Latest Image:
        API Group:
        Kind:       PersistentVolumeClaim
        Name:       unifi-shelf
    Latest Mover Status:
        Logs:  restoring <Snapshot 7ae5bbe4 of [/data] at 2024-11-25 00:00:12.619177665 +0000 UTC by root@volsync> to .
    Restic completed in 30s
        Result:  Successful
    Events:
    Type    Reason                        Age   From                Message
    ----    ------                        ----  ----                -------
    Normal  PersistentVolumeClaimCreated  83s   volsync-controller  created PersistentVolumeClaim/volsync-unifi-restore-20241126-0706-cache to receive incoming data

    $ kubectl get ReplicationDestination -n unifi
    NAME                          LAST SYNC              DURATION        NEXT SYNC
    unifi-restore-20241126-0706   2024-11-26T15:09:25Z   35.466214524s
    ```
