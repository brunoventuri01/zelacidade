from io import BytesIO

from PIL import Image

from conftest import nova_ocorrencia


def test_health(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_config_traz_area_e_vocabulario(client):
    dados = client.get("/api/v1/config").json()
    assert dados["area"]["bairros"]
    assert {c["valor"] for c in dados["categorias"]} >= {"buraco", "iluminacao", "obstaculo"}
    assert dados["visao"]["disponivel"] is False


def test_registrar_e_listar(client):
    criada = nova_ocorrencia(client)
    assert criada["protocolo"].startswith("ZC-")
    assert criada["status"] == "recebida"
    lista = client.get("/api/v1/ocorrencias").json()
    assert [o["id"] for o in lista] == [criada["id"]]
    assert lista[0]["foto_id"] is not None


def test_foto_reduzida_e_sem_exif(client):
    criada = nova_ocorrencia(client)
    detalhe = client.get(f"/api/v1/ocorrencias/{criada['id']}").json()
    foto = client.get(f"/api/v1/fotos/{detalhe['foto_id']}")
    imagem = Image.open(BytesIO(foto.content))
    assert max(imagem.size) <= 1280
    assert len(imagem.getexif()) == 0


def test_email_nunca_aparece_nas_rotas_publicas(client):
    criada = nova_ocorrencia(client, email="morador@exemplo.com", consentimento="true")
    texto = client.get(f"/api/v1/ocorrencias/{criada['id']}").text + client.get("/api/v1/ocorrencias").text
    assert "morador@exemplo.com" not in texto


def test_email_exige_consentimento(client):
    resposta = client.post("/api/v1/ocorrencias", data={
        "categoria": "buraco", "descricao": "Teste de consentimento", "bairro": "Santana",
        "latitude": "-23.5", "longitude": "-46.6", "email": "a@exemplo.com"})
    assert resposta.status_code == 422


def test_categoria_invalida(client):
    resposta = client.post("/api/v1/ocorrencias", data={
        "categoria": "dragao", "descricao": "Categoria errada", "bairro": "Santana",
        "latitude": "-23.5", "longitude": "-46.6"})
    assert resposta.status_code == 422


def test_arquivo_que_nao_e_imagem(client):
    resposta = client.post("/api/v1/ocorrencias",
                           data={"categoria": "buraco", "descricao": "Arquivo errado", "bairro": "Santana",
                                 "latitude": "-23.5", "longitude": "-46.6"},
                           files={"foto": ("x.jpg", b"isto nao e imagem", "image/jpeg")})
    assert resposta.status_code == 422
    assert client.get("/api/v1/ocorrencias").json() == []


def test_confirmacao_unica_por_aparelho(client):
    criada = nova_ocorrencia(client)
    url = f"/api/v1/ocorrencias/{criada['id']}/confirmacoes"
    cabecalho = {"X-Dispositivo": "aparelho-de-teste-1"}
    primeira = client.post(url, headers=cabecalho, data={"comentario": "Também vi hoje"})
    assert primeira.status_code == 201
    assert primeira.json()["confirmacoes"] == 1
    assert client.post(url, headers=cabecalho, data={}).status_code == 409
    detalhe = client.get(f"/api/v1/ocorrencias/{criada['id']}").json()
    assert detalhe["comentarios"][0]["comentario"] == "Também vi hoje"
    assert any(e["tipo"] == "confirmacao" for e in detalhe["eventos"])


def test_classificar_sem_modelo_nao_quebra(client):
    from conftest import jpeg_com_exif
    resposta = client.post("/api/v1/ia/classificar", files={"foto": ("a.jpg", jpeg_com_exif(), "image/jpeg")})
    assert resposta.status_code == 200
    assert resposta.json()["disponivel"] is False


def test_painel_ao_vivo_sem_ouro(client):
    nova_ocorrencia(client)
    dados = client.get("/api/v1/painel").json()
    assert dados["ouro"] is None
    assert dados["ao_vivo"]["total"] == 1
    assert dados["ao_vivo"]["abertas_por_categoria"] == {"buraco": 1}
