output "node_id" {
  value = {
    for instance in proxmox_virtual_environment_vm.proxmox-vmm:
      instance.name => element(split("/", instance.id), 2)
  }
}
