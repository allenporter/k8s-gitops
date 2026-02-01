# Supernote

[Supernote Lite](https://github.com/allenporter/supernote-lite) is a self hosted private cloud service for the supernote notebook.


## Create Admin user

First install the supernote CLI locally, then create the first user which becomes the admin user.

```shell
$ uv pip install 'supernote[server]'
% supernote admin --url https://supernote.k8s.mrv.thebends.org user add email@example.com
```

Registration is closed after this.

```shell
supernote cloud-login email@example.com --url https://supernote.k8s.mrv.thebends.org
# Now your creds will be remembered by default
supernote admin user list
```

Output:
```
Total Users: 1

Email                          Name                 Capacity
-----------------------------------------------------------------
example@gmail.com              example              10737418240
```

## Backup & Restore

### Manual Backup

Trigger a manual backup:

```bash
kubectl patch replicationsource supernote-backup -n supernote --type=merge -p '{"spec":{"trigger":{"manual":"trigger-1"}}}'
```

### Restore Specific Snapshot (Optional)

By default, the restore job uses the latest snapshot. To choose a specific one:

1.  **List Snapshots**

    ```bash
    # Set up credentials from the cluster secret
    export RESTIC_PASSWORD=$(kubectl get secret -n supernote supernote-restic-config -o jsonpath="{.data.RESTIC_PASSWORD}" | base64 -d)
    export RESTIC_REPOSITORY=$(kubectl get secret -n supernote supernote-restic-config -o jsonpath="{.data.RESTIC_REPOSITORY}" | base64 -d)

    # List using existing gcloud secrets
    restic snapshots
    ```

2.  **Edit Configuration**

    Open `restore.yaml` and uncomment/update the `snapshot` field:

    ```yaml
    # snapshot: "a1b2c3d4"
    ```

### Restore for Inspection

To restore the latest backup to a separate PVC and inspect the contents:

1.  **Create Restore PVC**

    Create the destination PVC explicitly:

    ```bash
    kubectl apply -f kubernetes/iot/prod/supernote/restore-pvc.yaml
    ```

2.  **Apply the Restore Job**

    This will restore the latest snapshot into the PVC.

    ```bash
    kubectl apply -f kubernetes/iot/prod/supernote/restore.yaml
    ```

3.  **Wait for Completion**

    Check the status of the restore job:

    ```bash
    kubectl get ReplicationDestination -n supernote --watch
    ```

    Wait until `LAST SYNC` is populated.

3.  **Launch Debug Pod**

    Start a pod that mounts the restored PVC:

    ```bash
    kubectl apply -f kubernetes/iot/prod/supernote/debug-pod.yaml
    ```

4.  **Inspect Files**

    Exec into the pod to browse the files:

    ```bash
    kubectl exec -it -n supernote supernote-debug -- bash

    # Inside the pod:
    ls -la /data
    ```

5.  **Cleanup**

    When finished, remove the resources:

    ```bash
    kubectl delete -f debug-pod.yaml
    kubectl delete -f restore.yaml
    kubectl delete pvc -n supernote supernote-restore-data
    ```
