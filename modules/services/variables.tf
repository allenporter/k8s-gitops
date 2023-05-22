variable "dns_zone" {
  description = "DNS zone to update, ends with '.'"
  type = string
}

variable "dns_env" {
  description = "DNS 'env' like prod or dev mapped to the hostname."
  type = string
}

variable "services" {
  description = "Logical services that need production DNS records"
  type = map
}
