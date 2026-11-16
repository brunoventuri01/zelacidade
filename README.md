# ZelaCidade — Global Solution FIAP 2026.2

> Bruno Venturi Lopes Vieira — RM 99431  
> Guilherme Alves de Lima — RM 550433  
> Leonardo de Oliveira Ruiz — RM 98901

Plataforma colaborativa para identificar, organizar e acompanhar problemas em espaços públicos: o morador registra com foto e local, a IA de visão sugere a categoria, um robô faz a triagem e a organização responsável só marca como resolvido com foto da solução.

## Ficha técnica do ZelaCidade

| Item | Descrição |
|---|---|
| Nome | ZelaCidade |
| Cidadão e território | Moradores da Zona Norte de São Paulo, na área da Subprefeitura Santana/Tucuruvi: Santana, Jardim São Paulo, Mandaqui e Tucuruvi |
| Problema | Buracos, calçadas danificadas, iluminação apagada, obstáculos e lixo em espaços públicos ficam sem registro organizado, sem prioridade clara e sem retorno para quem avisou |
| Proposta de valor | Registrar leva cerca de 1 minuto, com foto e local; a IA sugere a categoria; a comunidade confirma; um robô faz a triagem com motivo explicável; a organização responsável vê primeiro o que é urgente e só fecha a ocorrência com foto da solução |
| Componentes | MVP web (FastAPI + React) · visão computacional (YOLO11n em ONNX) · assistente com base de documentos oficiais (IA generativa) · robô de triagem (RPA com BotCity) · pipeline de dados (Airflow + Databricks) · robô Maker Lab "Roberto" (Arduino com sensor de distância) · Azure com Terraform, CI/CD DevSecOps e monitoramento |
| Fontes de dados | Registros do MVP (moradores, robô Maker e dados simulados marcados como tal) · Open-Meteo (chuva e temperatura) · 47 trechos de 19 fontes oficiais (base do assistente) · Pothole Dataset do Roboflow (treino da visão) |
| Modelos de IA | YOLO11n ajustado para "buraco": mAP50 de 0,793 e, no limiar de 0,35, precisão de 0,79 e recall de 0,68 (67 imagens de teste) · modelo de linguagem local com recuperação de trechos oficiais (repo de GenAI) |
| Indicadores | Negócio: organizações em piloto, conversão de piloto para pago, receita recorrente mensal e cancelamentos. Impacto: ocorrências confirmadas, tempo médio de triagem, porcentagem resolvida com evidência e moradores ativos por mês |
| ODS | 11 (metas 11.3 e 11.7) e 9 (meta 9.1) |
| MVP | <https://app-zelacidade-gs-99431.azurewebsites.net> |
| Repositórios | MVP e nuvem: <https://github.com/brunoventuri01/zelacidade> · Big Data: <https://github.com/leooruiz/zelacidade-bigdata> · RPA: <https://github.com/leooruiz/zelacidade-rpa> · IA generativa: <https://github.com/GuiAlves2005/zelacidade-genai> · Visão computacional: <https://github.com/GuiAlves2005/zelacidade-cv> · Maker Lab: link a definir |

## Estado atual

A infraestrutura de produção está criada no Azure por Terraform, o pipeline está funcional e o monitoramento está ativo. A URL pública serve o MVP oficial: um único container com a API FastAPI e o site React, na porta 8000, usando Postgres no Neon.

- MVP: <https://app-zelacidade-gs-99431.azurewebsites.net>
- Repositório público: <https://github.com/brunoventuri01/zelacidade>
- Pipeline de produção validado: <https://github.com/brunoventuri01/zelacidade/actions/runs/42635724419>

## MVP: como rodar no PC

Pré-requisito: Docker com Compose.

```bash
cp .env.example .env          # troque os CHANGE_ME por valores locais
docker compose up --build     # sobe db (Postgres) + app em http://localhost:8000
docker compose exec app python -m app.seed --quantidade 200 --semente 42 --limpar   # dados simulados
```

Testes:

```bash
pip install -r backend/requirements-dev.txt
PYTHONPATH=backend pytest -q backend/tests
cd frontend && npm ci && npm test && npm run build
```

Desenvolvimento do site com recarga automática: rode a API (`DATABASE_URL=sqlite:///./local.db uvicorn app.main:app --app-dir backend`) e, em outro terminal, `cd frontend && npm run dev`.

### Estrutura

| Caminho | Conteúdo |
|---|---|
| `Dockerfile` | Imagem única: build do React → Python 3.12 slim, usuário não root, porta 8000, `HEALTHCHECK` em `/health` |
| `backend/app/` | API FastAPI, modelos SQLAlchemy, visão (ONNX), assistente, gerador de dados simulados |
| `backend/app/data/area_piloto.json` | Área piloto (Subprefeitura Santana/Tucuruvi): centro, limites, bairros e centro de cada bairro |
| `backend/models/visao/` | Modelo de visão do Guilherme (YOLO11n v1, classe `buraco`): `best.onnx`, `classes.json`, `config.json` |
| `backend/app/data/trechos.json` | 47 trechos oficiais da base do assistente, usados no modo offline |
| `backend/tests/` | Testes de contrato, LGPD, assistente e regressão do modelo (`tests/visao/`: 5 fotos + `esperado.json`) |
| `frontend/` | Site React (Vite): mapa, registro, detalhe, painel, assistente, gestão e privacidade |

### Contratos da API

A documentação interativa fica em `/docs`. Resumo:

