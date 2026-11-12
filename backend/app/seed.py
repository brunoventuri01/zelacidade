"""Gera ocorrências SIMULADAS para o piloto, de forma reproduzível e documentada.

Por que simular: o grupo registra poucas ocorrências reais (com foto) no bairro piloto, e o Big Data e o
painel precisam de volume para as consultas fazerem sentido. Todo registro gerado aqui tem
origem="simulado" e simulado=True, aparece com selo na tela e pode ser filtrado em qualquer consulta.

Regras da geração (semente fixa, mesma saída a cada execução):
- datas de criação uniformes entre --inicio e --fim (padrão: 01/10/2026 a hoje), entre 7h e 21h;
- categorias com pesos: buraco 35%, calçada 18%, iluminação 15%, obstáculo 10%, lixo 10%,
  equipamento 7%, outro 5%;
- localização uniforme dentro dos limites da área piloto, com o bairro coerente com a posição;
- triagem em média 6 h depois (distribuição exponencial); 8% duplicadas e 7% pedindo informação;
- das triadas, ~30% entram em andamento (1 a 5 dias) e ~40% são resolvidas (2 a 15 dias), com uma
  foto de resolução gerada e marcada "SIMULADO";
- confirmações de 0 a 8, mais altas para buraco; metade com e-mail fictício @exemplo.com e consentimento.

Uso: python -m app.seed --quantidade 200 --semente 42 --limpar
"""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from io import BytesIO

from PIL import Image, ImageDraw
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from . import models  # noqa: F401
from .area import AreaPiloto
from .config import Settings
from .db import Base, criar_engine
from .dominio import CATEGORIAS, PRIORIDADES
from .models import Confirmacao, Evento, Foto, Ocorrencia, agora

PESOS = {
    "buraco": 35, "calcada_danificada": 18, "iluminacao": 15, "obstaculo": 10,
    "lixo_entulho": 10, "equipamento_danificado": 7, "outro": 5,
}
DESCRICOES = {
    "buraco": ["Buraco grande na faixa de rolamento", "Buraco perto da faixa de pedestres",
               "Asfalto cedeu depois da chuva"],
    "calcada_danificada": ["Calçada quebrada em frente ao número informado", "Piso solto na calçada",
                           "Raiz levantou a calçada"],
    "iluminacao": ["Poste apagado há vários dias", "Lâmpada piscando a noite toda", "Rua escura no trecho"],
    "obstaculo": ["Entulho bloqueando a calçada", "Placa caída na passagem", "Carro abandonado na calçada"],
    "lixo_entulho": ["Lixo acumulado na esquina", "Descarte irregular de móveis", "Entulho de obra na via"],
    "equipamento_danificado": ["Banco da praça quebrado", "Grade do parque danificada", "Lixeira arrancada"],
    "outro": ["Fiação baixa preocupando moradores", "Bueiro sem tampa", "Pichação em equipamento público"],
}
PONTOS_CATEGORIA = {"buraco": 3, "obstaculo": 3, "iluminacao": 2}


def _foto_simulada() -> tuple[bytes, int, int]:
    imagem = Image.new("RGB", (480, 320), (120, 128, 136))
    desenho = ImageDraw.Draw(imagem)
    desenho.rectangle([20, 20, 460, 300], outline=(255, 255, 255), width=4)
    desenho.text((150, 150), "SIMULADO - resolução", fill=(255, 255, 255))
    saida = BytesIO()
    imagem.save(saida, "JPEG", quality=70)
    return saida.getvalue(), 480, 320


def _prioridade(categoria: str, confirmacoes: int) -> tuple[str, str]:
    pontos = PONTOS_CATEGORIA.get(categoria, 1) + confirmacoes // 2
    nivel = "alta" if pontos >= 5 else "media" if pontos >= 3 else "baixa"
    return nivel, (f"Simulação da regra de pontos: categoria {PONTOS_CATEGORIA.get(categoria, 1)} + "
                   f"confirmações {confirmacoes // 2} = {pontos} ({PRIORIDADES[nivel].lower()}).")


