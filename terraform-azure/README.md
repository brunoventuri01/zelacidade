# Terraform Azure

Infraestrutura do ZelaCidade criada integralmente por codigo no Azure App Service: grupo de recursos, plano Linux gratuito F1 e aplicacao Web baseada em container. O servico publica somente HTTPS e nao possui porta administrativa ou SSH exposta.

Credenciais, `tfvars`, planos e state nunca devem ser versionados. O container Nginx e apenas um placeholder; o MVP oficial da equipe substituira a imagem sem recriar a infraestrutura.

Recursos aplicados:

- Resource Group `rg-zelacidade-gs-99431`;
- App Service Plan Linux F1 gratuito;
- Linux Web App com HTTPS obrigatorio;
- FTP e WebDeploy por autenticacao basica desabilitados;
- nenhuma porta SSH ou administrativa exposta.

URL provisoria: <https://app-zelacidade-gs-99431.azurewebsites.net>
