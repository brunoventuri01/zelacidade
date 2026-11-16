"""Ponte com a API de IA generativa do Guilherme (LLM local com base de conhecimento).

Contrato (repo zelacidade-genai, api/main.py): POST /perguntar {"pergunta": até 500 caracteres}, cabeçalho
X-API-Key quando configurado. Resposta: saida.{resposta, categoria, risco, fontes, recusou},
fontes_detalhadas[{id, titulo, orgao, url}], recusa_por_limiar, latencia_s e aviso.

Se a API não responder no limite de tempo, o MVP mostra trechos oficiais da mesma base (trechos.json),
escolhidos pela categoria da ocorrência e pelas palavras da pergunta, sem gerar texto.
"""

from __future__ import annotations

import json
import logging
import math
import re
import unicodedata
from pathlib import Path

import httpx

from .dominio import CATEGORIAS

log = logging.getLogger("zelacidade.assistente")

LIMITE_PERGUNTA = 500  # o mesmo max_length da API do Guilherme

MSG_OFFLINE = (
    "O assistente está indisponível no momento. Abaixo estão orientações oficiais da base de "
    "conhecimento, sem texto gerado por IA."
)
AVISO_PADRAO = "Orientação informativa. A ZelaCidade não substitui os canais oficiais da Prefeitura (SP156)."

# categoria do ZelaCidade -> categorias da base do Guilherme
CATEGORIAS_DA_BASE = {
    "buraco": ["buraco_via"],
    "calcada_danificada": ["calcada"],
    "iluminacao": ["iluminacao"],
    "obstaculo": ["obstaculo_sinalizacao", "calcada"],
    "equipamento_danificado": ["canais"],
    "lixo_entulho": ["drenagem", "canais"],
    "outro": ["canais"],
}

# palavras do dia a dia -> termos usados nos documentos oficiais
SINONIMOS = {
    "bueiro": "bocas de lobo galerias",
    "boeiro": "bocas de lobo galerias",
    "alagamento": "alagada alagamentos enchente",
    "enchente": "alagada alagamentos",
    "lampada": "iluminacao",
    "luz": "iluminacao",
    "escuro": "iluminacao apagada",
    "escura": "iluminacao apagada",
    "asfalto": "tapa buraco",
    "cratera": "buraco tapa",
    "entulho": "obstaculo",
    "bloqueando": "obstaculo",
    "bloqueada": "obstaculo",
}

PALAVRAS_VAZIAS = {
    "que", "com", "para", "pra", "por", "uma", "uns", "umas", "dos", "das", "nos", "nas", "num", "numa",
    "sua", "seu", "minha", "meu", "tem", "ter", "como", "qual", "quais", "quem", "onde", "quando",
    "faco", "fazer", "devo", "posso", "pode", "aqui", "esta", "isso", "esse", "essa", "este", "muito",
    "mais", "sobre", "rua", "frente", "casa", "bairro", "contexto", "registro", "categoria", "severidade",
}


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return base.lower()


def _radicais(texto: str) -> set[str]:
    """Tokens sem acento, sem palavras vazias, com plural simples cortado e radical de 6 letras."""
    radicais = set()
    for token in re.findall(r"[a-z0-9]+", _normalizar(texto)):
        if len(token) < 3 or token in PALAVRAS_VAZIAS:
            continue
        if len(token) > 4 and token.endswith("s"):
            token = token[:-1]
        radicais.add(token[:6])
    return radicais


def _url_segura(url) -> str | None:
    if isinstance(url, str) and url.startswith(("https://", "http://")):
        return url
    return None


def montar_pergunta(pergunta: str, contexto: str | None) -> str:
    texto = pergunta.strip()
    if not contexto or not contexto.strip():
        return texto[:LIMITE_PERGUNTA]
    extra = f"\n\nContexto do registro: {contexto.strip()}"
    return texto[: max(0, LIMITE_PERGUNTA - len(extra))].rstrip() + extra


