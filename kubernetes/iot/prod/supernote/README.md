# Supernote

[Supernote Lite](https://github.com/allenporter/supernote-lite) is a self hosted private cloud service for the supernote notebook.


## Generate configuration

```shell
% supernote-server config init 
```

You'll need to include this `/config/config.yaml` in the container. I recommend updating the storage dir to point to a pvc e.g. `/data`

```yaml
# Generated Supernote Server Configuration
# Save this as config.yaml.
auth:
  expiration_hours: 24
  secret_key: <abcef>
  users_file: /config/users.yaml
host: 0.0.0.0
port: 8080
storage_dir: /data
trace_log_file: /data/server_trace.log
```

## Generate users

```shell
% supernote-server user add alice
Password for alice: 
```

You'll need to include this `/config/users.yaml` in the container:

```yaml
# Generated Supernote User Entry
# Append this to your users.yaml file.
users:
- avatar: null
  devices: []
  email: null
  is_active: true
  mobile: null
  password_md5: <password md5>
  profile: {}
  signature: null
  username: alice
```
