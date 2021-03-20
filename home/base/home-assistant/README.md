# Home Assistnat

# Config

Configuration is stored in github, and needs an ssh key.
```
$ scripts/git-key.sh git-creds home-assistant
```

Then in vscode
```
REPO=[my repo]
git init
git remote add origin $REPO
git fetch
git checkout origin/master -ft
```
