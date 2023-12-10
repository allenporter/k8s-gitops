# localize

The `kustomize localize` command can pull remote resources to local files,
so they can be pushed to the cluster. A copy of the remote resources are
copied into their final location in the cluster.

The setup here is that there is a copy of original `Kustomization` here
and the localize run will output to the right spot in the cluster. The
`localize.sh` script needs to be run each time any resources in this directory
change.