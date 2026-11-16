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


def _coeficientes(n_destino: int, n_origem: int):
    """Coeficientes do cv2.INTER_LINEAR em ponto fixo (escala 2048), com as mesmas regras de borda."""
    pos = ((np.arange(n_destino) + 0.5) * (n_origem / n_destino) - 0.5).astype(np.float32)
    i0 = np.floor(pos).astype(np.int32)
    frac = (pos - i0).astype(np.float32)
    antes = i0 < 0
    frac[antes], i0[antes] = 0, 0
    depois = i0 >= n_origem - 1
    frac[depois], i0[depois] = 0, n_origem - 1
    i1 = np.minimum(i0 + 1, n_origem - 1)
    return i0, i1, np.rint((1.0 - frac) * 2048).astype(np.int32), np.rint(frac * 2048).astype(np.int32)


def redimensionar_bilinear(arr: np.ndarray, nova_l: int, nova_a: int) -> np.ndarray:
    """Reproduz bit a bit o cv2.resize(INTER_LINEAR) que o YOLO usa no letterbox, sem depender do OpenCV.

    O Pillow suaviza ao reduzir e arredonda diferente; isso muda as notas em até 0,008 e derruba caixas
    perto do limiar. Esta versão segue o caminho vetorizado do OpenCV e reproduz o esperado.json do Guilherme.
    """
    altura, largura = arr.shape[:2]
    if (largura, altura) == (nova_l, nova_a):
        return arr
    x0, x1, a0, a1 = _coeficientes(nova_l, largura)
    y0, y1, b0, b1 = _coeficientes(nova_a, altura)
    origem = arr.astype(np.int32)
    horizontal = origem[:, x0] * a0[None, :, None] + origem[:, x1] * a1[None, :, None]
    cima = ((horizontal[y0] >> 4) * b0[:, None, None]) >> 16
    baixo = ((horizontal[y1] >> 4) * b1[:, None, None]) >> 16
    return np.clip((cima + baixo + 2) >> 2, 0, 255).astype(np.uint8)


def letterbox(imagem: Image.Image, tamanho: int = 640, cor: int = 114):
    """Letterbox centralizado do Ultralytics: ganho = min(640/h, 640/w), borda cinza 114, RGB ÷255, NCHW.

    Devolve (tensor, ganho, borda_x, borda_y). A imagem é colada na borda arredondada, mas para desfazer o
    letterbox vale a borda fracionária (ex.: 106,5 px), como no config.json do Guilherme.
    """
    largura, altura = imagem.size
    escala = min(tamanho / largura, tamanho / altura)
    nova_l, nova_a = int(round(largura * escala)), int(round(altura * escala))
    borda_x, borda_y = (tamanho - nova_l) / 2, (tamanho - nova_a) / 2
    topo_x, topo_y = int(round(borda_x - 0.1)), int(round(borda_y - 0.1))
    tela = np.full((tamanho, tamanho, 3), cor, dtype=np.uint8)
    redim = redimensionar_bilinear(np.asarray(imagem.convert("RGB")), nova_l, nova_a)
    tela[topo_y:topo_y + nova_a, topo_x:topo_x + nova_l] = redim
    tensor = tela.astype(np.float32).transpose(2, 0, 1)[None] / 255.0
    return np.ascontiguousarray(tensor), escala, borda_x, borda_y


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
            "confianca": round(float(score), 4),
            "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            "area_relativa": round((x2 - x1) * (y2 - y1) / max(largura * altura, 1), 4),
        })
    return sorted(resultado, key=lambda c: c["confianca"], reverse=True)


def severidade(caixas: list[dict]) -> str:
    """Regra do Guilherme (a mesma do /detectar), aplicada depois do limiar e do NMS:
    0 caixas → nenhuma; maior área ≥ 0,05 ou ≥ 4 caixas → alta; maior área ≥ 0,015 ou ≥ 2 caixas → media;
    senão baixa. A área é relativa à imagem original."""
    if not caixas:
        return "nenhuma"
    maior = max(c["area_relativa"] for c in caixas)
    if maior >= 0.05 or len(caixas) >= 4:
        return "alta"
    if maior >= 0.015 or len(caixas) >= 2:
        return "media"
    return "baixa"


class DetectorBuracos:
    def __init__(self, caminho_modelo: str, limiar: float = 0.35, limiar_iou: float = 0.7, tamanho: int = 640):
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
            "severidade": severidade(caixas),
            "n_caixas": len(caixas),
            "caixas": caixas[:10],
            "modelo": self.nome_modelo,
            "limiar": self.limiar,
        }
