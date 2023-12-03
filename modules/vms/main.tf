terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "0.39.0"
    }
  }
}

resource "proxmox_vm_qemu" "proxmox-vmm" {
  for_each    = var.vms
  name        = each.key
  target_node = each.value.target_node
  clone       = lookup(each.value, "clone", "ubuntu-template")
  full_clone  = false
  clone_wait  = 15
  onboot      = true
  oncreate    = true
  tablet      = false  # Reduces CPU usage

  os_type      = "cloud-init"
  ipconfig0    = format("ip=%s/16,gw=%s", each.value.ip, var.cloud_init.gateway)
  nameserver   = var.cloud_init.nameserver
  searchdomain = var.cloud_init.searchdomain
  ciuser       = var.cloud_init.provision_user
  sshkeys      = var.cloud_init.provision_ssh_keys

  # Operator must manually apply changes
  automatic_reboot = lookup(each.value, "automatic_reboot", true)

  cores  = lookup(each.value, "cpus", null)
  memory = lookup(each.value, "memory", 2048)

  # Specified explicitly so that it does not always show as an update
  bootdisk = "scsi0"
  scsihw   = "virtio-scsi-pci"

  # Needed otherwise ubuntu-server hangs
  serial {
    id   = 0
    type = "socket"
  }

  disk {
    type         = "scsi"
    storage      = lookup(each.value, "disk_storage", "vm-pool")
    size         = lookup(each.value, "disk_size", "200G")
    backup       = true
    discard      = "on"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get install python3"
    ]

    connection {
      type  = "ssh"
      host  = each.value.ip
      user  = var.cloud_init.provision_user
      agent = true
    }
  }

  # Workaround: variables that change every time
  lifecycle {
    ignore_changes = [
      network,
      qemu_os,
      startup,
    ]
  }
}
