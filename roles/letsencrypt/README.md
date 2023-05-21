# letsencrypt

This role is used to generate certificates for the host. This is typically used by other roles
that need certificates for a particular service (e.g. proxmox webserver, haproxy, etc).

Expects the global `cert_dir` set and create certificates for the hostname in that
directory like:

  - `{{ inventory_hostname }}.pem` - Private key
  - `{{ inventory_hostname }}-fullchain.crt` - Fullchain certs
  - `{{ inventory_hostname }}-intermediate.crt` - Intermediate certs

Other roles can assume those files are set and use the cert for their purpose.
