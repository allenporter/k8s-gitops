resource "dns_a_record_set" "host_a_records" {
  for_each = var.hosts
  zone     = var.dns_zone
  name     = each.key
  addresses = [
    each.value
  ]
  # Fairly short ttl since these are dynamic hosts
  ttl = 300
}

resource "dns_ptr_record" "ip_ptr_records" {
  for_each = var.hosts
  # 10.10.X.X
  zone = var.reverse_zone
  name = format("%s.%s", element(split(".", each.value), 3), element(split(".", each.value), 2))
  ptr  = format("%s.%s", each.key, var.dns_zone)
  # Fairly short ttl since these are dynamic hosts
  ttl = 300
}
