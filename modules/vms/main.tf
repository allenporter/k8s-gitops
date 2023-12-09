terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "0.39.0"
    }
  }
}

resource "proxmox_virtual_environment_vm" "proxmox-vmm" {
  for_each    = var.vms
  name        = each.key
  node_name   = each.value.target_node
  on_boot     = true

  initialization {
    datastore_id = "vm-pool"
    ip_config {
      ipv4 {
        address = format("ip=%s/16", each.value.ip)
        gateway = var.cloud_init.gateway
      }
    }
    dns {
      domain = var.cloud_init.searchdomain
      server = var.cloud_init.nameserver
    }
    user_account {
      username = var.cloud_init.provision_user
      keys = split("\n", var.cloud_init.provision_ssh_keys)
    }
  }

  cpu {
    cores  = lookup(each.value, "cpus", null)
  }
  memory{
    dedicated = lookup(each.value, "memory", 2048)
  }

  # Needed otherwise ubuntu-server hangs
  serial_device {
    device = "socket"
  }

  clone {
    vm_id = lookup(each.value, "clone_vm_id")
    full = false
  }

  disk {
    interface    = "scsi0"
    datastore_id = lookup(each.value, "disk_storage", "vm-pool") 
    size         = lookup(each.value, "disk_size", 200)
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
    ]
  }
}
