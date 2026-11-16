# Checklist de integração do MVP oficial

O ambiente está pronto. Situação da integração do MVP oficial (PR `feat/mvp-oficial`):

- [x] confirmar a pasta e o Dockerfile que representam o frontend/API oficiais (`Dockerfile` único na raiz, `backend/`, `frontend/`);
- [x] registrar variáveis obrigatórias sem valores reais no `.env.example`;
- [ ] armazenar segredos somente em GitHub Secrets ou configurações seguras do Azure (`DATABASE_URL`, `ROBOT_API_KEY`, `RPA_API_KEY`, `EXPORT_API_KEY`, `ADMIN_TOKEN`, `HASH_SALT`, `GENAI_API_URL`, `GENAI_API_KEY`);
- [x] atualizar o contexto do build no job `deploy-azure` (`context: .`);
- [x] adicionar health check real do MVP (`/health` consulta o banco; usado no `HEALTHCHECK`, no smoke test do CI e no smoke test do deploy);
- [x] executar testes locais (30 testes do backend, 5 do frontend, build do site);
- [ ] abrir pull request e confirmar Gitleaks, Semgrep, Trivy e Terraform verdes;
- [ ] aplicar o `WEBSITES_PORT=8000` com `terraform apply` (responsável pela assinatura);
- [ ] fazer merge na `main` e acompanhar o deploy;
- [ ] validar URL pública, endpoints, persistência e fluxo principal;
- [ ] atualizar a ficha técnica e o PDF com prints do MVP oficial;
- [x] remover toda referência a “frontend provisório” no README e na arquitetura.

Não é necessário recriar a infraestrutura. A pipeline substitui a imagem do container mantendo URL, HTTPS e alertas.
