from pathlib import Path

import httpx
import numpy as np
from PIL import Image

from app.assistente import Assistente, adaptar_resposta
from app.visao import decodificar_saida, letterbox, nms, severidade

NOMES = {"0": "buraco"}
TRECHOS = str(Path(__file__).resolve().parents[1] / "app" / "data" / "trechos.json")


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


def caixa(area):
    return {"area_relativa": area}


def test_severidade_regra_do_guilherme():
    assert severidade([]) == "nenhuma"
    assert severidade([caixa(0.06)]) == "alta"
    assert severidade([caixa(0.01)] * 4) == "alta"          # 4 caixas pequenas
    assert severidade([caixa(0.02)]) == "media"
    assert severidade([caixa(0.01), caixa(0.01)]) == "media"  # 2 caixas
    assert severidade([caixa(0.01)]) == "baixa"


# Respostas reais da API do Guilherme (zelacidade-genai), coladas como vieram
RESPOSTA_NORMAL = {
    "saida": {"resposta": "A faixa livre é a parte da calçada destinada exclusivamente à circulação de pedestres. "
                          "Ela deve ter no mínimo 1,20 m de largura.",
              "categoria": "calcada", "risco": "medio", "fontes": ["T015"], "recusou": False},
    "fontes_detalhadas": [{"id": "T015", "titulo": "Faixa livre: largura e inclinação",
                           "orgao": "Prefeitura de Sao Paulo",
                           "url": "https://saopaulo.sp.leg.br/iah/fulltext/decretos/D59671.pdf"}],
    "config": "C", "recusa_por_limiar": False, "latencia_s": 13.474,
    "aviso": "Orientação informativa. A ZelaCidade não substitui os canais oficiais da Prefeitura (SP156).",
}
RESPOSTA_RECUSA = {
    "saida": {"resposta": "Não consta na base de conhecimento da ZelaCidade. Para esse assunto, consulte os "
                          "canais oficiais da Prefeitura (SP156).",
              "categoria": "fora_do_escopo", "risco": "nao_se_aplica", "fontes": [], "recusou": True},
    "fontes_detalhadas": [], "config": "C", "recusa_por_limiar": False, "latencia_s": 4.395,
    "aviso": "Orientação informativa. A ZelaCidade não substitui os canais oficiais da Prefeitura (SP156).",
}


def test_adapta_resposta_normal():
    adaptada = adaptar_resposta(RESPOSTA_NORMAL)
    assert adaptada["resposta"].startswith("A faixa livre")
    assert adaptada["recusou"] is False
    assert adaptada["fontes"] == [{"id": "T015", "titulo": "Faixa livre: largura e inclinação",
                                   "orgao": "Prefeitura de Sao Paulo",
                                   "url": "https://saopaulo.sp.leg.br/iah/fulltext/decretos/D59671.pdf"}]
    assert adaptada["risco"] == "medio"
    assert "SP156" in adaptada["aviso"]


def test_adapta_recusa_e_descarta_link_perigoso():
    assert adaptar_resposta(RESPOSTA_RECUSA)["recusou"] is True
    perigosa = {**RESPOSTA_NORMAL, "fontes_detalhadas": [{"id": "X", "titulo": "?", "url": "javascript:alert(1)"}]}
    assert adaptar_resposta(perigosa)["fontes"][0]["url"] is None


def test_offline_com_a_base_real():
    assistente = Assistente("", "", 1, TRECHOS)
    assert len(assistente.trechos) == 47
    por_categoria = assistente.perguntar("O que faço com um buraco?", categoria="buraco")
    assert por_categoria["disponivel"] is False
    assert len(por_categoria["trechos"]) == 3
    ids_buraco = {t["id"] for t in assistente.trechos if t["categoria"] == "buraco_via"}
    assert {t["id"] for t in por_categoria["trechos"]} <= ids_buraco
    sem_categoria = assistente.buscar_trechos("Tem um poste apagado na minha rua, quem eu aciono?")
    assert sem_categoria[0]["id"] in {"T027", "T028", "T029"}
    assert assistente.buscar_trechos("Qual o preço da CNH?") == []


def test_trecho_sem_link_nao_vira_url():
    assistente = Assistente("", "", 1, TRECHOS)
    plataforma = [t for t in assistente.buscar_trechos("ZelaCidade substitui o SP156?", limite=5)
                  if t["id"] == "T045"]
    assert plataforma and plataforma[0]["url"] is None


def test_pergunta_com_contexto_respeita_500_caracteres(monkeypatch):
    enviado = {}

    class Resposta:
        def raise_for_status(self):
            return None

        def json(self):
            return RESPOSTA_NORMAL

    def captura(url, json, headers, timeout):
        enviado.update(url=url, json=json, headers=headers, timeout=timeout)
        return Resposta()

    monkeypatch.setattr(httpx, "post", captura)
    assistente = Assistente("https://tunel.exemplo", "chave-genai", 60, TRECHOS)
    resposta = assistente.perguntar("x" * 500, contexto="Buraco na via, severidade alta")
    assert resposta["disponivel"] is True
    assert enviado["url"] == "https://tunel.exemplo/perguntar"
    assert enviado["headers"] == {"X-API-Key": "chave-genai"}
    assert enviado["timeout"] == 60
    assert len(enviado["json"]["pergunta"]) <= 500
    assert enviado["json"]["pergunta"].endswith("Contexto do registro: Buraco na via, severidade alta")


def test_assistente_cai_para_offline_quando_api_falha(monkeypatch):
    def falha(*_args, **_kwargs):
        raise httpx.ConnectTimeout("sem resposta")

    monkeypatch.setattr(httpx, "post", falha)
    assistente = Assistente("https://exemplo.invalid", "chave", 1, TRECHOS)
    resposta = assistente.perguntar("Poste apagado, o que faço?", categoria="iluminacao")
    assert resposta["disponivel"] is False
    assert resposta["trechos"][0]["id"].startswith("T0")
