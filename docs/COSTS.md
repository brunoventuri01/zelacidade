# Estimativa de custos

Atualizada em 15/11/2026. A estimativa separa o prototipo academico efetivamente
implantado de um ambiente inicial de producao para uma empresa.

| Componente | Plano ou cota | Estimativa mensal |
|---|---|---:|
| Azure App Service | Linux F1: 60 minutos de CPU/dia, 1 GB de RAM e 1 GB de disco | US$ 0 |
| Azure Monitor | Metricas de plataforma e 2 series de alerta; primeiras 10 series gratuitas | US$ 0 |
| Neon PostgreSQL | Free: 1 GB por projeto, 100 CU-h/mes e scale-to-zero | US$ 0 |
| GitHub Actions | Runners padrao em repositorio publico | US$ 0 |
| GitHub Container Registry | Pacote publico | US$ 0 |
| Dominio e HTTPS | Subdominio `azurewebsites.net` e certificado gerenciado | US$ 0 |
| **Total atual** | Dentro das cotas gratuitas | **US$ 0/mes** |

Nao existem VM, disco gerenciado, IP publico dedicado, Kubernetes ou banco Azure no ambiente atual.

## Cenario empresarial inicial

Para uma operacao pequena, com baixo trafego, foi considerado um App Service Linux
B1 e um PostgreSQL Flexible Server B1ms com 32 GiB. GitHub Actions e GHCR continuam
sem custo enquanto o repositorio e o pacote forem publicos.

| Componente | Premissa de producao inicial | Estimativa mensal |
|---|---|---:|
| Azure App Service | Linux B1, 1 vCPU, 1,75 GB RAM, 10 GB | US$ 13,14 |
| PostgreSQL gerenciado | Flexible Server B1ms, 1 vCore, 2 GiB | US$ 12,41 |
| Armazenamento PostgreSQL | 32 GiB a US$ 0,115/GiB | US$ 3,68 |
| Azure Monitor | 2 series de alerta de metrica | US$ 0,20 |
| CI/CD e registro | GitHub Actions e GHCR publicos | US$ 0,00 |
| Dominio | Nao incluido; varia conforme o registrador | — |
| **Subtotal tecnico** | Sem dominio, impostos e trafego excedente | **US$ 29,43/mes** |
| **Orcamento recomendado** | Margem para logs, trafego e pequenas variacoes | **US$ 30–35/mes** |

Com cambio de referencia de R$ 5,40/US$, o orcamento equivale a aproximadamente
**R$ 162–189/mes**. O valor em reais e apenas uma conversao de planejamento; a
fatura depende do cambio, impostos, regiao e consumo. Esse cenario e um ponto de
partida, nao uma arquitetura de alta disponibilidade.

O F1 nao possui SLA e e indicado somente para experimentacao e demonstracao. A
migracao comercial deve ser aplicada por Terraform e validada por `terraform plan`.

Fontes oficiais consultadas em 15/11/2026:

- <https://azure.microsoft.com/en-us/pricing/details/app-service/linux/>
- <https://azure.microsoft.com/en-us/pricing/details/postgresql/flexible-server/>
- <https://azure.microsoft.com/en-us/pricing/details/monitor/>
- <https://neon.com/blog/neon-free-plan-1-gb-per-project>
- <https://docs.github.com/en/billing/concepts/product-billing/github-actions>
- <https://docs.github.com/en/billing/concepts/product-billing/github-packages>

