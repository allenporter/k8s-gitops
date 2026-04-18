# Rook Ceph Storage

This directory contains the base configuration for deploying and managing the Rook Ceph storage operator and cluster.

## Troubleshooting

### Fixing a Corrupted Monitor (CrashLoopBackOff)

If a Rook Ceph Monitor pod (e.g., `rook-ceph-mon-c`) crashes continuously on startup and enters a `CrashLoopBackOff` state, it is likely due to a corrupted RocksDB database file on the host node. Because Rook monitors are stateful and use host networking/paths, simply deleting the Pod or Deployment does not clear the corrupt data.

**Symptoms inside the crashing monitor pod logs (`kubectl logs -n rook-ceph deployment/rook-ceph-mon-c -c mon --previous`):**

```
Corruption: block checksum mismatch: stored = ...
ceph_abort_msg("failed to write to db")
```

#### Recovery Procedure

To recover the monitor, you must manually delete its broken data directory on the host so that it can securely resync a fresh copy from the remaining healthy quorum monitors.

**1. Identify the Node**

Determine which node the crashing monitor is running on:

```bash
kubectl get pods -n rook-ceph -l app=rook-ceph-mon -o wide
# Example output will show it scheduled on something like 'kube01'
```

**2. Deploy a Temporary Cleanup Pod**
Create a YAML file (e.g., `clean-mon.yaml`) with a privileged container assigned specifically to that node to wipe the corrupted state. **Make sure to change `nodeName:` and the directory path `mon-c` to match your specific node and failing monitor:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mon-cleaner
  namespace: rook-ceph
spec:
  nodeName: kube01  # Replace with the node name from step 1
  volumes:
  - name: rook-data
    hostPath:
      path: /var/lib/rook  # The default Rook dataDirHostPath
  containers:
  - name: cleaner
    image: busybox
    # Verify the path matches the down monitor (e.g., mon-a, mon-b, mon-c)
    command: ["sh", "-c", "rm -rf /var/rook-data/mon-c/data/* || true; sleep 3600"]
    volumeMounts:
    - name: rook-data
      mountPath: /var/rook-data
```

**3. Run the Cleanup**

Apply the YAML to run the cleanup pod:

```bash
kubectl apply -f clean-mon.yaml
```

**4. Verify the Deletion (Optional)**

Check that the directory is empty:

```bash
kubectl exec -n rook-ceph mon-cleaner -- ls -la /var/rook-data/mon-c/data/
```

**5. Clean Up and Restart**

Delete the temporary cleaner pod, then delete the crashing monitor pod to trigger a fresh start:

```bash
kubectl delete pod mon-cleaner -n rook-ceph
# Be sure to target the correct mon label (e.g., mon=c)
kubectl delete pod -n rook-ceph -l app=rook-ceph-mon,mon=c
```

**6. Verify Sync**

Wait for the replacement pod to initialize and join the quorum. You can follow it with:

```bash
kubectl get pods -n rook-ceph -l app=rook-ceph-mon -w
```

It will take a couple of minutes to sync the database from its peers and return to a `Running` (2/2) status.
