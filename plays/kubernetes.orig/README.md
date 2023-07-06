# Kubernetes

## Intro

These playbooks were written using the kubernes docs (ugh) as well as [Kubernetes Setup Using Ansible and Vagrant](https://kubernetes.io/blog/2019/03/15/kubernetes-setup-using-ansible-and-vagrant/)
however, this doesn't and some of the other unnecessary stuff.

This uses a standalone etcd cluster.  The set up of the cluster does not
bother setting up certs, and instead assumes strict firewall rules effectively
using host authentication and preventing ip spoofing.

## Update Packages

```
$ prod
$ ansible-playbook cluster/kubernetes/verify-kubernetes.yml
```

## Provision

First attempt to build the root node, then repeat the steps for other
control plane nodes or worker nodes.

Add vm via teraform then configure with ansible:
```
$ prod
$ HOST="kapi01.${ENV}"
$ ansible-playbook hosts/common.yml -l $HOST
$ ansible-playbook cluster/kubernetes/verify-kubernetes.yml -l $HOST,localhost
```

If a root node:
```
$ ansible-playbook cluster/kubernetes/provision-kapi-root.yml -l kapi01.${ENV}
```

If another control plane node. You have to include the root node to have a join cmd:
```
$ ansible-playbook cluster/kubernetes/provision.yml -l $HOST,kapi01.${ENV}
```

You will need to refresh the join command:
```
$ ansible-playbook cluster/kubernetes/provision-refresh-join-cmd.yml -l kapi01.${ENV}
```

Verify:
```
$ kubectl version
$ kubectl cluster-info
$ kubectl get nodes
$ kubectl get pods -n kube-system
```

Verify the control plane proxy has connections to the new backends
http://prx01.prod:8404/stats
