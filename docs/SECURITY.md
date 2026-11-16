# Seguranca, LGPD e responsabilidade compartilhada

## Microsoft Azure e Neon

Os provedores respondem por seguranca fisica, datacenters, hipervisor e operacao da plataforma gerenciada dentro dos planos contratados.

## Equipe ZelaCidade

A equipe responde por codigo, dependencias, imagens, identidades, segredos, configuracao do App Service, autorizacao das rotas, finalidade dos dados, retencao e exclusao.

Controles implementados:

- container multi-stage e usuario nao root (`uid 10001`);
- acesso publico apenas por HTTPS;
- nenhuma VM, SSH, RDP ou porta administrativa publica;
- credencial de deploy e chaves armazenadas em GitHub Secrets ou Azure App Settings;
- imagem versionada pelo SHA do commit;
- Gitleaks, Semgrep, Trivy e testes bloqueantes;
- `tfstate`, planos, `tfvars`, `.env` e chaves fora do Git;
- cabecalhos CSP, `nosniff`, `Referrer-Policy` e `Permissions-Policy`;
- upload limitado a JPEG, PNG ou WEBP de ate 5 MB;
- imagens reduzidas e regravadas sem EXIF;
- e-mail opcional e condicionado a consentimento;
- identificador do dispositivo armazenado como hash;
- registros simulados identificados por `simulado=true`, selo e filtro;
- alertas de HTTP 5xx e trafego gerenciados por Terraform.

## LGPD

Fotos, descricoes e geolocalizacao sao dados potencialmente identificaveis. O MVP aplica minimizacao, remove EXIF, orienta a evitar rostos e placas, separa simulacoes e nao publica e-mail nas rotas publicas.

Para uso real alem da demonstracao academica, a equipe deve formalizar prazo de retencao, processo de exclusao, canal para solicitacoes do titular, rotacao periodica de segredos e rotina de backup e restauracao.

