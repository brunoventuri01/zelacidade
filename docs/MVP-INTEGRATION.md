# Checklist de integração do MVP oficial

O ambiente está pronto. Quando a equipe entregar o MVP, executar:

- [ ] confirmar a pasta e o Dockerfile que representam o frontend/API oficiais;
- [ ] registrar variáveis obrigatórias sem valores reais no `.env.example`;
- [ ] armazenar segredos somente em GitHub Secrets ou configurações seguras do Azure;
- [ ] atualizar o contexto do build no job `deploy-azure`;
- [ ] adicionar health check real do MVP;
- [ ] executar testes locais e abrir pull request;
- [ ] confirmar Gitleaks, Semgrep, Trivy e Terraform verdes;
- [ ] fazer merge na `main` e acompanhar o deploy;
- [ ] validar URL pública, endpoints, persistência e fluxo principal;
- [ ] atualizar a ficha técnica e o PDF com prints do MVP oficial;
- [ ] remover toda referência a “frontend provisório”.

Não é necessário recriar a infraestrutura. A pipeline substitui a imagem do container mantendo URL, HTTPS e alertas.

