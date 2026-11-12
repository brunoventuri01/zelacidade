"""Painel da organização (cliente B2B): fila por prioridade e troca de status com evidência."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..dominio import ORDEM_PRIORIDADE, STATUS, STATUS_GESTOR
from ..imagens import ImagemInvalida, ler_limitado
from ..models import Ocorrencia, agora
from ..seguranca import token_gestor
from ..servicos import anexar_foto, publico, registrar_evento

router = APIRouter(prefix="/api/v1/gestao", tags=["gestão"], dependencies=[Depends(token_gestor)])


@router.get("/ocorrencias")
def fila(db: Session = Depends(get_db), simulados: bool = Query(True)):
    consulta = select(Ocorrencia).options(selectinload(Ocorrencia.fotos)).where(Ocorrencia.status != "duplicada")
    if not simulados:
        consulta = consulta.where(Ocorrencia.simulado.is_(False))
    itens = list(db.scalars(consulta))
    itens.sort(key=lambda o: (o.status == "resolvida", ORDEM_PRIORIDADE.get(o.prioridade or "", 3), o.criado_em))
    return [publico(o) for o in itens]


@router.patch("/ocorrencias/{ocorrencia_id}")
def mudar_status(
    ocorrencia_id: int,
    db: Session = Depends(get_db),
    status: str = Form(...),
    comentario: str | None = Form(None),
    foto: UploadFile | None = File(None),
):
    if status not in STATUS_GESTOR:
        raise HTTPException(422, "Status permitido para a organização: em_andamento ou resolvida.")
    ocorrencia = db.get(Ocorrencia, ocorrencia_id, options=[selectinload(Ocorrencia.fotos)])
    if ocorrencia is None:
        raise HTTPException(404, "Ocorrência não encontrada.")
    if ocorrencia.status in ("duplicada", "resolvida"):
        raise HTTPException(409, f"Ocorrência já está como {STATUS[ocorrencia.status].lower()}.")
    tem_foto = foto is not None and bool(foto.filename)
    if status == "resolvida" and not tem_foto:
        raise HTTPException(422, "Para marcar como resolvida, anexe a foto da solução.")
    if tem_foto:
        try:
            anexar_foto(db, ocorrencia, ler_limitado(foto.file), "resolucao")
        except ImagemInvalida as exc:
            db.rollback()
            raise HTTPException(422, str(exc)) from exc
    comentario = (comentario or "").strip()[:500]
    ocorrencia.status = status
    if status == "resolvida":
        ocorrencia.resolvido_em = agora()
    texto = f"A organização responsável mudou o status para “{STATUS[status]}”"
    texto += " e anexou a foto da solução." if status == "resolvida" else "."
    if comentario:
        texto += f" Comentário: {comentario}"
    registrar_evento(db, ocorrencia, "status", texto, "gestor")
    db.commit()
    return publico(ocorrencia)
