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
