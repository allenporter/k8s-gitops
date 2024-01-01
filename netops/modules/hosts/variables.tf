variable "dns_zone" {
  description = "DNS zone for all registere dhostnames, ends in ."
  type = string
}

variable "reverse_zone" {
  description = "The reverse name ip dns zone.  Must match the host ips."
  type = string
}

variable "hosts" {
  description = "Collection of hostnames for DNS management"
  type = map
  # The key is used as a hostname with the 'ip' field as the ip to resolve
}
