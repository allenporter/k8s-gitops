# Nvidia device plugin

From [Testing the RuntimeClass](https://www.talos.dev/v1.8/talos-guides/configuration/nvidia-gpu-proprietary/#testing-the-runtime-class)

```bash
$ kubectl run nvidia-test \
    --restart=Never   -ti --rm \
    --image nvcr.io/nvidia/cuda:12.4.1-base-ubuntu22.04 \
    --overrides '{"spec": {"runtimeClassName": "nvidia"}}' \
    nvidia-smi
```
