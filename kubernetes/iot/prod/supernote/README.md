# Supernote

[Supernote Personal Knowledge Management Hub](https://github.com/allenporter/supernote) is a self hosted private cloud service for the supernote notebook.


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

## Local Dev Build (Zot Registry)

To build `supernote` from GitHub (`main` or a branch) in-cluster and push it to the internal Zot registry (`registry.k8s.mrv.thebends.org/allenporter/supernote`) without cutting a public release:

1. **Trigger a Manual Build Job**

   ```bash
   kubectl delete job build-supernote-manual -n supernote --ignore-not-found=true
   kubectl create job --from=cronjob/build-supernote build-supernote-manual -n supernote
   ```

2. **Watch Build Logs**

   ```bash
   kubectl logs -n supernote job/build-supernote-manual -c builder -f
   ```

   This builds `Dockerfile` from `GIT_REF` (default `main`) and pushes both:
   - `registry.k8s.mrv.thebends.org/allenporter/supernote:dev`
   - `registry.k8s.mrv.thebends.org/allenporter/supernote:<short-sha>`

3. **Deploy Local Dev Image**

   Update `release.yaml` to point to the local registry image and tag:

   ```yaml
   image:
     repository: registry.${name_service_dns_domain}/allenporter/supernote
     tag: dev # or the <short-sha> printed by the build job
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
