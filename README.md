# ZelaCidade — Global Solution FIAP 2026.2

> Integrantes: **Bruno Venturi Lopes Vieira — RM 99431**, **Guilherme Alves de Lima — RM 550433** e **Leonardo de Oliveira Ruiz — RM 98901**

Plataforma colaborativa para registrar e acompanhar problemas urbanos, inicialmente focada em mobilidade, buracos e obstáculos.

## Arquitetura

```text
Internet :80/:443 -> CloudStack NAT/Firewall -> Nginx -> React
                                                   └-> FastAPI -> PostgreSQL
                                                       └-> /metrics <- Prometheus <- Node Exporter
                                                                      └-> Grafana
Robô Maker Lab -> X-API-Key -> POST /api/v1/robot/occurrences
```

## Tecnologias

Ubuntu 24.04 LTS, Docker Engine/Compose, React, FastAPI, PostgreSQL 16, Nginx, Prometheus, Grafana, Terraform CloudStack e GitHub Actions com Gitleaks, Semgrep e Trivy.

## Execução

```bash
cp .env.example .env
# substitua todos os CHANGE_ME por valores fortes
docker compose config -q
docker compose up -d --build
curl http://127.0.0.1/health
```

Nunca versione `.env`, `*.tfvars`, states ou chaves. PostgreSQL não possui porta publicada; Grafana e Prometheus estão em `127.0.0.1`.

## URLs do MVP

- Aplicação: https://200.187.67.91
- API/OpenAPI: https://200.187.67.91/docs
- Health: https://200.187.67.91/health

HTTPS usa certificado Let’s Encrypt emitido diretamente para o IPv4 público, com renovação automática. O HTTP redireciona para HTTPS.

## API

- `GET /health`
- `POST /api/v1/occurrences`
- `GET /api/v1/occurrences`
- `POST /api/v1/robot/occurrences` — exige `X-API-Key`

## CI/CD

`.github/workflows/ci.yml` executa testes, build, Gitleaks, Semgrep e Trivy. O deploy só ocorre na `main` após os jobs obrigatórios, usando runner self-hosted e ambiente `production`. Pull requests não executam deploy.

## Terraform

O diretório `terraform/` usa o provider CloudStack. A criação fica desabilitada por padrão e a configuração foi validada localmente. Como as credenciais CloudStack não estão disponíveis, `plan`, `apply` e provisionamento real não foram executados. A VM principal não é destruída nem recriada.

## Observabilidade

Prometheus coleta FastAPI e Node Exporter. O Grafana provisiona o dashboard das quatro métricas de ouro: latência, tráfego, erros e saturação. Interfaces administrativas não são públicas.

## Maker Lab e documentação

- `makerlab/README.md`: contrato e exemplo da API do robô.
- `docs/SECURITY.md`: segurança, responsabilidade compartilhada e LGPD.
- `docs/COSTS.md`: metodologia de custos.
- `docs/EVIDENCE.md`: evidências reais e pendências.

## Pendências externas

- Restringir SSH público e trocar senha temporária ao final.
- Fornecer credenciais CloudStack por canal seguro e autorizar eventual recurso de demonstração, caso a FIAP exija execução real do Terraform.
