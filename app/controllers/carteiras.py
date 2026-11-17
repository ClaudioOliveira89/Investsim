"""Carteiras do usuário: painel, relatório comparado ao CDI e operações."""
import csv
import io
from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from app.controllers._helpers import aplicar_erro
from app.extensions import db
from app.forms import CarteiraForm, OperacaoForm
from app.models import Ativo, Carteira, Operacao
from app.services import carteira_service
from app.services.excecoes import RegraNegocioError
from app.simulador.regras import CLASSES, COMPRA, VENDA
from app.utils import filtros
from app.utils.tempo import hoje

bp = Blueprint("carteiras", __name__)
MAX_PONTOS_GRAFICO = 700


@bp.before_request
@login_required
def _protegido():
    pass


def _minha_carteira(carteira_id: int) -> Carteira:
    """Só o dono enxerga a carteira (404 para os demais, sem revelar que ela existe)."""
    carteira = db.session.get(Carteira, carteira_id)
    if carteira is None or carteira.usuario_id != current_user.id:
        abort(404)
    return carteira


def _minha_operacao(operacao_id: int) -> Operacao:
    operacao = db.session.get(Operacao, operacao_id)
    if operacao is None or operacao.carteira.usuario_id != current_user.id:
        abort(404)
    return operacao


def _dados_grafico(resultado) -> dict:
    pontos = resultado.pontos
    passo = max(1, len(pontos) // MAX_PONTOS_GRAFICO)
    amostra = pontos[::passo]
    if amostra and amostra[-1] is not pontos[-1]:
        amostra.append(pontos[-1])
    return {
        "datas": [p.data.isoformat() for p in amostra],
        "carteira": [round((p.cota - 1) * 100, 4) for p in amostra],
        "cdi": [round((p.cota_cdi - 1) * 100, 4) for p in amostra],
        "patrimonio": [round(p.patrimonio, 2) for p in amostra],
        "espelho": [round(p.espelho_cdi, 2) for p in amostra],
        "investido": [round(p.investido_liquido, 2) for p in amostra],
    }


# --------------------------------------------------------------------------- painel
@bp.route("/")
def painel():
    resumos, avisos = [], []
    for carteira in current_user.carteiras:
        resultado, aviso = carteira_service.relatorio(carteira)
        resumos.append((carteira, resultado))
        avisos += aviso
    totais = {
        "patrimonio": sum(r.indicadores.get("patrimonio", 0) for _, r in resumos),
        "investido": sum(r.indicadores.get("investido_liquido", 0) for _, r in resumos),
        "espelho": sum(r.indicadores.get("espelho_cdi", 0) for _, r in resumos),
    }
    return render_template("carteiras/painel.html", resumos=resumos, totais=totais, avisos=sorted(set(avisos)))


# --------------------------------------------------------------------------- carteira
@bp.route("/carteiras/nova", methods=["GET", "POST"])
def nova():
    form = CarteiraForm()
    if form.validate_on_submit():
        try:
            carteira = carteira_service.salvar_carteira(Carteira(), form.data, current_user)
        except RegraNegocioError as erro:
            aplicar_erro(form, erro)
        else:
            flash(f"Carteira “{carteira.nome}” criada. Registre a primeira aplicação!", "sucesso")
            return redirect(url_for("carteiras.nova_operacao", carteira_id=carteira.id))
    return render_template("carteiras/form.html", form=form, carteira=None)


@bp.route("/carteiras/<int:carteira_id>")
def detalhe(carteira_id):
    carteira = _minha_carteira(carteira_id)
    resultado, avisos = carteira_service.relatorio(carteira)
    return render_template(
        "carteiras/relatorio.html",
        carteira=carteira,
        r=resultado,
        i=resultado.indicadores,
        grafico=_dados_grafico(resultado) if not resultado.vazio else None,
        operacoes=sorted(carteira.operacoes, key=lambda o: (o.data, o.id), reverse=True),
        avisos=avisos,
        modo_impressao=False,
    )


@bp.route("/carteiras/<int:carteira_id>/imprimir")
def imprimir(carteira_id):
    carteira = _minha_carteira(carteira_id)
    resultado, avisos = carteira_service.relatorio(carteira)
    return render_template(
        "carteiras/impressao.html",
        carteira=carteira, r=resultado, i=resultado.indicadores,
        grafico=_dados_grafico(resultado) if not resultado.vazio else None,
        operacoes=sorted(carteira.operacoes, key=lambda o: (o.data, o.id)),
        avisos=avisos, gerado_em=hoje(),
    )


@bp.route("/carteiras/<int:carteira_id>/exportar.csv")
def exportar(carteira_id):
    carteira = _minha_carteira(carteira_id)
    resultado, _ = carteira_service.relatorio(carteira)
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["data", "patrimonio", "investido_liquido", "rentabilidade_acumulada_pct",
                       "cdi_acumulado_pct", "carteira_espelho_cdi"])
    for p in resultado.pontos:
        escritor.writerow([
            p.data.isoformat(), f"{p.patrimonio:.2f}", f"{p.investido_liquido:.2f}",
            f"{(p.cota - 1) * 100:.4f}", f"{(p.cota_cdi - 1) * 100:.4f}", f"{p.espelho_cdi:.2f}",
        ])
    nome = "".join(c if c.isalnum() else "-" for c in carteira.nome.lower()).strip("-") or "carteira"
    return Response(
        "﻿" + saida.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{nome}-evolucao.csv"'},
    )


