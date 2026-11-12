"""Detector de buracos (modelo YOLO11n do Guilherme exportado em ONNX).

O modelo só é carregado no primeiro uso, com uma thread, para caber no plano F1.
Sem o arquivo best.onnx, o MVP continua funcionando e o morador escolhe a categoria.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

import numpy as np
from PIL import Image

log = logging.getLogger("zelacidade.visao")


def letterbox(imagem: Image.Image, tamanho: int = 640, cor: int = 114):
    """Redimensiona mantendo a proporção e completa com borda cinza (padrão do YOLO)."""
    largura, altura = imagem.size
    escala = min(tamanho / largura, tamanho / altura)
    nova_l, nova_a = round(largura * escala), round(altura * escala)
    tela = Image.new("RGB", (tamanho, tamanho), (cor, cor, cor))
    pad_x, pad_y = (tamanho - nova_l) // 2, (tamanho - nova_a) // 2
    tela.paste(imagem.resize((nova_l, nova_a), Image.BILINEAR), (pad_x, pad_y))
    tensor = np.asarray(tela, dtype=np.float32).transpose(2, 0, 1)[None] / 255.0
    return np.ascontiguousarray(tensor), escala, pad_x, pad_y


def nms(caixas: np.ndarray, scores: np.ndarray, limiar_iou: float) -> list[int]:
    if len(caixas) == 0:
        return []
    x1, y1, x2, y2 = caixas.T
    areas = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    ordem = scores.argsort()[::-1]
    manter: list[int] = []
    while ordem.size:
        i = int(ordem[0])
        manter.append(i)
        xx1 = np.maximum(x1[i], x1[ordem[1:]])
        yy1 = np.maximum(y1[i], y1[ordem[1:]])
        xx2 = np.minimum(x2[i], x2[ordem[1:]])
        yy2 = np.minimum(y2[i], y2[ordem[1:]])
        inter = np.clip(xx2 - xx1, 0, None) * np.clip(yy2 - yy1, 0, None)
        iou = inter / (areas[i] + areas[ordem[1:]] - inter + 1e-9)
        ordem = ordem[1:][iou <= limiar_iou]
    return manter


def decodificar_saida(saida, limiar, limiar_iou, escala, pad_x, pad_y, largura, altura, nomes):
    """Aceita a saída bruta [1, 4+nc, N] (sem NMS) ou a com NMS embutido [1, K, 6]."""
    arr = np.asarray(saida, dtype=np.float32)
    if arr.ndim != 3:
        raise ValueError(f"Formato de saída não suportado: {arr.shape}")
    if arr.shape[2] == 6 and arr.shape[1] != 6:
        pred = arr[0]
        pred = pred[pred[:, 4] >= limiar]
        caixas, scores, classes = pred[:, :4].copy(), pred[:, 4], pred[:, 5].astype(int)
    else:
        pred = arr[0].T  # [N, 4+nc]
        cls_scores = pred[:, 4:]
        scores = cls_scores.max(axis=1)
        classes = cls_scores.argmax(axis=1)
        filtro = scores >= limiar
        xywh, scores, classes = pred[filtro, :4], scores[filtro], classes[filtro]
        caixas = np.stack(
            [xywh[:, 0] - xywh[:, 2] / 2, xywh[:, 1] - xywh[:, 3] / 2,
             xywh[:, 0] + xywh[:, 2] / 2, xywh[:, 1] + xywh[:, 3] / 2],
            axis=1,
        ) if len(xywh) else np.zeros((0, 4), dtype=np.float32)
        manter = nms(caixas, scores, limiar_iou)
        caixas, scores, classes = caixas[manter], scores[manter], classes[manter]

    resultado = []
    for caixa, score, classe in zip(caixas, scores, classes):
        x1 = float(np.clip((caixa[0] - pad_x) / escala, 0, largura))
        y1 = float(np.clip((caixa[1] - pad_y) / escala, 0, altura))
        x2 = float(np.clip((caixa[2] - pad_x) / escala, 0, largura))
        y2 = float(np.clip((caixa[3] - pad_y) / escala, 0, altura))
        resultado.append({
            "classe": nomes.get(str(int(classe)), str(int(classe))),
            "confianca": round(float(score), 3),
            "bbox": [round(x1), round(y1), round(x2), round(y2)],
        })
    return sorted(resultado, key=lambda c: c["confianca"], reverse=True)


def severidade(caixas: list[dict], largura: int, altura: int) -> str | None:
    """Regra PROVISÓRIA pela área da maior caixa. Será trocada pela regra do /detectar do Guilherme."""
    if not caixas:
        return None
    maior = max((c["bbox"][2] - c["bbox"][0]) * (c["bbox"][3] - c["bbox"][1]) for c in caixas)
    fracao = maior / max(largura * altura, 1)
    if fracao >= 0.15:
        return "alta"
    if fracao >= 0.05:
        return "media"
    return "baixa"


class DetectorBuracos:
    def __init__(self, caminho_modelo: str, limiar: float = 0.35, limiar_iou: float = 0.45, tamanho: int = 640):
        self.caminho = Path(caminho_modelo)
        self.limiar = limiar
        self.limiar_iou = limiar_iou
        self.tamanho = tamanho
        self._sessao = None
        self._entrada = None
        self._lock = threading.Lock()
        self.nomes = {"0": "buraco"}
        classes = self.caminho.with_name("classes.json")
        if classes.is_file():
            try:
                self.nomes = {str(k): str(v) for k, v in json.loads(classes.read_text(encoding="utf-8")).items()}
            except (ValueError, OSError):
                log.warning("classes.json inválido; usando {'0': 'buraco'}")

    @property
    def disponivel(self) -> bool:
        return self.caminho.is_file()

    @property
    def nome_modelo(self) -> str:
        return f"YOLO11n · {self.caminho.name}"

    def _sessao_onnx(self):
        with self._lock:
            if self._sessao is None:
                import onnxruntime as ort

                opcoes = ort.SessionOptions()
                opcoes.intra_op_num_threads = 1
                opcoes.inter_op_num_threads = 1
                self._sessao = ort.InferenceSession(
                    str(self.caminho), sess_options=opcoes, providers=["CPUExecutionProvider"]
                )
                self._entrada = self._sessao.get_inputs()[0].name
                log.info("Modelo de visão carregado: %s", self.caminho.name)
        return self._sessao

    def detectar(self, imagem: Image.Image) -> dict:
        if not self.disponivel:
            return {"disponivel": False, "motivo": "O modelo de visão ainda não foi instalado."}
        try:
            sessao = self._sessao_onnx()
            tensor, escala, pad_x, pad_y = letterbox(imagem, self.tamanho)
            saida = sessao.run(None, {self._entrada: tensor})[0]
            caixas = decodificar_saida(
                saida, self.limiar, self.limiar_iou, escala, pad_x, pad_y,
                imagem.width, imagem.height, self.nomes,
            )
        except Exception:  # a falha da IA nunca impede o cadastro
            log.exception("Falha na inferência de visão")
            return {"disponivel": False, "motivo": "A análise automática falhou. Escolha a categoria."}
        melhor = caixas[0] if caixas else None
        return {
            "disponivel": True,
            "categoria_sugerida": melhor["classe"] if melhor else None,
            "confianca": melhor["confianca"] if melhor else None,
            "severidade": severidade(caixas, imagem.width, imagem.height),
            "caixas": caixas[:10],
            "modelo": self.nome_modelo,
            "limiar": self.limiar,
        }
