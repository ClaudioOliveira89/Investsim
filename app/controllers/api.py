"""Endpoints JSON consumidos pelo JavaScript das telas."""
from datetime import date

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.extensions import db
from app.models import Ativo
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
                   gerado_em=date.today().isoformat())
