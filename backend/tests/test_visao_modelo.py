"""Regressão da integração com o modelo do Guilherme: o backend tem de reproduzir o esperado.json.

O esperado.json é o que o modelo responde (não é gabarito): a teste_4 sai sem caixas e serve para o
caminho "nenhuma detecção". Ao trocar o best.onnx (ex.: v2), atualize também tests/visao/esperado.json.
"""

import json
from pathlib import Path

import pytest
from PIL import Image

from app.visao import DetectorBuracos

RAIZ = Path(__file__).resolve().parents[1]
MODELO = RAIZ / "models" / "visao" / "best.onnx"
AMOSTRAS = Path(__file__).resolve().parent / "visao"
ESPERADO = json.loads((AMOSTRAS / "esperado.json").read_text(encoding="utf-8"))

pytestmark = pytest.mark.skipif(not MODELO.is_file(), reason="best.onnx não instalado")


@pytest.fixture(scope="module")
def detector():
    return DetectorBuracos(str(MODELO))


@pytest.mark.parametrize("nome", sorted(ESPERADO))
def test_reproduz_saida_do_modelo(detector, nome):
    esperado = ESPERADO[nome]
    imagem = Image.open(AMOSTRAS / "amostras" / nome).convert("RGB")
    assert imagem.size == (esperado["largura"], esperado["altura"])

    resultado = detector.detectar(imagem)

    assert resultado["disponivel"] is True
    assert resultado["n_caixas"] == esperado["n_caixas"]
    assert resultado["severidade"] == esperado["severidade"]
    for obtida, alvo in zip(resultado["caixas"], esperado["deteccoes"]):
        assert obtida["classe"] == alvo["classe"]
        assert obtida["confianca"] == pytest.approx(alvo["confianca"], abs=0.002)
        assert obtida["bbox"] == pytest.approx(alvo["bbox_xyxy"], abs=0.5)
        assert obtida["area_relativa"] == pytest.approx(alvo["area_relativa"], abs=0.001)


def test_sugestao_usa_a_caixa_mais_confiante(detector):
    resultado = detector.detectar(Image.open(AMOSTRAS / "amostras" / "teste_2.jpg").convert("RGB"))
    assert resultado["categoria_sugerida"] == "buraco"
    assert resultado["confianca"] == pytest.approx(0.8906, abs=0.002)


def test_sem_buraco_nao_sugere_categoria(detector):
    resultado = detector.detectar(Image.open(AMOSTRAS / "amostras" / "teste_4.jpg").convert("RGB"))
    assert resultado["categoria_sugerida"] is None
    assert resultado["severidade"] == "nenhuma"


def test_registro_pela_api_guarda_a_sugestao_da_ia():
    """Ponta a ponta: a foto enviada ao MVP é analisada antes da recompressão e o resultado vai para o registro."""
    from fastapi.testclient import TestClient

    from app.main import create_app
    from conftest import configuracao

    foto = (AMOSTRAS / "amostras" / "teste_3.jpg").read_bytes()
    with TestClient(create_app(configuracao(cv_model_path=str(MODELO)))) as client:
        sugestao = client.post("/api/v1/ia/classificar", files={"foto": ("t3.jpg", foto, "image/jpeg")}).json()
        assert sugestao["n_caixas"] == ESPERADO["teste_3.jpg"]["n_caixas"]
        criada = client.post(
            "/api/v1/ocorrencias",
            data={"categoria": "buraco", "descricao": "Buraco na pista", "bairro": "Santana",
                  "latitude": "-23.50", "longitude": "-46.62"},
            files={"foto": ("t3.jpg", foto, "image/jpeg")},
        ).json()
        detalhe = client.get(f"/api/v1/ocorrencias/{criada['id']}").json()
    assert detalhe["categoria_ia"] == "buraco"
    assert detalhe["confianca_ia"] == pytest.approx(0.874, abs=0.002)
    assert detalhe["severidade_ia"] == "alta"
    assert any(e["ator"] == "ia" for e in detalhe["eventos"])
