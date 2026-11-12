import os
from io import BytesIO

import pytest

# o módulo app.main cria uma app ao ser importado; nos testes ela usa SQLite em memória
os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

CHAVES = {"robo": "chave-robo-teste", "rpa": "chave-rpa-teste", "export": "chave-export-teste",
          "admin": "token-admin-teste"}


def configuracao(**extra) -> Settings:
    base = dict(
        database_url="sqlite://",
        robot_api_key=CHAVES["robo"],
        rpa_api_key=CHAVES["rpa"],
        export_api_key=CHAVES["export"],
        admin_token=CHAVES["admin"],
        cv_model_path="/nao/existe/best.onnx",
        hash_salt="sal-de-teste",
    )
    base.update(extra)
    return Settings(**base)


@pytest.fixture
def client():
    with TestClient(create_app(configuracao())) as c:
        yield c


def jpeg_com_exif(largura=1600, altura=1200) -> bytes:
    imagem = Image.new("RGB", (largura, altura), (90, 90, 90))
    exif = imagem.getexif()
    exif[0x010F] = "FabricanteTeste"  # Make
    exif[0x0110] = "ModeloTeste"  # Model
    saida = BytesIO()
    imagem.save(saida, "JPEG", exif=exif)
    return saida.getvalue()


def nova_ocorrencia(client, **campos):
    dados = {"categoria": "buraco", "descricao": "Buraco grande na esquina", "bairro": "Santana",
             "latitude": "-23.50", "longitude": "-46.62"}
    dados.update(campos)
    arquivos = {"foto": ("buraco.jpg", jpeg_com_exif(), "image/jpeg")}
    resposta = client.post("/api/v1/ocorrencias", data=dados, files=arquivos)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()
