"""Terminal de mercado: Ações, BDRs, FIIs, ETFs e Cripto, e catálogo (admin)."""
from datetime import timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from app.controllers._helpers import admin_obrigatorio, aplicar_erro, obter_ou_404
from app.extensions import db
from app.forms import AtivoForm
from app.models import Ativo, Carteira, Cotacao, Provento
from app.services import mercado_service
from app.services.excecoes import RegraNegocioError
from app.simulador.regras import CLASSES
from app.utils.tempo import hoje

bp = Blueprint("mercado", __name__, url_prefix="/mercado")


@bp.before_request
@login_required
def _protegido():
    pass


@bp.route("/")
def index():
    classe = request.args.get("classe", "ACAO")
    if classe not in (*CLASSES, "BDR"):
        classe = "ACAO"
    carteira_id = request.args.get("carteira_id", type=int)
    if carteira_id:
        carteira = db.session.get(Carteira, carteira_id)
        if carteira is None or carteira.usuario_id != current_user.id:
            abort(404)
    contagens = dict(db.session.execute(
        select(Ativo.classe, func.count(Ativo.id))
        .where(Ativo.ativo.is_(True))
        .group_by(Ativo.classe)
    ).all())
    acoes_ativas = db.session.scalars(
        select(Ativo).where(Ativo.classe == "ACAO", Ativo.ativo.is_(True)).order_by(Ativo.ticker)
    ).all()
    bdrs = [ativo for ativo in acoes_ativas if ativo.is_bdr]
    contagens["ACAO"] = len(acoes_ativas) - len(bdrs)
    contagens["BDR"] = len(bdrs)
    if classe == "BDR":
        ativos = bdrs
    elif classe == "ACAO":
        ativos = [ativo for ativo in acoes_ativas if not ativo.is_bdr]
    else:
        ativos = db.session.scalars(
            select(Ativo).where(Ativo.classe == classe, Ativo.ativo.is_(True)).order_by(Ativo.ticker)
        ).all()
    linhas, avisos = mercado_service.resumo(ativos)
    return render_template(
        "mercado/index.html", classe=classe, linhas=linhas, avisos=avisos,
        contagens=contagens, carteira_id=carteira_id,
    )


@bp.route("/<ticker>")
def ativo(ticker):
    ativo = db.session.scalar(select(Ativo).where(Ativo.ticker == ticker.upper()))
    if ativo is None:
        abort(404)
    carteira_id = request.args.get("carteira_id", type=int)
    if carteira_id:
        carteira = db.session.get(Carteira, carteira_id)
        if carteira is None or carteira.usuario_id != current_user.id:
            abort(404)
    (linha,), avisos = mercado_service.resumo([ativo])
    um_ano = hoje() - timedelta(days=365)
    minimo, maximo = db.session.execute(
        select(func.min(Cotacao.fechamento), func.max(Cotacao.fechamento)).where(
            Cotacao.ativo_id == ativo.id, Cotacao.data >= um_ano
        )
    ).one()
    proventos_12m = db.session.scalar(
        select(func.coalesce(func.sum(Provento.valor), 0)).where(Provento.ativo_id == ativo.id, Provento.data >= um_ano)
    )
    ultimo = linha.get("ultimo")
    return render_template(
        "mercado/ativo.html",
        ativo=ativo,
        linha=linha,
        minimo=minimo,
        maximo=maximo,
        proventos_12m=float(proventos_12m or 0),
        dividend_yield=float(proventos_12m) / ultimo * 100 if ultimo and proventos_12m else None,
        carteiras=current_user.carteiras,
        carteira_id=carteira_id,
        avisos=avisos,
    )


# --------------------------------------------------------------------------- catálogo (admin)
@bp.route("/ativos")
@admin_obrigatorio
def catalogo():
    ativos = db.session.scalars(select(Ativo).order_by(Ativo.classe, Ativo.ticker)).all()
    return render_template("mercado/catalogo.html", ativos=ativos)


def _salvar_ativo(ativo: Ativo, form: AtivoForm) -> bool:
    existente = db.session.scalar(select(Ativo).where(Ativo.ticker == form.ticker.data))
    if existente and existente.id != ativo.id:
        aplicar_erro(form, RegraNegocioError("Esse ticker já está no catálogo.", campo="ticker"))
        return False
    # Confirma na fonte que o símbolo tem cotação ANTES de gravar qualquer coisa.
    erro = mercado_service.validar_simbolo(form.ticker.data, form.simbolo_fonte.data, form.classe.data)
    if erro:
        aplicar_erro(form, RegraNegocioError(
            f"A fonte de dados não retornou cotação para esse símbolo ({erro}). Confira o código (ex.: PETR4).",
            campo="simbolo_fonte",
        ))
        return False
    form.populate_obj(ativo)
    db.session.add(ativo)
    db.session.commit()
    return True


@bp.route("/ativos/novo", methods=["GET", "POST"])
@admin_obrigatorio
def novo_ativo():
    form = AtivoForm()
    if form.validate_on_submit() and _salvar_ativo(Ativo(), form):
        flash(f"{form.ticker.data} adicionado ao catálogo.", "sucesso")
        return redirect(url_for("mercado.catalogo"))
    return render_template("mercado/form_ativo.html", form=form, ativo=None)


@bp.route("/ativos/<int:ativo_id>/editar", methods=["GET", "POST"])
@admin_obrigatorio
def editar_ativo(ativo_id):
    ativo = obter_ou_404(Ativo, ativo_id)
    form = AtivoForm(obj=ativo)
    if form.validate_on_submit() and _salvar_ativo(ativo, form):
        flash(f"{ativo.ticker} atualizado.", "sucesso")
        return redirect(url_for("mercado.catalogo"))
    return render_template("mercado/form_ativo.html", form=form, ativo=ativo)


@bp.route("/ativos/<int:ativo_id>/alternar", methods=["POST"])
@admin_obrigatorio
def alternar_ativo(ativo_id):
    ativo = obter_ou_404(Ativo, ativo_id)
    ativo.ativo = not ativo.ativo
    db.session.commit()
    estado = "disponível" if ativo.ativo else "oculto para novas operações (carteiras existentes não mudam)"
    flash(f"{ativo.ticker} {estado}.", "sucesso")
    return redirect(url_for("mercado.catalogo"))
