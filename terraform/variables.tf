variable "cloudstack_api_url" { type = string }
variable "cloudstack_api_key" { type = string; sensitive = true }
variable "cloudstack_secret_key" { type = string; sensitive = true }
variable "zone" { type = string }
variable "network" { type = string }
variable "service_offering" { type = string }
variable "template" { type = string }
variable "ssh_keypair" { type = string }
variable "demo_instance_name" { type = string; default = "L-ZELACIDADE-TF-DEMO" }
variable "enable_demo_instance" { type = bool; default = false }
