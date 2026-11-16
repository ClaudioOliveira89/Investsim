"""Funções de data/hora.

O banco guarda datas/horas "locais" (sem fuso), sempre no fuso configurado em
FUSO_HORARIO. Centralizar o "agora" aqui facilita os testes (basta substituir
esta função) e evita misturar horários UTC e locais.
"""
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from flask import current_app, has_app_context


def agora() -> datetime:
    fuso = "America/Sao_Paulo"
    if has_app_context():
        fuso = current_app.config.get("FUSO_HORARIO", fuso)
    return datetime.now(ZoneInfo(fuso)).replace(tzinfo=None, second=0, microsecond=0)


def hoje():
    return agora().date()


# Faixa de datas aceita nas URLs e formulários: evita estouro (OverflowError) ao somar
# ou subtrair dias de datas extremas como 9999-12-31.
ANO_MINIMO = 1900
ANO_MAXIMO = 2999


def data_valida(valor: date | None) -> bool:
    return valor is not None and ANO_MINIMO <= valor.year <= ANO_MAXIMO


def data_da_url(texto: str | None) -> date | None:
    """Converte 'AAAA-MM-DD' vindo da URL; devolve None se inválida ou fora da faixa."""
    try:
        valor = date.fromisoformat(texto or "")
    except ValueError:
        return None
    return valor if data_valida(valor) else None


def parse_hora(valor: str) -> time:
    """Converte 'HH:MM' em time. Lança ValueError se o formato for inválido."""
    return datetime.strptime(valor.strip(), "%H:%M").time()
