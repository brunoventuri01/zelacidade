terraform {
  required_version = ">= 1.8.0"
  required_providers {
    cloudstack = {
      source  = "cloudstack/cloudstack"
      version = "~> 0.5"
    }
  }
}
