variable "vms" {
  description = "vms to create/manage"
  type = map
}

variable "cloud_init" {
  description = "Cloud-init configuration"
  type = map
  # Should include these variables in the map
  # - gateway
  # - nameserver
  # - searchdomain
  # - provision_ssh_key
  # - provision_user
}
