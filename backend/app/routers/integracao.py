"""Integrações com chave própria: robô RPA (triagem e painel) e export diário para o Big Data."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..dominio import PRIORIDADES, STATUS
from ..models import Ocorrencia, PainelSnapshot, agora
from ..seguranca import chave_export, chave_rpa
from ..servicos import para_integracao, para_utc_ingenuo, publico, registrar_evento

router = APIRouter(prefix="/api/v1", tags=["integrações"])

# Brasil sem horário de verão desde 2019: São Paulo é sempre UTC-3
FUSO_SP = timezone(timedelta(hours=-3))


@router.get("/integracao/ocorrencias", dependencies=[Depends(chave_rpa)])
def listar_para_rpa(
    db: Session = Depends(get_db),
    status: str = Query("recebida", description="Um ou mais status separados por vírgula"),
    dias: int | None = Query(None, ge=1, le=365, description="Só as criadas nos últimos N dias"),
    limite: int = Query(500, ge=1, le=2000),
):
    consulta = (
        select(Ocorrencia)
        .options(selectinload(Ocorrencia.fotos))
        .where(Ocorrencia.status.in_(status.split(",")))
    )
    if dias:
        consulta = consulta.where(Ocorrencia.criado_em >= agora() - timedelta(days=dias))
    consulta = consulta.order_by(Ocorrencia.criado_em).limit(limite)
    return [para_integracao(o) for o in db.scalars(consulta)]


class TriagemIn(BaseModel):
    status: Literal["triada", "duplicada", "precisa_info"]
    prioridade: Literal["alta", "media", "baixa"] | None = None
    motivo: str = Field(min_length=3, max_length=500)
    duplicada_de: int | None = None


@router.patch("/integracao/ocorrencias/{ocorrencia_id}/triagem", dependencies=[Depends(chave_rpa)])
def registrar_triagem(ocorrencia_id: int, item: TriagemIn, db: Session = Depends(get_db)):
    ocorrencia = db.get(Ocorrencia, ocorrencia_id, options=[selectinload(Ocorrencia.fotos)])
    if ocorrencia is None:
        raise HTTPException(404, "Ocorrência não encontrada.")
    if ocorrencia.status not in ("recebida", "precisa_info"):
        raise HTTPException(409, f"Ocorrência já triada (status atual: {ocorrencia.status}).")
    if item.status == "triada" and not item.prioridade:
        raise HTTPException(422, "Informe a prioridade da triagem.")

    if item.status == "duplicada":
        if not item.duplicada_de or item.duplicada_de == ocorrencia.id:
            raise HTTPException(422, "Informe a ocorrência original em duplicada_de.")
        original = db.get(Ocorrencia, item.duplicada_de)
        if original is None:
            raise HTTPException(422, "Ocorrência original não encontrada.")
        original.confirmacoes += 1
        registrar_evento(
            db, original, "confirmacao",
            f"O registro {ocorrencia.protocolo} foi identificado como duplicado e somado como confirmação.",
            "robo_rpa",
        )
        ocorrencia.duplicada_de = original.id
        texto = f"Marcada como duplicada de {original.protocolo}. Motivo: {item.motivo}"
    elif item.status == "triada":
        texto = f"Triada pelo robô com prioridade {PRIORIDADES[item.prioridade].lower()}. Motivo: {item.motivo}"
    else:
        texto = f"O robô de triagem pediu mais informação. Motivo: {item.motivo}"

    ocorrencia.status = item.status
    ocorrencia.prioridade = item.prioridade if item.status == "triada" else None
    ocorrencia.prioridade_motivo = item.motivo
    ocorrencia.triado_em = agora()
    registrar_evento(db, ocorrencia, "triagem", texto, "robo_rpa")
    db.commit()
    return publico(ocorrencia)


class PainelIn(BaseModel):
    fonte: str = Field(min_length=3, max_length=200)
    gerado_em: datetime
    linhas: list[dict] = Field(min_length=1, max_length=5000)
    kpis: dict = Field(default_factory=dict)


@router.post("/integracao/painel", status_code=201, dependencies=[Depends(chave_rpa)])
def publicar_painel(item: PainelIn, db: Session = Depends(get_db)):
    snapshot = PainelSnapshot(
        fonte=item.fonte,
        gerado_em=para_utc_ingenuo(item.gerado_em),
        payload=json.dumps({"linhas": item.linhas, "kpis": item.kpis}, ensure_ascii=False, default=str),
    )
    db.add(snapshot)
    db.commit()
    return {"id": snapshot.id, "linhas": len(item.linhas)}


@router.get("/export/ocorrencias", dependencies=[Depends(chave_export)])
def exportar_ocorrencias(data: date = Query(..., description="Dia de coleta (AAAA-MM-DD, horário de São Paulo)"),
                         db: Session = Depends(get_db)):
    """NDJSON com as ocorrências criadas OU atualizadas no dia: a Prata resolve com MERGE pelo id."""
    inicio = datetime.combine(data, time.min, tzinfo=FUSO_SP).astimezone(UTC).replace(tzinfo=None)
    fim = inicio + timedelta(days=1)
    consulta = (
        select(Ocorrencia)
        .options(selectinload(Ocorrencia.fotos))
        .where(or_(
            and_(Ocorrencia.criado_em >= inicio, Ocorrencia.criado_em < fim),
            and_(Ocorrencia.atualizado_em >= inicio, Ocorrencia.atualizado_em < fim),
        ))
        .order_by(Ocorrencia.id)
    )
    linhas = [
        json.dumps({**para_integracao(o), "status_rotulo": STATUS.get(o.status), "data_coleta": data.isoformat()},
                   ensure_ascii=False)
        for o in db.scalars(consulta)
    ]
    corpo = "\n".join(linhas) + ("\n" if linhas else "")
    return Response(corpo, media_type="application/x-ndjson")
