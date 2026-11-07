resource "cloudstack_instance" "demo" {
  count            = var.enable_demo_instance ? 1 : 0
  name             = var.demo_instance_name
  display_name     = var.demo_instance_name
  zone             = var.zone
  network_id       = var.network
  service_offering = var.service_offering
  template         = var.template
  keypair          = var.ssh_keypair
  expunge          = false
  lifecycle {
    prevent_destroy = true
  }
}
