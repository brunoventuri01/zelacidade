# Estimativa de custos

## Configuração atual

| Componente | Plano | Estimativa atual |
|---|---|---|
| Azure App Service Plan | Linux F1 | Sem cobrança enquanto permanecer dentro do plano gratuito |
| Azure Web App | Vinculado ao F1 | Incluído no plano |
| GitHub Container Registry | Repositório público | Sem custo previsto para o volume acadêmico |
| GitHub Actions | Repositório público | Sem custo previsto para o volume acadêmico |
| Azure Monitor | Métricas de plataforma e dois alertas | Uso acadêmico mínimo; acompanhar a tela de custos da assinatura |

Não há VM, disco gerenciado, IP público dedicado ou banco de dados provisionado nesta etapa. Portanto, esses itens não geram custo agora.

## Controle de custo

- manter o App Service no SKU `F1`;
- não criar recursos manualmente fora do Terraform;
- revisar `terraform plan` antes de cada `apply`;
- configurar orçamento/alerta de custo se a assinatura disponibilizar o recurso;
- reavaliar custo ao integrar banco, armazenamento de fotos ou outros serviços do MVP.

Valores comerciais podem mudar e devem ser confirmados na calculadora oficial do Azure antes de qualquer migração para plano pago.

