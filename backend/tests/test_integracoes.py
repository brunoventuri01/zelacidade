import json
from datetime import UTC, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import create_app
from conftest import CHAVES, configuracao, jpeg_com_exif, nova_ocorrencia

RPA = {"X-API-Key": CHAVES["rpa"]}
ADMIN = {"Authorization": f"Bearer {CHAVES['admin']}"}


def _robo(client, **campos):
    corpo = {"robot_id": "roberto-01", "event_type": "obstacle", "distance_cm": 18.5,
             "timestamp": "2026-11-06T15:18:00-03:00", "test_location": "Bancada Maker Lab - FIAP",
             "simulated": True, "latitude": -23.574, "longitude": -46.623}
    corpo.update(campos)
    return client.post("/api/v1/robot/occurrences", json=corpo, headers={"X-API-Key": CHAVES["robo"]})


def test_robo_exige_chave(client):
    resposta = client.post("/api/v1/robot/occurrences", json={})
    assert resposta.status_code == 401


def test_integracao_desligada_sem_chave_no_servidor():
    with TestClient(create_app(configuracao(robot_api_key=""))) as c:
        assert _robo(c).status_code == 503


def test_robo_registra_com_protocolo(client):
    resposta = _robo(client)
    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["protocolo"] == f"ZC-{dados['id']:06d}"
    detalhe = client.get(f"/api/v1/ocorrencias/{dados['id']}").json()
    assert detalhe["categoria"] == "obstaculo"
    assert detalhe["origem"] == "robo" and detalhe["simulado"] is True
    assert detalhe["criado_em"] == "2026-11-06T18:18:00Z"


def test_robo_sem_coordenada_usa_centro_da_area(client):
    dados = _robo(client, latitude=None, longitude=None).json()
    detalhe = client.get(f"/api/v1/ocorrencias/{dados['id']}").json()
    area = client.get("/api/v1/config").json()["area"]
    assert detalhe["local_aproximado"] is True
    assert detalhe["latitude"] == area["centro"]["latitude"]


def test_rpa_lista_inclui_email_so_com_consentimento(client):
    nova_ocorrencia(client, email="morador@exemplo.com", consentimento="true")
    pendentes = client.get("/api/v1/integracao/ocorrencias", headers=RPA).json()
    assert pendentes[0]["autor_email"] == "morador@exemplo.com"


def test_triagem_e_linha_do_tempo(client):
    criada = nova_ocorrencia(client)
    resposta = client.patch(f"/api/v1/integracao/ocorrencias/{criada['id']}/triagem", headers=RPA,
                            json={"status": "triada", "prioridade": "alta", "motivo": "buraco + chuva prevista"})
    assert resposta.status_code == 200
    assert resposta.json()["prioridade"] == "alta"
    detalhe = client.get(f"/api/v1/ocorrencias/{criada['id']}").json()
    assert detalhe["eventos"][-1]["ator"] == "robo_rpa"
    repetida = client.patch(f"/api/v1/integracao/ocorrencias/{criada['id']}/triagem", headers=RPA,
                            json={"status": "triada", "prioridade": "alta", "motivo": "de novo"})
    assert repetida.status_code == 409


def test_duplicada_soma_confirmacao_na_original(client):
    original = nova_ocorrencia(client)
    repetida = nova_ocorrencia(client)
    resposta = client.patch(f"/api/v1/integracao/ocorrencias/{repetida['id']}/triagem", headers=RPA,
                            json={"status": "duplicada", "motivo": "mesmo buraco a 12 m",
                                  "duplicada_de": original["id"]})
    assert resposta.status_code == 200
    assert client.get(f"/api/v1/ocorrencias/{original['id']}").json()["confirmacoes"] == 1


def test_triada_exige_prioridade(client):
    criada = nova_ocorrencia(client)
    resposta = client.patch(f"/api/v1/integracao/ocorrencias/{criada['id']}/triagem", headers=RPA,
                            json={"status": "triada", "motivo": "sem prioridade"})
    assert resposta.status_code == 422


def test_painel_publicado_pelo_robo(client):
    corpo = {"fonte": "workspace.zelacidade.ouro_painel", "gerado_em": "2026-11-15T12:00:00Z",
             "linhas": [{"bairro": "Santana", "categoria": "buraco", "abertas": 4}], "kpis": {"pct_resolvidas": 0.4}}
    assert client.post("/api/v1/integracao/painel", json=corpo, headers=RPA).status_code == 201
    ouro = client.get("/api/v1/painel").json()["ouro"]
    assert ouro["fonte"] == "workspace.zelacidade.ouro_painel"
    assert ouro["linhas"][0]["abertas"] == 4


def test_export_ndjson_por_dia_de_sao_paulo(client):
    criada = nova_ocorrencia(client, email="morador@exemplo.com", consentimento="true")
    hoje_sp = datetime.now(UTC).astimezone(timezone(timedelta(hours=-3))).date()
    resposta = client.get(f"/api/v1/export/ocorrencias?data={hoje_sp}", headers={"X-API-Key": CHAVES["export"]})
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("application/x-ndjson")
    linhas = [json.loads(linha) for linha in resposta.text.strip().splitlines()]
    assert linhas[0]["id"] == criada["id"]
    assert linhas[0]["autor_email"] == "morador@exemplo.com"
    ontem = hoje_sp - timedelta(days=2)
    vazio = client.get(f"/api/v1/export/ocorrencias?data={ontem}", headers={"X-API-Key": CHAVES["export"]})
    assert vazio.text == ""


def test_gestor_so_resolve_com_foto(client):
    criada = nova_ocorrencia(client)
    url = f"/api/v1/gestao/ocorrencias/{criada['id']}"
    assert client.patch(url, data={"status": "resolvida"}).status_code == 401
    assert client.patch(url, data={"status": "resolvida"}, headers=ADMIN).status_code == 422
    resolvida = client.patch(url, data={"status": "resolvida", "comentario": "Tapado"}, headers=ADMIN,
                             files={"foto": ("ok.jpg", jpeg_com_exif(), "image/jpeg")})
    assert resolvida.status_code == 200
    assert resolvida.json()["status"] == "resolvida"
    detalhe = client.get(f"/api/v1/ocorrencias/{criada['id']}").json()
    assert {f["tipo"] for f in detalhe["fotos"]} == {"registro", "resolucao"}
