"""Formulário público de testes (Situação-Problema 3) e área de tratativa dos feedbacks."""
import csv
import io

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import select
from sqlalchemy.orm import undefer

from app.controllers._helpers import admin_obrigatorio, aplicar_erro, obter_ou_404
from app.extensions import db
from app.forms import FeedbackForm, TratativaFeedbackForm
from app.models import FeedbackAnexo, FeedbackTeste
from app.services import feedback_service
from app.services.excecoes import RegraNegocioError
from app.utils.tempo import hoje

bp = Blueprint("feedback", __name__, url_prefix="/feedback")


def celula_segura(valor) -> str:
    """Neutraliza injeção de fórmulas em planilhas (CSV injection).

    O texto vem de um formulário público: se começar com = + - @ (ou tab/CR), o Excel
    o interpretaria como fórmula. Um apóstrofo na frente faz a planilha tratá-lo como texto.
    """
    texto = "" if valor is None else str(valor)
    return "'" + texto if texto[:1] in ("=", "+", "-", "@", "\t", "\r") else texto


# --------------------------------------------------------------------------- público
@bp.route("/", methods=["GET", "POST"])
def enviar():
    form = FeedbackForm()
    if request.method == "GET":
        form.data_teste.data = hoje()
    if form.validate_on_submit():
        try:
            feedback_service.registrar_feedback(
                form.data, request.files.getlist("prints"), request.headers.get("User-Agent")
            )
        except RegraNegocioError as erro:
            aplicar_erro(form, erro)
        else:
            return redirect(url_for("feedback.obrigado"))
    return render_template("feedback/enviar.html", form=form)


@bp.route("/obrigado")
def obrigado():
    return render_template("feedback/obrigado.html")


# --------------------------------------------------------------------------- administração
@bp.route("/admin")
@login_required
@admin_obrigatorio
def listar():
    feedbacks = db.session.scalars(
        select(FeedbackTeste).order_by(FeedbackTeste.criado_em.desc())
    ).all()
    return render_template("feedback/listar.html", feedbacks=feedbacks)


@bp.route("/admin/<int:feedback_id>", methods=["GET", "POST"])
@login_required
@admin_obrigatorio
def detalhe(feedback_id):
    feedback = obter_ou_404(FeedbackTeste, feedback_id)
    form = TratativaFeedbackForm(obj=feedback)
    form.status.choices = list(FeedbackTeste.STATUS.items())
    if form.validate_on_submit():
        feedback_service.atualizar_tratativa(feedback, form.status.data, form.tratativa.data)
        flash("Tratativa registrada.", "sucesso")
        return redirect(url_for("feedback.detalhe", feedback_id=feedback.id))
    return render_template("feedback/detalhe.html", feedback=feedback, form=form)


@bp.route("/admin/anexo/<int:anexo_id>")
@login_required
@admin_obrigatorio
def anexo(anexo_id):
    registro = db.session.scalar(
        select(FeedbackAnexo).options(undefer(FeedbackAnexo.conteudo)).where(FeedbackAnexo.id == anexo_id)
    )
    if registro is None:
        return render_template("erros/erro.html", codigo=404, titulo="Imagem não encontrada"), 404
    return Response(
        registro.conteudo,
        mimetype=registro.tipo_mime,
        headers={
            "Content-Disposition": f'inline; filename="{registro.nome_arquivo}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@bp.route("/admin/relatorio")
@login_required
@admin_obrigatorio
def relatorio():
    """Página pronta para imprimir/salvar em PDF com todos os laudos dos testadores."""
    feedbacks = db.session.scalars(
        select(FeedbackTeste).order_by(FeedbackTeste.data_teste, FeedbackTeste.id)
    ).all()
    return render_template("feedback/relatorio.html", feedbacks=feedbacks, gerado_em=hoje())


@bp.route("/admin/exportar.csv")
@login_required
@admin_obrigatorio
def exportar_csv():
    feedbacks = db.session.scalars(select(FeedbackTeste).order_by(FeedbackTeste.id)).all()
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(
        ["id", "testador", "perfil", "data_teste", "nota", "funcionou", "nao_funcionou",
         "nao_testado", "sugestoes", "status", "tratativa", "qtd_prints"]
    )
    for f in feedbacks:
        texto = celula_segura  # campos de texto livre vindos do formulário público
        escritor.writerow(
            [f.id, texto(f.nome_testador), texto(f.perfil_testador), f.data_teste.isoformat(),
             f.nota, texto(f.funcionou), texto(f.nao_funcionou), texto(f.nao_testado),
             texto(f.sugestoes), f.status_descricao, texto(f.tratativa), len(f.anexos)]
        )
    # BOM para o Excel abrir acentos corretamente
    return Response(
        "﻿" + saida.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="feedbacks-testes.csv"'},
    )
