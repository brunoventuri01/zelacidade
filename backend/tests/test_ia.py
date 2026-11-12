import httpx
import numpy as np
from PIL import Image

from app.assistente import Assistente, adaptar_resposta
from app.visao import decodificar_saida, letterbox, nms, severidade

NOMES = {"0": "buraco"}


def test_letterbox_mantem_proporcao():
    tensor, escala, pad_x, pad_y = letterbox(Image.new("RGB", (1280, 640)), 640)
    assert tensor.shape == (1, 3, 640, 640)
    assert escala == 0.5 and pad_x == 0 and pad_y == 160


def test_nms_remove_caixa_sobreposta():
    caixas = np.array([[0, 0, 100, 100], [5, 5, 100, 100], [200, 200, 260, 260]], dtype=np.float32)
    scores = np.array([0.9, 0.8, 0.7], dtype=np.float32)
    assert nms(caixas, scores, 0.45) == [0, 2]


def test_decodifica_saida_bruta_do_yolo11():
    saida = np.zeros((1, 5, 8400), dtype=np.float32)
    saida[0, :, 0] = [320, 320, 100, 50, 0.9]   # caixa válida
    saida[0, :, 1] = [322, 321, 100, 50, 0.6]   # duplicada (some no NMS)
    saida[0, :, 2] = [100, 100, 20, 20, 0.1]    # abaixo do limiar
    caixas = decodificar_saida(saida, 0.35, 0.45, 1.0, 0, 0, 640, 640, NOMES)
    assert len(caixas) == 1
    assert caixas[0]["classe"] == "buraco"
    assert caixas[0]["bbox"] == [270, 295, 370, 345]


def test_decodifica_saida_com_nms_embutido_e_desfaz_letterbox():
    saida = np.zeros((1, 300, 6), dtype=np.float32)
    saida[0, 0] = [100, 260, 300, 360, 0.8, 0]
    caixas = decodificar_saida(saida, 0.35, 0.45, 0.5, 0, 160, 1280, 640, NOMES)
    assert caixas[0]["bbox"] == [200, 200, 600, 400]


def test_severidade_provisoria():
    assert severidade([], 100, 100) is None
    assert severidade([{"bbox": [0, 0, 50, 50]}], 100, 100) == "alta"
    assert severidade([{"bbox": [0, 0, 10, 10]}], 100, 100) == "baixa"


def test_adapta_formato_do_guilherme():
    dados = {
        "saida": {"resposta": "Ligue 156.", "fontes": ["SP156"], "recusou": False,
                  "categoria": "buraco", "risco": "medio"},
        "fontes_detalhadas": [{"titulo": "Tapa-buraco", "orgao": "Prefeitura de SP",
                               "link": "https://sp156.prefeitura.sp.gov.br"},
                              {"titulo": "Link perigoso", "link": "javascript:alert(1)"}],
    }
    adaptada = adaptar_resposta(dados)
    assert adaptada["resposta"] == "Ligue 156."
    assert adaptada["fontes"][0]["orgao"] == "Prefeitura de SP"
    assert adaptada["fontes"][1]["url"] is None
    assert adaptada["risco"] == "medio"


def test_assistente_offline_usa_trechos(tmp_path):
    trechos = tmp_path / "trechos.json"
    trechos.write_text('[{"texto": "Buraco na via: SP156", "titulo": "SP156", "categorias": ["buraco"]},'
                       ' {"texto": "Poste apagado: 156", "titulo": "Ilume", "categorias": ["iluminação"]}]',
                       encoding="utf-8")
    assistente = Assistente("", "", 1, str(trechos))
    resposta = assistente.perguntar("O que faço com um buraco?", categoria="buraco")
    assert resposta["disponivel"] is False
    assert [t["titulo"] for t in resposta["trechos"]] == ["SP156"]
    assert assistente.trechos_para("iluminacao")[0]["titulo"] == "Ilume"


def test_assistente_cai_para_offline_quando_api_falha(monkeypatch, tmp_path):
    def falha(*_args, **_kwargs):
        raise httpx.ConnectTimeout("sem resposta")

    monkeypatch.setattr(httpx, "post", falha)
    assistente = Assistente("https://exemplo.invalid", "chave", 1, str(tmp_path / "nao-existe.json"))
    assert assistente.perguntar("Teste?")["disponivel"] is False
