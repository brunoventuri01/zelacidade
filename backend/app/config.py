"""Configuração lida das variáveis de ambiente. Nenhuma credencial fica no código."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
log = logging.getLogger("zelacidade")


def _env(nome: str, padrao: str = "") -> str:
    return os.environ.get(nome, padrao).strip()


def _segredo(nome: str) -> str:
    """Valores vazios ou de exemplo (CHANGE_ME) nunca liberam acesso."""
    valor = _env(nome)
    if not valor or valor.upper().startswith("CHANGE_ME"):
        return ""
    return valor


def normalizar_url_banco(url: str) -> str:
    """Aceita a string do Neon (postgresql://...) e usa o driver psycopg 3."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


@dataclass(frozen=True)
class Settings:
    database_url: str
    robot_api_key: str = ""
    rpa_api_key: str = ""
    export_api_key: str = ""
    admin_token: str = ""
    genai_api_url: str = ""
    genai_api_key: str = ""
    genai_timeout: float = 60.0
    cv_model_path: str = str(BASE_DIR.parent / "models" / "visao" / "best.onnx")
    cv_conf_limiar: float = 0.35
    hash_salt: str = "zelacidade-local"
    static_dir: str = ""
    area_piloto_path: str = str(BASE_DIR / "data" / "area_piloto.json")
    trechos_path: str = str(BASE_DIR / "data" / "trechos.json")

    @classmethod
    def from_env(cls) -> "Settings":
        url = _env("DATABASE_URL")
        if not url:
            raise RuntimeError(
                "DATABASE_URL não definida. Em produção ela vem dos App Settings do Azure; "
                "no PC, use o docker compose ou exporte DATABASE_URL."
            )
        salt = _segredo("HASH_SALT")
        if not salt:
            log.warning("HASH_SALT não definido: usando valor local. Defina em produção.")
            salt = "zelacidade-local"
        return cls(
            database_url=normalizar_url_banco(url),
            robot_api_key=_segredo("ROBOT_API_KEY"),
            rpa_api_key=_segredo("RPA_API_KEY"),
            export_api_key=_segredo("EXPORT_API_KEY"),
            admin_token=_segredo("ADMIN_TOKEN"),
            genai_api_url=_env("GENAI_API_URL"),
            genai_api_key=_segredo("GENAI_API_KEY"),
            genai_timeout=float(_env("GENAI_TIMEOUT", "60") or 60),
            cv_model_path=_env("CV_MODEL_PATH", cls.cv_model_path) or cls.cv_model_path,
            cv_conf_limiar=float(_env("CV_CONF_LIMIAR", "0.35") or 0.35),
            hash_salt=salt,
            static_dir=_env("STATIC_DIR"),
            area_piloto_path=_env("AREA_PILOTO_PATH", cls.area_piloto_path) or cls.area_piloto_path,
            trechos_path=_env("TRECHOS_PATH", cls.trechos_path) or cls.trechos_path,
        )
