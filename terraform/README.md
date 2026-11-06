# Terraform / CloudStack

`enable_demo_instance=false` e `prevent_destroy=true` impedem criação acidental e destruição. Forneça segredos por `TF_VAR_cloudstack_api_key` e `TF_VAR_cloudstack_secret_key`. A VM principal existente não é recriada por este módulo. Provisionamento real depende de credenciais seguras e autorização de custo.
