"""Funções de apoio: serialização pública (sem dados pessoais), eventos e fotos."""

from __future__ import annotations

from datetime import UTC, datetime

from PIL import Image
from sqlalchemy.orm import Session

from .imagens import preparar_foto_e_imagem
from .models import Evento, Foto, Ocorrencia, agora


def iso(data: datetime | None) -> str | None:
    if data is None:
        return None
    return data.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")


def para_utc_ingenuo(data: datetime) -> datetime:
    if data.tzinfo is None:
        return data
    return data.astimezone(UTC).replace(tzinfo=None)


def foto_principal(ocorrencia: Ocorrencia) -> int | None:
    for foto in ocorrencia.fotos:
        if foto.tipo == "registro":
            return foto.id
    return None


def publico(o: Ocorrencia) -> dict:
    """Campos que qualquer pessoa pode ver. E-mail e consentimento nunca entram aqui."""
    return {
        "id": o.id,
        "protocolo": o.protocolo,
        "categoria": o.categoria,
        "categoria_ia": o.categoria_ia,
        "confianca_ia": o.confianca_ia,
        "severidade_ia": o.severidade_ia,
        "descricao": o.descricao,
        "bairro": o.bairro,
        "latitude": o.latitude,
        "longitude": o.longitude,
        "local_aproximado": o.local_aproximado,
        "status": o.status,
        "prioridade": o.prioridade,
        "prioridade_motivo": o.prioridade_motivo,
        "duplicada_de": o.duplicada_de,
        "confirmacoes": o.confirmacoes,
        "origem": o.origem,
        "simulado": o.simulado,
        "foto_id": foto_principal(o),
        "criado_em": iso(o.criado_em),
        "atualizado_em": iso(o.atualizado_em),
        "triado_em": iso(o.triado_em),
        "resolvido_em": iso(o.resolvido_em),
    }


def para_integracao(o: Ocorrencia) -> dict:
    """Usado pelo robô RPA e pelo export do Big Data, sempre atrás de chave própria."""
    dados = publico(o)
    dados.update({
        "autor_email": o.autor_email if o.consentimento else None,
        "consentimento": o.consentimento,
        "modelo_ia": o.modelo_ia,
        "robot_id": o.robot_id,
        "distancia_cm": o.distancia_cm,
        "test_location": o.test_location,
    })
    return dados


def registrar_evento(db: Session, ocorrencia: Ocorrencia, tipo: str, descricao: str, ator: str,
                     quando: datetime | None = None) -> Evento:
    evento = Evento(ocorrencia=ocorrencia, tipo=tipo, descricao=descricao, ator=ator, criado_em=quando or agora())
    db.add(evento)
    ocorrencia.atualizado_em = max(ocorrencia.atualizado_em or evento.criado_em, evento.criado_em)
    return evento


def anexar_foto(db: Session, ocorrencia: Ocorrencia, dados: bytes, tipo: str) -> Foto:
    return anexar_foto_com_imagem(db, ocorrencia, dados, tipo)[0]


def anexar_foto_com_imagem(db: Session, ocorrencia: Ocorrencia, dados: bytes, tipo: str) -> tuple[Foto, Image.Image]:
    """Guarda a foto tratada e devolve também a imagem decodificada, que é a analisada pela visão."""
    jpeg, largura, altura, imagem = preparar_foto_e_imagem(dados)
    foto = Foto(ocorrencia=ocorrencia, tipo=tipo, conteudo=jpeg, largura=largura, altura=altura)
    db.add(foto)
    return foto, imagem
