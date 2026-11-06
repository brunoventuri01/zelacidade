# Segurança e responsabilidade compartilhada

- SkyNova/CloudStack: segurança física, hipervisor, disponibilidade e firewall de borda.
- Equipe ZelaCidade: sistema operacional, containers, aplicação, identidades, segredos, backups e dados.
- PostgreSQL não publica porta; Grafana e Prometheus usam apenas loopback.
- `.env`, states e `tfvars` sensíveis são ignorados pelo Git.
- Pendências: restringir SSH `0.0.0.0/0` e trocar a senha temporária ao final.

## LGPD

Fotos e geolocalização podem constituir dados pessoais. Devem possuir finalidade explícita, retenção limitada, controle de acesso e mecanismo de exclusão. Evitar rostos e placas ou aplicar anonimização.
