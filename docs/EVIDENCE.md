# Registro final de evidencias

Atualizado em 15/11/2026. Todos os itens abaixo foram executados e verificados.

| Criterio | Evidencia | Estado |
|---|---|---|
| Repositorio publico | <https://github.com/brunoventuri01/zelacidade> | Concluido |
| PR do MVP oficial | <https://github.com/brunoventuri01/zelacidade/pull/2> | Mesclada |
| Pipeline final e deploy | <https://github.com/brunoventuri01/zelacidade/actions/runs/43790913541> | Concluido |
| Terraform `fmt` e `validate` | Job `terraform-validate` da execucao final | Concluido |
| Build e smoke test | Jobs `test-and-build` e `deploy-azure` | Concluido |
| Gitleaks, Semgrep e Trivy | Gates verdes na execucao final | Concluido |
| Execucao barrada | <https://github.com/brunoventuri01/zelacidade/actions/runs/42637898515> | Concluido |
| Correcao comprovada | <https://github.com/brunoventuri01/zelacidade/actions/runs/42638080332> | Concluido |
| MVP HTTPS | <https://app-zelacidade-gs-99431.azurewebsites.net> | HTTP 200 |
| Health check | `/health`: aplicacao, banco e visao operacionais | Concluido |
| Metricas | `/metrics` e metricas de plataforma do Azure Monitor | Concluido |
| Dados do MVP | 200 ocorrencias simuladas no Neon | Concluido |
| Maker Lab | Registro do Roberto: protocolo `ZC-000201` | Concluido |
| Alerta 5xx | `alert-zelacidade-http5xx` | Ativo |
| Alerta controlado | `alert-zelacidade-traffic-evidence` | Disparado (`Unhealthy`) |

## Evidencia do alerta disparado

Em 15/11/2026, a consulta ao endpoint de estado da regra no Azure Resource Manager
retornou `status: Unhealthy` para `alert-zelacidade-traffic-evidence`, com timestamp
`2026-11-13T16:38:32.338Z`. Em alertas de metrica do Azure, esse estado significa
que a condicao configurada foi atingida. A regra controlada monitora `Requests > 0`,
com janela de uma hora e avaliacao a cada minuto. A regra operacional de HTTP 5xx
permanece separada e ativa.

## Resultado observado no deploy final

- commit implantado: `1b1ec2855312dbcdcf8d4e60af9ef488a1f9891b`;
- pipeline: sucesso em todos os seis jobs;
- `/health`: `status=ok`, `banco=ok`, `visao=true`;
- `/metrics`: HTTP 200;
- mapa: 201 ocorrencias exibidas;
- teste do Roberto: status `recebida` e protocolo `ZC-000201`.

## Teste de segredo

A PR de evidencia utilizou somente um valor sintetico e invalido em branch isolada. O Gitleaks bloqueou a execucao. A branch foi reescrita sem o valor e passou nos mesmos gates. Nenhum segredo real foi usado.

