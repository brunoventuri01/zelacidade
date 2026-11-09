# Registro de evidências

Atualizado em 09/11/2026. Somente resultados efetivamente executados foram marcados como concluídos.

| Critério | Evidência verificável | Estado |
|---|---|---|
| Repositório público | <https://github.com/brunoventuri01/zelacidade> | Concluído |
| Terraform `fmt` e `validate` | Job `terraform-validate` da execução 42635724419 | Concluído |
| Terraform `plan` e `apply` | RG, App Service Plan, Web App e alertas presentes na assinatura FIAP | Concluído |
| URL pública HTTPS | <https://app-zelacidade-gs-99431.azurewebsites.net> retorna HTTP 200 | Concluído |
| Pipeline completa e deploy | <https://github.com/brunoventuri01/zelacidade/actions/runs/42635724419> | Concluído |
| Build e container | Imagem versionada por SHA no GHCR e implantada no App Service | Concluído |
| Gitleaks barrando segredo | Execução <https://github.com/brunoventuri01/zelacidade/actions/runs/42637898515> | Concluído |
| Correção após bloqueio | Execução <https://github.com/brunoventuri01/zelacidade/actions/runs/42638080332> | Concluído |
| Semgrep e Trivy | Jobs aprovados nas execuções acima | Concluído |
| Métricas de tráfego | Azure Monitor registrou picos de 12 e 60 requests/min no teste controlado | Concluído |
| Alerta HTTP 5xx | Criado por Terraform: `alert-zelacidade-http5xx` | Concluído |
| Alerta controlado | Criado por Terraform: `alert-zelacidade-traffic-evidence` | Concluído |
| MVP oficial | Imagem/contrato ainda não fornecidos pela equipe | **Pendente** |
| Testes funcionais do MVP | Dependem do MVP oficial | **Pendente** |

## Decisão de arquitetura

A assinatura FIAP é `Azure para Estudantes Starter` e bloqueia recursos de VM, rede e armazenamento que seriam necessários para uma VM convencional. O professor autorizou explicitamente seguir com Azure App Service criado por Terraform e priorizar o pipeline DevSecOps. O App Service atende com container, HTTPS e ausência de porta administrativa pública.

## Observação sobre o teste de segredo

A PR #1 usou um valor sintético em uma branch isolada. A execução foi barrada pelo Gitleaks; depois a branch foi reescrita a partir da `main` sem o valor, a execução corrigida passou e a PR foi encerrada sem merge. Nenhum segredo real foi utilizado.

