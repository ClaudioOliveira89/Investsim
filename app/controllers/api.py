"""Endpoints JSON consumidos pelo JavaScript das telas."""
from datetime import date, timedelta

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.extensions import db
from sqlalchemy import func, select

from app.models import Ativo, Provento
from app.services import mercado_service
from app.services.excecoes import RegraNegocioError
from app.simulador.regras import casas_decimais
from app.utils.tempo import data_da_url, hoje

bp = Blueprint("api", __name__, url_prefix="/api")
PERIODOS = {"1m": 31, "6m": 183, "1a": 366, "2a": 731, "5a": 1827}


@bp.before_request
@login_required
def _protegido():
    pass


@bp.get("/cotacao")
def cotacao():
    """Preço de fechamento de um ativo numa data (usado no formulário de operação)."""
    ativo = db.session.get(Ativo, request.args.get("ativo_id", type=int) or 0)
    if ativo is None:
        return jsonify(erro="Ativo não encontrado."), 404
    dia = data_da_url(request.args.get("data"))
    if dia is None:
        return jsonify(erro="Data inválida. Use AAAA-MM-DD."), 400
    if dia > hoje():
        return jsonify(erro="A data não pode estar no futuro."), 422
    try:
        data_efetiva, preco, avisos = mercado_service.preco_em(ativo, dia)
    except RegraNegocioError as erro:
        return jsonify(erro=erro.mensagem), 422
    return jsonify(
        ativo=ativo.ticker,
        classe=ativo.classe,
        casas=casas_decimais(ativo.classe),
        data_pedida=dia.isoformat(),
        data=data_efetiva.isoformat(),
        preco=preco,
        avisos=avisos,
    )


@bp.get("/ativos/<int:ativo_id>/historico")
def historico(ativo_id):
    ativo = db.session.get(Ativo, ativo_id)
    if ativo is None:
        return jsonify(erro="Ativo não encontrado."), 404
    periodo = request.args.get("periodo", "1a")
    if periodo not in PERIODOS:
        return jsonify(erro=f"Período inválido. Use: {', '.join(PERIODOS)}."), 400
    pontos, avisos = mercado_service.historico_grafico(ativo, PERIODOS[periodo])
    return jsonify(ativo=ativo.ticker, periodo=periodo, pontos=pontos, avisos=avisos,
                   estatisticas=_estatisticas(ativo, pontos, PERIODOS[periodo]),
                   gerado_em=date.today().isoformat())


def _estatisticas(ativo: Ativo, pontos: list[dict], dias: int) -> dict | None:
    """Indicadores do período escolhido (os cards da página acompanham o botão 1M/6M/1A/2A/5A)."""
    if not pontos:
        return None
    valores = [p["valor"] for p in pontos]
    proventos = float(db.session.scalar(
        select(func.coalesce(func.sum(Provento.valor), 0)).where(
            Provento.ativo_id == ativo.id, Provento.data >= hoje() - timedelta(days=dias)
        )
    ) or 0)
    return {
        "variacao": (valores[-1] / valores[0] - 1) * 100 if valores[0] else None,
        "minimo": min(valores),
        "maximo": max(valores),
        "proventos": proventos,
        "dividend_yield": proventos / valores[-1] * 100 if proventos and valores[-1] else None,
    }
