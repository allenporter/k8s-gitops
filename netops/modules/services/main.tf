resource "dns_cname_record" "dns_cnames" {
  zone = var.dns_zone
  for_each = var.services
  name = format("%s.%s", each.key, var.dns_env)
  cname = format("%s.%s", each.value, var.dns_zone)
  # Fairly short ttl since these are dynamic hosts
  ttl = 300
}
