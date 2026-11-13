"""Rotas usadas pelo site: registrar, consultar, confirmar, painel e assistente."""

from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from PIL import Image
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..dominio import CATEGORIAS, ORIGENS, PRIORIDADES, STATUS, STATUS_ABERTOS, protocolo
from ..imagens import ImagemInvalida, ler_limitado, preparar_foto_e_imagem
from ..models import Confirmacao, Foto, Ocorrencia, PainelSnapshot
from ..seguranca import hash_dispositivo
from ..servicos import anexar_foto, anexar_foto_com_imagem, iso, publico, registrar_evento

router = APIRouter(prefix="/api/v1", tags=["público"])

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")


def _carregar(db: Session, ocorrencia_id: int) -> Ocorrencia:
    ocorrencia = db.get(
        Ocorrencia,
        ocorrencia_id,
        options=[
            selectinload(Ocorrencia.fotos),
            selectinload(Ocorrencia.eventos),
            selectinload(Ocorrencia.confirmacoes_registradas),
        ],
    )
    if ocorrencia is None:
        raise HTTPException(404, "Ocorrência não encontrada.")
    return ocorrencia


def _analisar(request: Request, imagem: Image.Image) -> dict:
    detector = request.app.state.detector
    if not detector.disponivel:
        return {"disponivel": False, "motivo": "O modelo de visão ainda não foi instalado."}
    return detector.detectar(imagem)


def _tem_arquivo(foto: UploadFile | None) -> bool:
    return foto is not None and bool(foto.filename)


@router.get("/config")
def configuracao(request: Request):
    estado = request.app.state
    return {
        "area": estado.area.como_dict(),
        "categorias": [{"valor": k, "rotulo": v} for k, v in CATEGORIAS.items()],
        "status": [{"valor": k, "rotulo": v} for k, v in STATUS.items()],
        "prioridades": [{"valor": k, "rotulo": v} for k, v in PRIORIDADES.items()],
        "origens": [{"valor": k, "rotulo": v} for k, v in ORIGENS.items()],
        "visao": {"disponivel": estado.detector.disponivel, "limiar": estado.detector.limiar},
        "assistente": {"configurado": estado.assistente.configurado},
    }


@router.post("/ia/classificar")
def classificar(request: Request, foto: UploadFile = File(...)):
    try:
        _, _, _, imagem = preparar_foto_e_imagem(ler_limitado(foto.file))
    except ImagemInvalida as exc:
        raise HTTPException(422, str(exc)) from exc
    return _analisar(request, imagem)


@router.post("/ocorrencias", status_code=201)
def criar_ocorrencia(
    request: Request,
    db: Session = Depends(get_db),
    categoria: str = Form(...),
    descricao: str = Form(...),
    bairro: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    email: str | None = Form(None),
    consentimento: bool = Form(False),
    foto: UploadFile | None = File(None),
):
    descricao, bairro = descricao.strip(), bairro.strip()
    email = (email or "").strip() or None
    if categoria not in CATEGORIAS:
        raise HTTPException(422, "Categoria inválida.")
    if not 3 <= len(descricao) <= 1000:
        raise HTTPException(422, "Descreva o problema em 3 a 1000 caracteres.")
    if not 2 <= len(bairro) <= 80:
        raise HTTPException(422, "Informe o bairro.")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise HTTPException(422, "Localização inválida.")
    if email and not consentimento:
        raise HTTPException(422, "Para receber avisos por e-mail, marque o consentimento.")
    if email and (len(email) > 254 or not EMAIL_RE.match(email)):
        raise HTTPException(422, "E-mail inválido.")

    ocorrencia = Ocorrencia(
        categoria=categoria,
        descricao=descricao,
        bairro=bairro,
        latitude=latitude,
        longitude=longitude,
        origem="cidadao",
        autor_email=email if consentimento else None,
        consentimento=bool(consentimento and email),
    )
    db.add(ocorrencia)
    db.flush()

    ia = None
    if _tem_arquivo(foto):
        try:
            _, imagem = anexar_foto_com_imagem(db, ocorrencia, ler_limitado(foto.file), "registro")
        except ImagemInvalida as exc:
            db.rollback()
            raise HTTPException(422, str(exc)) from exc
        ia = _analisar(request, imagem)
        if ia.get("disponivel"):
            ocorrencia.categoria_ia = ia.get("categoria_sugerida")
            ocorrencia.confianca_ia = ia.get("confianca")
            ocorrencia.severidade_ia = ia.get("severidade")
            ocorrencia.modelo_ia = ia.get("modelo")

    registrar_evento(db, ocorrencia, "criada", "Registrada por um morador.", "morador")
    if ia and ia.get("disponivel"):
        escolhida = CATEGORIAS[categoria]
        if ocorrencia.categoria_ia:
            sugerida = CATEGORIAS.get(ocorrencia.categoria_ia, ocorrencia.categoria_ia)
            texto = (f"A IA sugeriu “{sugerida}” com {round((ocorrencia.confianca_ia or 0) * 100)}% de "
                     f"confiança. O morador confirmou “{escolhida}”.")
        else:
            texto = f"A IA não encontrou buraco na foto. O morador escolheu “{escolhida}”."
        registrar_evento(db, ocorrencia, "ia", texto, "ia")
    db.commit()
    return {"id": ocorrencia.id, "protocolo": ocorrencia.protocolo, "status": ocorrencia.status, "ia": ia}


