"""Uma chave por cliente de integração. Chave vazia no servidor = integração desligada (503)."""

from __future__ import annotations

import hashlib
import hmac

from fastapi import Header, HTTPException, Request, status


def _conferir(fornecida: str | None, esperada: str) -> None:
    if not esperada:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Integração não configurada no servidor.")
    if not fornecida or not hmac.compare_digest(fornecida.encode(), esperada.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credencial inválida.")


def chave_robo(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    _conferir(x_api_key, request.app.state.settings.robot_api_key)


def chave_rpa(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    _conferir(x_api_key, request.app.state.settings.rpa_api_key)


def chave_export(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    _conferir(x_api_key, request.app.state.settings.export_api_key)


def token_gestor(request: Request, authorization: str | None = Header(default=None)) -> None:
    token = authorization[7:].strip() if authorization and authorization.startswith("Bearer ") else None
    _conferir(token, request.app.state.settings.admin_token)


def hash_dispositivo(salt: str, dispositivo: str) -> str:
    """O identificador do aparelho nunca é guardado puro."""
    return hashlib.sha256(f"{salt}:{dispositivo}".encode()).hexdigest()
