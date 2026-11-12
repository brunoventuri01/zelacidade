"""Contrato do robô Maker Lab (Roberto), mantido como o Bruno definiu."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..dominio import CATEGORIAS, EVENTO_ROBO_PARA_CATEGORIA
from ..models import Ocorrencia
from ..seguranca import chave_robo
from ..servicos import iso, para_utc_ingenuo, registrar_evento

router = APIRouter(prefix="/api/v1", tags=["robô Maker Lab"])


def _agora_utc() -> datetime:
    return datetime.now(UTC)


class RobotOccurrenceIn(BaseModel):
    robot_id: str = Field(min_length=2, max_length=80)
    event_type: Literal["obstacle", "pothole", "other"]
    distance_cm: float = Field(gt=0, le=1000)
    timestamp: datetime = Field(default_factory=_agora_utc)
    test_location: str = Field(min_length=2, max_length=200)
    simulated: bool
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


@router.post("/robot/occurrences", status_code=201, dependencies=[Depends(chave_robo)])
def registrar_do_robo(item: RobotOccurrenceIn, request: Request, db: Session = Depends(get_db)):
    area = request.app.state.area
    sem_coordenada = item.latitude is None or item.longitude is None
    latitude = area.centro_lat if sem_coordenada else item.latitude
    longitude = area.centro_lon if sem_coordenada else item.longitude
    categoria = EVENTO_ROBO_PARA_CATEGORIA[item.event_type]
    quando = para_utc_ingenuo(item.timestamp)

    ocorrencia = Ocorrencia(
        categoria=categoria,
        descricao=(f"{CATEGORIAS[categoria]} detectado pelo robô {item.robot_id} em {item.test_location}, "
                   f"a {item.distance_cm:.0f} cm."),
        bairro="Teste de bancada" if item.simulated else "Registro do robô",
        latitude=latitude,
        longitude=longitude,
        local_aproximado=sem_coordenada,
        origem="robo",
        simulado=item.simulated,
        robot_id=item.robot_id,
        distancia_cm=item.distance_cm,
        test_location=item.test_location,
        criado_em=quando,
        atualizado_em=quando,
    )
    db.add(ocorrencia)
    db.flush()
    texto = f"Registrada automaticamente pelo robô {item.robot_id}"
    texto += " em teste de bancada." if item.simulated else "."
    registrar_evento(db, ocorrencia, "criada", texto, "robo_maker", quando=quando)
    db.commit()
    return {"id": ocorrencia.id, "created_at": iso(ocorrencia.criado_em),
            "protocolo": ocorrencia.protocolo, "status": ocorrencia.status}
