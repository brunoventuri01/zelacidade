"""Aplicação do ZelaCidade: API + site React no mesmo container (porta 8000)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CollectorRegistry
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import models  # noqa: F401  (registra as tabelas no Base)
from .area import AreaPiloto
from .assistente import Assistente
from .config import Settings
from .db import Base, criar_engine
from .routers import gestao, integracao, publico, robo
from .visao import DetectorBuracos

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

CSP = (
    "default-src 'self'; img-src 'self' data: blob: https://tile.openstreetmap.org; "
    "style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)
SEM_CSP = ("/docs", "/redoc", "/openapi.json")


class SPAStaticFiles(StaticFiles):
    """Serve o React compilado; rotas do site (ex.: /ocorrencias/12) caem no index.html."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and not path.startswith("api"):
                return await super().get_response("index.html", scope)
            raise


async def cabecalhos_de_seguranca(request: Request, call_next):
    resposta = await call_next(request)
    resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
    resposta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resposta.headers.setdefault("Permissions-Policy", "camera=(self), geolocation=(self), microphone=()")
    if not request.url.path.startswith(SEM_CSP):
        resposta.headers.setdefault("Content-Security-Policy", CSP)
    if request.url.path.startswith("/assets/"):
        resposta.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resposta


def health(request: Request):
    """Usado pelo HEALTHCHECK do container, pelo smoke test do CI e pelo monitor de disponibilidade."""
    estado = request.app.state
    try:
        with estado.engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
    except Exception:
        logging.getLogger("zelacidade").exception("Banco indisponível no /health")
        return JSONResponse({"status": "erro", "banco": "indisponivel"}, status_code=503)
    return {
        "status": "ok",
        "banco": "ok",
        "visao": estado.detector.disponivel,
        "assistente": estado.assistente.configurado,
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    engine = criar_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(
        title="ZelaCidade API",
        version="1.0.0",
        description="Zeladoria colaborativa: registro com foto, triagem automática e indicadores.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = sessionmaker(bind=engine, expire_on_commit=False)
    app.state.area = AreaPiloto.carregar(settings.area_piloto_path)
    app.state.detector = DetectorBuracos(settings.cv_model_path, settings.cv_conf_limiar)
    app.state.assistente = Assistente(
        settings.genai_api_url, settings.genai_api_key, settings.genai_timeout, settings.trechos_path
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.middleware("http")(cabecalhos_de_seguranca)

    Instrumentator(registry=CollectorRegistry(), excluded_handlers=["/metrics", "/health"]).instrument(
        app
    ).expose(app, include_in_schema=False)

    app.add_api_route("/health", health, methods=["GET"], tags=["operação"])
    app.include_router(publico.router)
    app.include_router(gestao.router)
    app.include_router(integracao.router)
    app.include_router(robo.router)

    estatico = Path(settings.static_dir) if settings.static_dir else None
    if estatico and (estatico / "index.html").is_file():
        app.mount("/", SPAStaticFiles(directory=estatico, html=True), name="site")
    return app


app = create_app()