def gerar(db: Session, area: AreaPiloto, quantidade: int, semente: int, inicio: datetime, fim: datetime) -> int:
    rng = random.Random(semente)
    foto_jpeg, foto_l, foto_a = _foto_simulada()
    categorias, pesos = list(PESOS), list(PESOS.values())
    largura_faixa = (area.leste - area.oeste) / len(area.bairros)
    intervalo = (fim - inicio).total_seconds()
    agora_ = agora()
    criadas: list[Ocorrencia] = []

    for n in range(1, quantidade + 1):
        categoria = rng.choices(categorias, pesos)[0]
        indice_bairro = rng.randrange(len(area.bairros))
        oeste = area.oeste + indice_bairro * largura_faixa
        criado = inicio + timedelta(seconds=rng.uniform(0, intervalo))
        criado = criado.replace(hour=rng.randint(10, 23) % 24, minute=rng.randint(0, 59))  # 7h-20h em SP = 10h-23h UTC
        if criado > agora_:
            criado = agora_ - timedelta(minutes=rng.randint(5, 600))
        confirmacoes = min(8, int(rng.expovariate(1 / (3 if categoria == "buraco" else 1.5))))
        com_email = rng.random() < 0.5
        o = Ocorrencia(
            categoria=categoria,
            descricao=rng.choice(DESCRICOES[categoria]),
            bairro=area.bairros[indice_bairro],
            latitude=round(rng.uniform(area.sul, area.norte), 6),
            longitude=round(rng.uniform(oeste, oeste + largura_faixa), 6),
            origem="simulado",
            simulado=True,
            confirmacoes=confirmacoes,
            autor_email=f"morador{n:03d}@exemplo.com" if com_email else None,
            consentimento=com_email,
            criado_em=criado,
            atualizado_em=criado,
        )
        if categoria == "buraco" and rng.random() < 0.7:
            o.categoria_ia, o.confianca_ia = "buraco", round(rng.uniform(0.4, 0.95), 2)
            o.severidade_ia = rng.choice(["baixa", "media", "alta"])
            o.modelo_ia = "simulado"
        db.add(o)
        eventos = [Evento(ocorrencia=o, tipo="criada", descricao="Registro simulado para o piloto.",
                          ator="sistema", criado_em=criado)]

        triado = criado + timedelta(hours=rng.expovariate(1 / 6))
        if triado < agora_:
            sorteio = rng.random()
            o.triado_em = triado
            anteriores = [c for c in criadas if c.categoria == categoria and c.criado_em < criado]
            if sorteio < 0.08 and anteriores:
                original = rng.choice(anteriores)
                o.status, o.duplicada_de = "duplicada", None
                o.prioridade_motivo = "Simulação: mesmo problema já registrado por perto."
                o._original = original  # resolvido depois do flush
            elif sorteio < 0.15:
                o.status, o.prioridade_motivo = "precisa_info", "Simulação: descrição insuficiente."
            else:
                o.status = "triada"
                o.prioridade, o.prioridade_motivo = _prioridade(categoria, confirmacoes)
                andamento = triado + timedelta(days=rng.uniform(1, 5))
                resolvido = triado + timedelta(days=rng.uniform(2, 15))
                destino = rng.random()
                if destino < 0.40 and resolvido < agora_:
                    o.status, o.resolvido_em = "resolvida", resolvido
                    db.add(Foto(ocorrencia=o, tipo="resolucao", conteudo=foto_jpeg, largura=foto_l,
                                altura=foto_a, criado_em=resolvido))
                    eventos.append(Evento(ocorrencia=o, tipo="status", ator="sistema", criado_em=resolvido,
                                          descricao="Resolução simulada, com foto de evidência simulada."))
                elif destino < 0.70 and andamento < agora_:
                    o.status = "em_andamento"
                    eventos.append(Evento(ocorrencia=o, tipo="status", ator="sistema", criado_em=andamento,
                                          descricao="Andamento simulado."))
            eventos.insert(1, Evento(ocorrencia=o, tipo="triagem", ator="sistema", criado_em=triado,
                                     descricao=f"Triagem simulada: {o.prioridade_motivo}"))
        o.atualizado_em = max(e.criado_em for e in eventos)
        db.add_all(eventos)
        criadas.append(o)

    db.flush()
    for o in criadas:
        original = getattr(o, "_original", None)
        if original is not None:
            o.duplicada_de = original.id
    db.commit()
    return len(criadas)


def limpar_simulados(db: Session) -> None:
    ids = list(db.scalars(select(Ocorrencia.id).where(Ocorrencia.origem == "simulado")))
    if not ids:
        return
    db.execute(delete(Confirmacao).where(Confirmacao.ocorrencia_id.in_(ids)))
    db.execute(delete(Evento).where(Evento.ocorrencia_id.in_(ids)))
    db.execute(delete(Foto).where(Foto.ocorrencia_id.in_(ids)))
    db.execute(Ocorrencia.__table__.update().where(Ocorrencia.id.in_(ids)).values(duplicada_de=None))
    db.execute(delete(Ocorrencia).where(Ocorrencia.id.in_(ids)))
    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quantidade", type=int, default=200)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--inicio", default="2026-10-01")
    parser.add_argument("--fim", default=None, help="AAAA-MM-DD; padrão: agora")
    parser.add_argument("--limpar", action="store_true", help="apaga os simulados antes de gerar")
    args = parser.parse_args()

    settings = Settings.from_env()
    engine = criar_engine(settings.database_url)
    Base.metadata.create_all(engine)
    area = AreaPiloto.carregar(settings.area_piloto_path)
    inicio = datetime.fromisoformat(args.inicio)
    fim = datetime.fromisoformat(args.fim) if args.fim else agora()
    with sessionmaker(bind=engine)() as db:
        if args.limpar:
            limpar_simulados(db)
        total = gerar(db, area, args.quantidade, args.semente, inicio, fim)
    print(f"{total} ocorrências simuladas geradas em {area.nome} (semente {args.semente}).")
    assert set(PESOS) == set(CATEGORIAS)


if __name__ == "__main__":
    main()
