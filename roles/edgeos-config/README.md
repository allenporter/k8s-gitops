# edgeos-config

This play managines the configuration for the edgerouter x. This page below also describes the initial setup for managing an edgerouter via ansible.

## EdgeRouter X

### Load SSH Keys

You only need to do this the first time you need to load a new ssh key. You
can add SSH keys via the .cfg file and push with ansible.

On host machine:
```
$ scp ~/.ssh/id_rsa.pub <server>:
```

On router:
```
$ configure
# loadkey <user> id_rsa.pub
# commit
# save
# exit
```

Don't forget to add the ssh key to the config file.