"""Área piloto configurável em um único arquivo JSON (centro, limites e bairros)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AreaPiloto:
    nome: str
    cidade: str
    provisoria: bool
    centro_lat: float
    centro_lon: float
    sul: float
    norte: float
    oeste: float
    leste: float
    zoom: int
    bairros: tuple[str, ...]

    @classmethod
    def carregar(cls, caminho: str) -> "AreaPiloto":
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
        limites = dados["limites"]
        return cls(
            nome=dados["nome"],
            cidade=dados.get("cidade", "São Paulo"),
            provisoria=bool(dados.get("provisoria", False)),
            centro_lat=float(dados["centro"]["latitude"]),
            centro_lon=float(dados["centro"]["longitude"]),
            sul=float(limites["sul"]),
            norte=float(limites["norte"]),
            oeste=float(limites["oeste"]),
            leste=float(limites["leste"]),
            zoom=int(dados.get("zoom", 14)),
            bairros=tuple(dados["bairros"]),
        )

    def contem(self, latitude: float, longitude: float) -> bool:
        return self.sul <= latitude <= self.norte and self.oeste <= longitude <= self.leste

    def como_dict(self) -> dict:
        return {
            "nome": self.nome,
            "cidade": self.cidade,
            "provisoria": self.provisoria,
            "centro": {"latitude": self.centro_lat, "longitude": self.centro_lon},
            "limites": {"sul": self.sul, "norte": self.norte, "oeste": self.oeste, "leste": self.leste},
            "zoom": self.zoom,
            "bairros": list(self.bairros),
        }