def adaptar_resposta(dados: dict) -> dict:
    """Lê o formato do Guilherme (saida.* + fontes_detalhadas) e aceita também o formato achatado."""
    if not isinstance(dados, dict):
        raise ValueError("Resposta do assistente não é um objeto JSON")
    saida = dados.get("saida") if isinstance(dados.get("saida"), dict) else dados
    fontes = []
    for fonte in dados.get("fontes_detalhadas") or []:
        if isinstance(fonte, dict):
            fontes.append({
                "id": fonte.get("id"),
                "titulo": str(fonte.get("titulo") or fonte.get("title") or "Fonte oficial"),
                "orgao": fonte.get("orgao"),
                "url": _url_segura(fonte.get("url") or fonte.get("link")),
            })
    if not fontes:
        for fonte in saida.get("fontes") or []:
            if isinstance(fonte, dict):
                fontes.append({
                    "id": fonte.get("id"),
                    "titulo": str(fonte.get("titulo") or "Fonte oficial"),
                    "orgao": fonte.get("orgao"),
                    "url": _url_segura(fonte.get("url") or fonte.get("link")),
                })
            else:
                fontes.append({"id": str(fonte), "titulo": str(fonte), "orgao": None, "url": None})
    return {
        "resposta": str(saida.get("resposta") or "").strip(),
        "recusou": bool(saida.get("recusou", False)),
        "recusa_por_limiar": bool(dados.get("recusa_por_limiar", False)),
        "fontes": fontes[:8],
        "categoria": saida.get("categoria"),
        "risco": saida.get("risco"),
        "aviso": str(dados.get("aviso") or AVISO_PADRAO),
    }


class Assistente:
    def __init__(self, url: str, chave: str, timeout: float, trechos_path: str):
        self.url = url.rstrip("/")
        self.chave = chave
        self.timeout = timeout
        self.trechos = self._carregar_trechos(Path(trechos_path))
        self._indice = [_radicais(f"{t.get('titulo', '')} {t['texto']}") for t in self.trechos]
        # palavras raras na base pesam mais que as comuns (IDF): "apagado" diz mais que "poste"
        total = max(len(self._indice), 1)
        frequencia: dict[str, int] = {}
        for radicais in self._indice:
            for radical in radicais:
                frequencia[radical] = frequencia.get(radical, 0) + 1
        self._peso = {radical: math.log(1 + total / n) for radical, n in frequencia.items()}

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

    def buscar_trechos(self, pergunta: str = "", categoria: str | None = None, limite: int = 3) -> list[dict]:
        """Busca simples e explicável: palavras em comum com a pergunta, pesadas pela raridade na base,
        mais um bônus para a categoria da ocorrência."""
        alvo = set(CATEGORIAS_DA_BASE.get(categoria or "", []))
        consulta = f"{pergunta} {CATEGORIAS.get(categoria or '', '')}"
        extras = [SINONIMOS[p] for p in re.findall(r"[a-z]+", _normalizar(consulta)) if p in SINONIMOS]
        termos = _radicais(" ".join([consulta, *extras]))
        bonus = max(self._peso.values(), default=1.0)
        pontuados = []
        for posicao, (trecho, radicais) in enumerate(zip(self.trechos, self._indice)):
            pontos = sum(self._peso[r] for r in termos & radicais)
            pontos += bonus if trecho.get("categoria") in alvo else 0
            if pontos > 0:
                pontuados.append((-pontos, posicao, trecho))
        pontuados.sort()
        return [
            {
                "id": t.get("id"),
                "texto": str(t["texto"]),
                "titulo": str(t.get("titulo") or "Fonte oficial"),
                "orgao": t.get("orgao"),
                "url": _url_segura(t.get("link") or t.get("url")),
            }
            for _, _, t in pontuados[:limite]
        ]

    def perguntar(self, pergunta: str, contexto: str | None = None, categoria: str | None = None) -> dict:
        texto = montar_pergunta(pergunta, contexto)
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
        return {
            "disponivel": False,
            "mensagem": MSG_OFFLINE,
            "aviso": AVISO_PADRAO,
            "trechos": self.buscar_trechos(pergunta, categoria),
        }
