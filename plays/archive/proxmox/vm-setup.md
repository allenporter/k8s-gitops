# VM Setup

## New Guest

These are the current steps to create a new guest:

1.  Create a hostname

        $ allocate_hostname

1.  Add the host to the terraform.tfvars file.
1.  Run terraform to create the guest VM in proxmox and all DNS records.

        $ terraform plan
        $ terraform apply

1.  Run ansible to install or update any base packages.

1. Done!

## Install Proxmox

1. Every VMM has proxmox installed, and an IP address configured with static IP
1. Every VM auto starts on boot

        $ pvesh create /nodes/crimson/startall

1. Add to the ansibble environments/
1. Add DNS setup to terraform config.
1. Repeat for each machine.  Set up a cluster if desired.

## Prepare Proxmox for Ansible

1. Update [Package repositories](https://pve.proxmox.com/wiki/Package_Repositories) unless you have a license
1. Update the ansible inventory file, including adding your ssh public key
1. Run provisioning  as root to create the user accounts (provioning_user above).
```
$ dev
$ ansible-playbook proxmox/vmm.yml --ask-pass -u root
```

Now you should have a user account on the remote machines.


## Create a new cloud-init template

See [Cloud-Init Support](https://pve.proxmox.com/wiki/Cloud-Init_Support) for
an example of how to create a template.

This is an example of manually cloning a VM:
```
$ qm clone 200 201 --name isabel
$ qm set 201 --ipconfig0 ip=192.168.87.41/24,gw=192.168.87.1 --nameserver=192.168.87.1 --searchdomain=thebends.org --ciuser=allen --sshkey ~allen/allen-thebends.pub
```

However, now this is automated with terraform/ansible.


# Restore from backup

1. Reinstall with same name/ip
1. Run the vmm.yml playbook above
1. Run the verify-vmm.yml playbook
1. ssh into the host and copy an auth key from another node
```
scp root@XXXX.prod:/etc/corosync/authkey /etc/corosync/authkey
```
1. While on the new host, list available backups:
```
ls /mnt/pve/vm-backup/hosts/*YYYY*
```
1. Restore a backup:
```
ansible-playbook -i environments/prod/hosts proxmox/vmm-restore.yml -l YYYY.prod
```
