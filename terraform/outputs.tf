output "demo_instance_id" { value = try(cloudstack_instance.demo[0].id, null) }
output "demo_private_ip" { value = try(cloudstack_instance.demo[0].ip_address, null) }
