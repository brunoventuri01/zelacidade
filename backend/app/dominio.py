"""Vocabulário comum do ZelaCidade: o mesmo no MVP, no robô RPA e no Databricks."""

CATEGORIAS = {
    "buraco": "Buraco na via",
    "calcada_danificada": "Calçada danificada",
    "iluminacao": "Iluminação apagada ou falhando",
    "obstaculo": "Obstáculo na passagem",
    "equipamento_danificado": "Equipamento público danificado",
    "lixo_entulho": "Lixo ou entulho",
    "outro": "Outro problema",
}

STATUS = {
    "recebida": "Recebida",
    "triada": "Triada",
    "duplicada": "Duplicada",
    "precisa_info": "Precisa de informação",
    "em_andamento": "Em andamento",
    "resolvida": "Resolvida",
}

STATUS_ABERTOS = ("recebida", "triada", "precisa_info", "em_andamento")
STATUS_TRIAGEM = ("triada", "duplicada", "precisa_info")
STATUS_GESTOR = ("em_andamento", "resolvida")

PRIORIDADES = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}
ORDEM_PRIORIDADE = {"alta": 0, "media": 1, "baixa": 2}

ORIGENS = {"cidadao": "Morador", "robo": "Robô Maker Lab", "simulado": "Dado simulado"}

# event_type do robô do Bruno -> categoria do ZelaCidade
EVENTO_ROBO_PARA_CATEGORIA = {"obstacle": "obstaculo", "pothole": "buraco", "other": "outro"}


def protocolo(ocorrencia_id: int) -> str:
    return f"ZC-{ocorrencia_id:06d}"
