# Registro de evidências

| Evidência | Estado |
|---|---|
| Docker Engine e Compose | Validado na VM |
| Health check público | HTTP 200 validado |
| Persistência PostgreSQL | Validada com ocorrência sintética |
| Endpoint Maker Lab | Autenticado 201; chave inválida 401 |
| Prometheus target da API | `up` validado |
| Dashboard das quatro métricas | Provisionado; captura pendente |
| Alerta funcional | Configurado; disparo controlado pendente |
| GitHub Actions | Pipeline real validada com análise de segurança, build e deploy |
| Terraform fmt/validate | Validado localmente |
| Terraform plan/apply | Não executado: credenciais CloudStack indisponíveis |
| HTTPS | Certificado Let’s Encrypt para o IP público; renovação automática |