| Quem chama | Endpoint | Autenticação |
|---|---|---|
| Site | `GET /api/v1/config`, `GET/POST /api/v1/ocorrencias`, `GET /api/v1/ocorrencias/{id}`, `POST /api/v1/ocorrencias/{id}/confirmacoes`, `GET /api/v1/fotos/{id}`, `POST /api/v1/ia/classificar`, `GET /api/v1/painel`, `POST /api/v1/assistente` | pública |
| Organização (gestão) | `GET /api/v1/gestao/ocorrencias`, `PATCH /api/v1/gestao/ocorrencias/{id}` | `Authorization: Bearer ADMIN_TOKEN` |
| Robô Maker Lab | `POST /api/v1/robot/occurrences` (resposta traz `protocolo` para o LCD) | `X-API-Key: ROBOT_API_KEY` |
| Robô RPA | `GET /api/v1/integracao/ocorrencias`, `PATCH /api/v1/integracao/ocorrencias/{id}/triagem`, `POST /api/v1/integracao/painel` | `X-API-Key: RPA_API_KEY` |
| Airflow (Big Data) | `GET /api/v1/export/ocorrencias?data=AAAA-MM-DD` (NDJSON) | `X-API-Key: EXPORT_API_KEY` |
| Operação | `GET /health`, `GET /metrics` | pública |

### Segurança e LGPD no MVP

- Credenciais só por variável de ambiente; `CHANGE_ME` ou vazio desliga a integração (HTTP 503).
- Fotos reduzidas para até 1280 px e regravadas sem EXIF (que pode conter GPS e aparelho).
- E-mail só com consentimento e nunca nas rotas públicas; o identificador do aparelho é guardado como hash.
- Cabeçalhos de segurança (CSP, `nosniff`, `Referrer-Policy`) e upload limitado a JPEG/PNG/WEBP de até 5 MB.
- Dados simulados têm `simulado=true`, selo na tela e filtro; a geração está documentada em `backend/app/seed.py`.

## Arquitetura

```mermaid
flowchart LR
    DEV[Equipe] -->|push / pull request| GH[GitHub]
    GH --> CI[Testes + build]
    CI --> SEC[Gitleaks + Semgrep + Trivy]
    SEC --> TF[Terraform validate]
    TF -->|main aprovada| REG[GitHub Container Registry]
    REG --> APP[Azure App Service Linux F1]
    USER[Usuário HTTPS] --> APP
    APP --> MON[Azure Monitor: métricas e alertas]
    TF2[Terraform] --> RG[Resource Group]
    TF2 --> APP
    TF2 --> MON
```

Detalhes e responsabilidades: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Infraestrutura como código

`terraform-azure/` cria:

- Resource Group `rg-zelacidade-gs-99431`;
- App Service Plan Linux F1;
- Web App em container com HTTPS obrigatório;
- autenticação básica de FTP e WebDeploy desabilitada;
- alerta operacional de HTTP 5xx;
- alerta controlado para evidência do monitoramento.

O state, planos, `tfvars` e credenciais não são versionados. O deploy altera somente a imagem do container; o Terraform ignora essa propriedade para não desfazer uma versão publicada pelo CI/CD.

## Pipeline DevSecOps

`.github/workflows/ci.yml` roda em cada push e pull request:

1. testes, validação do Compose e build dos containers;
2. Gitleaks para segredos;
3. Semgrep para análise estática;
4. Trivy para vulnerabilidades HIGH/CRITICAL;
5. `terraform fmt` e `terraform validate`;
6. na `main`, build/push da imagem no GHCR e deploy automático no Azure;
7. smoke test HTTPS da URL pública.

Evidência controlada: a execução [42637898515](https://github.com/brunoventuri01/zelacidade/actions/runs/42637898515) foi barrada por um segredo sintético. Após a correção, a execução [42638080332](https://github.com/brunoventuri01/zelacidade/actions/runs/42638080332) passou.

## Observabilidade

O Azure Monitor coleta métricas nativas do App Service: tráfego, respostas HTTP 2xx/4xx/5xx, tempo de resposta, CPU e memória. O Terraform mantém dois alertas:

- `alert-zelacidade-http5xx`: mais de cinco erros 5xx em cinco minutos;
- `alert-zelacidade-traffic-evidence`: limite baixo usado no teste controlado.

## Como reproduzir

Pré-requisitos: Terraform 1.17+, Azure CLI autenticada e uma assinatura compatível.

```bash
cd terraform-azure
terraform init
terraform fmt -check
terraform validate
terraform plan -var="subscription_id=<ID_DA_ASSINATURA>"
```

O `apply` deve ser executado apenas pelo responsável pela assinatura. O deploy da aplicação ocorre pela pipeline, usando `AZURE_CREDENTIALS` nos GitHub Secrets.

## Ficha técnica da infraestrutura

| Item | Situação |
|---|---|
| Nuvem | Microsoft Azure — assinatura FIAP Students Starter |
| Execução | Azure App Service Linux F1 em container |
| IaC | Terraform com provider AzureRM |
| Registry | GitHub Container Registry |
| CI/CD | GitHub Actions |
| Segurança | Gitleaks, Semgrep, Trivy e secrets do GitHub |
| Observabilidade | Azure Monitor e alertas de métrica |
| HTTPS | Obrigatório no App Service |
| MVP oficial | FastAPI + React em container único (porta 8000), Postgres no Neon |

## Documentos

- [`docs/EVIDENCE.md`](docs/EVIDENCE.md): evidências verificáveis e pendências;
- [`docs/SECURITY.md`](docs/SECURITY.md): segurança, LGPD e responsabilidade compartilhada;
- [`docs/COSTS.md`](docs/COSTS.md): estimativa de custos;
- [`docs/MVP-INTEGRATION.md`](docs/MVP-INTEGRATION.md): checklist para receber o MVP oficial.

