# Integração Maker Lab

Endpoint: `POST /api/v1/robot/occurrences`. Autenticação pelo cabeçalho `X-API-Key`, armazenado somente no `.env` do servidor.

```bash
curl -X POST http://HOST/api/v1/robot/occurrences -H 'Content-Type: application/json' -H 'X-API-Key: SUA_CHAVE' -d '{"robot_id":"robo-01","event_type":"obstacle","distance_cm":18.5,"timestamp":"2026-11-06T15:18:00-03:00","test_location":"Bancada Maker Lab","simulated":true}'
```

Os testes atuais validam apenas a infraestrutura da API; não comprovam integração com hardware físico.
