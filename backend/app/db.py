"""Conexão com o banco: Postgres (Neon) em produção, SQLite nos testes."""

from __future__ import annotations

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def criar_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if url in ("sqlite://", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool
        return create_engine(url, **kwargs)
    # pool pequeno: o F1 roda um único worker e o Neon suspende o banco ocioso
    return create_engine(url, pool_pre_ping=True, pool_size=3, max_overflow=2, pool_recycle=300)


def get_db(request: Request):
    db: Session = request.app.state.sessionmaker()
    try:
        yield db
    finally:
        db.close()
