# Estimativa de custos

Atualizada em 15/11/2026 para a configuracao efetivamente implantada.

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

O F1 nao possui SLA e e indicado somente para experimentacao e demonstracao. Ao exceder cotas ou migrar para producao, os primeiros itens a reavaliar sao o plano do App Service, o armazenamento e compute do Neon e a observabilidade. Qualquer mudanca deve ser calculada nas ferramentas oficiais e revisada em um novo `terraform plan`.

Fontes oficiais consultadas em 15/11/2026:

- <https://azure.microsoft.com/en-us/pricing/details/app-service/linux/>
- <https://azure.microsoft.com/en-us/pricing/details/monitor/>
- <https://neon.com/blog/neon-free-plan-1-gb-per-project>
- <https://docs.github.com/en/billing/concepts/product-billing/github-actions>
- <https://docs.github.com/en/billing/concepts/product-billing/github-packages>