@router.get("/ocorrencias")
def listar_ocorrencias(
    db: Session = Depends(get_db),
    status: str | None = Query(None),
    categoria: str | None = Query(None),
    bairro: str | None = Query(None),
    origem: str | None = Query(None),
    simulados: bool = Query(True),
    limite: int = Query(500, ge=1, le=1000),
):
    consulta = select(Ocorrencia).options(selectinload(Ocorrencia.fotos))
    if status:
        consulta = consulta.where(Ocorrencia.status.in_(status.split(",")))
    if categoria:
        consulta = consulta.where(Ocorrencia.categoria == categoria)
    if bairro:
        consulta = consulta.where(Ocorrencia.bairro == bairro)
    if origem:
        consulta = consulta.where(Ocorrencia.origem == origem)
    if not simulados:
        consulta = consulta.where(Ocorrencia.simulado.is_(False))
    consulta = consulta.order_by(Ocorrencia.criado_em.desc()).limit(limite)
    return [publico(o) for o in db.scalars(consulta)]


@router.get("/ocorrencias/{ocorrencia_id}")
def detalhar_ocorrencia(ocorrencia_id: int, db: Session = Depends(get_db)):
    o = _carregar(db, ocorrencia_id)
    return {
        **publico(o),
        "duplicada_de_protocolo": protocolo(o.duplicada_de) if o.duplicada_de else None,
        "fotos": [{"id": f.id, "tipo": f.tipo} for f in o.fotos],
        "eventos": [
            {"tipo": e.tipo, "descricao": e.descricao, "ator": e.ator, "criado_em": iso(e.criado_em)}
            for e in o.eventos
        ],
        "comentarios": [
            {"comentario": c.comentario, "foto_id": c.foto_id, "criado_em": iso(c.criado_em)}
            for c in o.confirmacoes_registradas
            if c.comentario or c.foto_id
        ],
    }


@router.post("/ocorrencias/{ocorrencia_id}/confirmacoes", status_code=201)
def confirmar_ocorrencia(
    ocorrencia_id: int,
    request: Request,
    db: Session = Depends(get_db),
    x_dispositivo: str | None = Header(None),
    comentario: str | None = Form(None),
    foto: UploadFile | None = File(None),
):
    if not x_dispositivo or not 8 <= len(x_dispositivo) <= 100:
        raise HTTPException(400, "Identificador do aparelho ausente.")
    o = _carregar(db, ocorrencia_id)
    if o.status in ("resolvida", "duplicada"):
        raise HTTPException(409, "Esta ocorrência não recebe mais confirmações.")
    marca = hash_dispositivo(request.app.state.settings.hash_salt, x_dispositivo)
    ja_confirmou = db.scalar(
        select(Confirmacao.id).where(Confirmacao.ocorrencia_id == o.id, Confirmacao.dispositivo_hash == marca)
    )
    if ja_confirmou:
        raise HTTPException(409, "Você já confirmou esta ocorrência neste aparelho.")
    comentario = (comentario or "").strip()[:500] or None

    evidencia = None
    if _tem_arquivo(foto):
        try:
            evidencia = anexar_foto(db, o, ler_limitado(foto.file), "evidencia")
        except ImagemInvalida as exc:
            db.rollback()
            raise HTTPException(422, str(exc)) from exc
        db.flush()
    db.add(Confirmacao(ocorrencia=o, dispositivo_hash=marca, comentario=comentario,
                       foto_id=evidencia.id if evidencia else None))
    o.confirmacoes += 1
    partes = ["Um morador confirmou o problema"]
    if evidencia:
        partes.append("enviou uma foto")
    if comentario:
        partes.append("deixou um comentário")
    texto = partes[0] + ("" if len(partes) == 1 else ", " + " e ".join(partes[1:])) + "."
    registrar_evento(db, o, "confirmacao", texto, "morador")
    db.commit()
    return {"confirmacoes": o.confirmacoes}


@router.get("/fotos/{foto_id}")
def obter_foto(foto_id: int, db: Session = Depends(get_db)):
    foto = db.get(Foto, foto_id)
    if foto is None:
        raise HTTPException(404, "Foto não encontrada.")
    return Response(content=foto.conteudo, media_type=foto.mime,
                    headers={"Cache-Control": "public, max-age=86400"})


@router.get("/painel")
def painel(db: Session = Depends(get_db)):
    snapshot = db.scalars(
        select(PainelSnapshot).order_by(PainelSnapshot.importado_em.desc(), PainelSnapshot.id.desc()).limit(1)
    ).first()
    ouro = None
    if snapshot:
        ouro = {
            "fonte": snapshot.fonte,
            "gerado_em": iso(snapshot.gerado_em),
            "importado_em": iso(snapshot.importado_em),
            **json.loads(snapshot.payload),
        }
    por_status = dict(db.execute(select(Ocorrencia.status, func.count()).group_by(Ocorrencia.status)).all())
    abertas = dict(db.execute(
        select(Ocorrencia.categoria, func.count())
        .where(Ocorrencia.status.in_(STATUS_ABERTOS))
        .group_by(Ocorrencia.categoria)
    ).all())
    simulados = db.scalar(select(func.count()).where(Ocorrencia.simulado.is_(True))) or 0
    return {
        "ouro": ouro,
        "ao_vivo": {
            "total": sum(por_status.values()),
            "simulados": simulados,
            "por_status": por_status,
            "abertas_por_categoria": abertas,
        },
    }


class PerguntaIn(BaseModel):
    pergunta: str = Field(min_length=3, max_length=500)
    contexto: str | None = Field(default=None, max_length=200)
    categoria: str | None = Field(default=None, max_length=40)


@router.post("/assistente")
def perguntar(item: PerguntaIn, request: Request):
    return request.app.state.assistente.perguntar(item.pergunta, item.contexto, item.categoria)
