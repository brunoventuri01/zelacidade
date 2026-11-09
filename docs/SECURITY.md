# Segurança e responsabilidade compartilhada

## Microsoft Azure

Responsável pela segurança física, datacenters, hipervisor e disponibilidade da plataforma gerenciada.

## Equipe ZelaCidade

Responsável por código, dependências, imagens, identidades, segredos, configuração do App Service, dados e regras do MVP.

Controles já aplicados:

- acesso público somente por HTTPS;
- nenhuma VM, SSH ou porta administrativa pública;
- FTP e WebDeploy com autenticação básica desabilitados;
- credencial de deploy limitada ao Web App e armazenada em GitHub Secrets;
- imagens versionadas pelo SHA do commit;
- Gitleaks, Semgrep e Trivy bloqueiam a pipeline;
- `*.tfstate`, planos, `*.tfvars`, `.env` e chaves permanecem fora do Git;
- alertas de erros HTTP 5xx e tráfego controlado gerenciados por Terraform.

## LGPD

Fotos, descrição e geolocalização podem identificar pessoas ou rotinas e devem ser tratadas com finalidade explícita, minimização, retenção limitada, controle de acesso e processo de exclusão. Rostos e placas devem ser evitados ou anonimizados.

Antes do MVP oficial entrar em produção, a equipe deve definir:

- política de retenção e exclusão;
- autenticação e autorização de usuários;
- validação e limite de uploads;
- gestão e rotação dos segredos reais;
- backup e restauração dos dados;
- canal para solicitações do titular.

