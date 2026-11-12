"""Tabelas do MVP. Datas sempre em UTC, sem fuso, para valer igual no Postgres e no SQLite."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
from .dominio import protocolo


def agora() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Ocorrencia(Base):
    __tablename__ = "ocorrencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    categoria: Mapped[str] = mapped_column(String(40), index=True)
    descricao: Mapped[str] = mapped_column(Text)
    bairro: Mapped[str] = mapped_column(String(80), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    local_aproximado: Mapped[bool] = mapped_column(Boolean, default=False)

    # sugestão da visão computacional; quem decide a categoria é o morador
    categoria_ia: Mapped[str | None] = mapped_column(String(40), nullable=True)
    confianca_ia: Mapped[float | None] = mapped_column(Float, nullable=True)
    severidade_ia: Mapped[str | None] = mapped_column(String(10), nullable=True)
    modelo_ia: Mapped[str | None] = mapped_column(String(80), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="recebida", index=True)
    prioridade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    prioridade_motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    duplicada_de: Mapped[int | None] = mapped_column(ForeignKey("ocorrencias.id"), nullable=True)
    confirmacoes: Mapped[int] = mapped_column(Integer, default=0)

    origem: Mapped[str] = mapped_column(String(10), default="cidadao", index=True)
    simulado: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # dado pessoal: só existe com consentimento e nunca sai nas rotas públicas
    autor_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    consentimento: Mapped[bool] = mapped_column(Boolean, default=False)

    robot_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    distancia_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    test_location: Mapped[str | None] = mapped_column(String(200), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora, index=True)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=agora, index=True)
    triado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolvido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    fotos: Mapped[list["Foto"]] = relationship(
        back_populates="ocorrencia", cascade="all, delete-orphan", order_by="Foto.id"
    )
    eventos: Mapped[list["Evento"]] = relationship(
        back_populates="ocorrencia", cascade="all, delete-orphan", order_by="Evento.id"
    )
    confirmacoes_registradas: Mapped[list["Confirmacao"]] = relationship(
        back_populates="ocorrencia", cascade="all, delete-orphan", order_by="Confirmacao.id"
    )

    @property
    def protocolo(self) -> str:
        return protocolo(self.id)


class Foto(Base):
    __tablename__ = "fotos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ocorrencia_id: Mapped[int] = mapped_column(ForeignKey("ocorrencias.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(12))  # registro | evidencia | resolucao
    conteudo: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    mime: Mapped[str] = mapped_column(String(30), default="image/jpeg")
    largura: Mapped[int] = mapped_column(Integer)
    altura: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora)

    ocorrencia: Mapped[Ocorrencia] = relationship(back_populates="fotos")


class Evento(Base):
    """Linha do tempo pública e trilha de auditoria de cada ocorrência."""

    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ocorrencia_id: Mapped[int] = mapped_column(ForeignKey("ocorrencias.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(30))
    descricao: Mapped[str] = mapped_column(Text)
    ator: Mapped[str] = mapped_column(String(20))  # morador | ia | robo_rpa | robo_maker | gestor | sistema
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora)

    ocorrencia: Mapped[Ocorrencia] = relationship(back_populates="eventos")


class Confirmacao(Base):
    __tablename__ = "confirmacoes"
    __table_args__ = (UniqueConstraint("ocorrencia_id", "dispositivo_hash", name="uq_confirmacao_dispositivo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ocorrencia_id: Mapped[int] = mapped_column(ForeignKey("ocorrencias.id"), index=True)
    dispositivo_hash: Mapped[str] = mapped_column(String(64))
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    foto_id: Mapped[int | None] = mapped_column(ForeignKey("fotos.id"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora)

    ocorrencia: Mapped[Ocorrencia] = relationship(back_populates="confirmacoes_registradas")


class PainelSnapshot(Base):
    """Retrato da tabela Ouro publicado pelo robô RPA."""

    __tablename__ = "painel_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fonte: Mapped[str] = mapped_column(String(200))
    gerado_em: Mapped[datetime] = mapped_column(DateTime)
    payload: Mapped[str] = mapped_column(Text)  # JSON
    importado_em: Mapped[datetime] = mapped_column(DateTime, default=agora)
