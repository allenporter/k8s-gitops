output "node_id" {
  value = {
    for instance in proxmox_vm_qemu.proxmox-vmm:
      instance.name => element(split("/", instance.id), 2)
  }
}
