"""Ponte com a API de IA generativa do Guilherme (LLM local com base de conhecimento).

Se a API não responder no limite de tempo, o MVP mostra trechos oficiais da base, sem gerar texto.
"""

from __future__ import annotations

import json
import logging
import unicodedata
from pathlib import Path

import httpx

log = logging.getLogger("zelacidade.assistente")

MSG_OFFLINE = (
    "O assistente está indisponível no momento. Abaixo estão orientações oficiais da base de "
    "conhecimento, sem texto gerado por IA."
)


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return base.lower().replace(" ", "_")


def _url_segura(url) -> str | None:
    if isinstance(url, str) and url.startswith(("https://", "http://")):
        return url
    return None


def adaptar_resposta(dados: dict) -> dict:
    """Lê o formato do Guilherme (saida.* + fontes_detalhadas) e aceita também o formato achatado."""
    if not isinstance(dados, dict):
        raise ValueError("Resposta do assistente não é um objeto JSON")
    saida = dados.get("saida") if isinstance(dados.get("saida"), dict) else dados
    fontes = []
    for fonte in dados.get("fontes_detalhadas") or []:
        if isinstance(fonte, dict):
            fontes.append({
                "titulo": str(fonte.get("titulo") or fonte.get("title") or "Fonte oficial"),
                "orgao": fonte.get("orgao"),
                "url": _url_segura(fonte.get("link") or fonte.get("url")),
            })
    if not fontes:
        for fonte in saida.get("fontes") or []:
            if isinstance(fonte, dict):
                fontes.append({
                    "titulo": str(fonte.get("titulo") or "Fonte oficial"),
                    "orgao": fonte.get("orgao"),
                    "url": _url_segura(fonte.get("link") or fonte.get("url")),
                })
            else:
                fontes.append({"titulo": str(fonte), "orgao": None, "url": None})
    return {
        "resposta": str(saida.get("resposta") or "").strip(),
        "recusou": bool(saida.get("recusou", False)),
        "fontes": fontes[:8],
        "categoria": saida.get("categoria"),
        "risco": saida.get("risco"),
    }


class Assistente:
    def __init__(self, url: str, chave: str, timeout: float, trechos_path: str):
        self.url = url.rstrip("/")
        self.chave = chave
        self.timeout = timeout
        self.trechos = self._carregar_trechos(Path(trechos_path))

    @staticmethod
    def _carregar_trechos(caminho: Path) -> list[dict]:
        if not caminho.is_file():
            return []
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            log.warning("trechos.json inválido; modo offline sem trechos")
            return []
        return [t for t in dados if isinstance(t, dict) and t.get("texto")]

    @property
    def configurado(self) -> bool:
        return bool(self.url)

    @property
    def endpoint(self) -> str:
        return self.url if self.url.endswith("/perguntar") else f"{self.url}/perguntar"

    def trechos_para(self, categoria: str | None, limite: int = 3) -> list[dict]:
        alvo = _normalizar(categoria) if categoria else ""
        escolhidos = []
        for trecho in self.trechos:
            etiquetas = trecho.get("categorias") or [trecho.get("categoria") or ""]
            etiquetas = [_normalizar(e) for e in etiquetas if e]
            if not alvo or any(e and (e in alvo or alvo in e) for e in etiquetas):
                escolhidos.append({
                    "texto": str(trecho["texto"]),
                    "titulo": str(trecho.get("titulo") or "Fonte oficial"),
                    "orgao": trecho.get("orgao"),
                    "url": _url_segura(trecho.get("link") or trecho.get("url")),
                })
            if len(escolhidos) >= limite:
                break
        return escolhidos

    def perguntar(self, pergunta: str, contexto: str | None = None, categoria: str | None = None) -> dict:
        texto = pergunta.strip()
        if contexto:
            texto = f"{texto}\n\nContexto do registro: {contexto.strip()}"
        if self.configurado:
            cabecalhos = {"X-API-Key": self.chave} if self.chave else {}
            try:
                resposta = httpx.post(
                    self.endpoint, json={"pergunta": texto}, headers=cabecalhos, timeout=self.timeout
                )
                resposta.raise_for_status()
                return {"disponivel": True, **adaptar_resposta(resposta.json())}
            except (httpx.HTTPError, ValueError) as exc:
                log.warning("Assistente indisponível: %s", type(exc).__name__)
        return {"disponivel": False, "mensagem": MSG_OFFLINE, "trechos": self.trechos_para(categoria)}