@bp.route("/carteiras/<int:carteira_id>/editar", methods=["GET", "POST"])
def editar(carteira_id):
    carteira = _minha_carteira(carteira_id)
    form = CarteiraForm(obj=carteira)
    if form.validate_on_submit():
        try:
            carteira_service.salvar_carteira(carteira, form.data, current_user)
        except RegraNegocioError as erro:
            aplicar_erro(form, erro)
        else:
            flash("Carteira atualizada.", "sucesso")
            return redirect(url_for("carteiras.detalhe", carteira_id=carteira.id))
    return render_template("carteiras/form.html", form=form, carteira=carteira)


@bp.route("/carteiras/<int:carteira_id>/excluir", methods=["POST"])
def excluir(carteira_id):
    carteira = _minha_carteira(carteira_id)
    nome = carteira.nome
    carteira_service.excluir_carteira(carteira)
    flash(f"Carteira “{nome}” excluída.", "sucesso")
    return redirect(url_for("carteiras.painel"))


# --------------------------------------------------------------------------- operações
def _ativos_para_escolha(incluir_id: int | None = None) -> list[Ativo]:
    consulta = select(Ativo).where((Ativo.ativo.is_(True)) | (Ativo.id == (incluir_id or 0)))
    return db.session.scalars(consulta.order_by(Ativo.classe, Ativo.ticker)).all()


def _preparar_form(form: OperacaoForm, operacao: Operacao | None = None) -> tuple[OperacaoForm, dict]:
    ativos = _ativos_para_escolha(operacao.ativo_id if operacao else None)
    form.ativo_id.choices = [(0, "Escolha o ativo…")] + [(a.id, f"{a.ticker} — {a.nome}") for a in ativos]
    grupos: dict[str, list[Ativo]] = {}
    for ativo in ativos:
        grupos.setdefault(CLASSES[ativo.classe], []).append(ativo)
    return form, grupos


def _form_para_dados(form: OperacaoForm) -> dict:
    return {
        "ativo_id": form.ativo_id.data,
        "tipo": form.tipo.data,
        "data": form.data.data,
        "modo": form.modo.data,
        "valor": form.valor.data,
        "quantidade": form.quantidade.data,
        "preco": form.preco.data,
        "taxas": form.taxas.data,
        "observacao": form.observacao.data,
    }


def _salvar_operacao(carteira: Carteira, form: OperacaoForm, operacao: Operacao | None):
    try:
        salva, avisos = carteira_service.registrar_operacao(carteira, _form_para_dados(form), operacao)
    except RegraNegocioError as erro:
        db.session.rollback()
        aplicar_erro(form, erro)
        return None
    for aviso in avisos:
        flash(aviso, "aviso")
    verbo = "Compra" if salva.tipo == COMPRA else "Venda"
    flash(
        f"{verbo} registrada: {filtros.quantidade(salva.quantidade)} {salva.ativo.ticker} a "
        f"{filtros.preco(salva.preco)} em {salva.data:%d/%m/%Y} (total {filtros.moeda(salva.valor_total)}).",
        "sucesso",
    )
    return redirect(url_for("carteiras.detalhe", carteira_id=carteira.id))


@bp.route("/carteiras/<int:carteira_id>/operacoes/nova", methods=["GET", "POST"])
def nova_operacao(carteira_id):
    carteira = _minha_carteira(carteira_id)
    form, grupos = _preparar_form(OperacaoForm())
    if request.method == "GET":
        form.ativo_id.data = request.args.get("ativo_id", type=int) or 0
        form.tipo.data = VENDA if request.args.get("tipo") == VENDA else COMPRA
        form.data.data = hoje()
    if form.validate_on_submit():
        resposta = _salvar_operacao(carteira, form, None)
        if resposta:
            return resposta
    return render_template(
        "operacoes/form.html", form=form, grupos=grupos, carteira=carteira, operacao=None,
        ativo_selecionado=db.session.get(Ativo, form.ativo_id.data or 0),
    )


@bp.route("/operacoes/<int:operacao_id>/editar", methods=["GET", "POST"])
def editar_operacao(operacao_id):
    operacao = _minha_operacao(operacao_id)
    form, grupos = _preparar_form(OperacaoForm(obj=operacao), operacao)
    if request.method == "GET":
        form.modo.data = "QUANTIDADE"
    if form.validate_on_submit():
        resposta = _salvar_operacao(operacao.carteira, form, operacao)
        if resposta:
            return resposta
    return render_template(
        "operacoes/form.html", form=form, grupos=grupos, carteira=operacao.carteira,
        operacao=operacao, ativo_selecionado=operacao.ativo,
    )


@bp.route("/operacoes/<int:operacao_id>/excluir", methods=["POST"])
def excluir_operacao(operacao_id):
    operacao = _minha_operacao(operacao_id)
    carteira_id = operacao.carteira_id
    try:
        carteira_service.excluir_operacao(operacao)
    except RegraNegocioError as erro:
        flash(erro.mensagem, "erro")
    else:
        flash("Operação excluída. O relatório foi recalculado.", "sucesso")
    return redirect(url_for("carteiras.detalhe", carteira_id=carteira_id))
