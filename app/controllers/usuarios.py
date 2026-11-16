from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from app.controllers._helpers import admin_obrigatorio, aplicar_erro, obter_ou_404
from app.extensions import db
from app.forms import UsuarioForm
from app.models import Usuario
from app.services import usuario_service
from app.services.excecoes import RegraNegocioError

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.before_request
@login_required
@admin_obrigatorio
def _somente_admin():
    pass


@bp.route("/")
def listar():
    usuarios = db.session.scalars(select(Usuario).order_by(Usuario.ativo.desc(), Usuario.nome)).all()
    return render_template("usuarios/listar.html", usuarios=usuarios)


@bp.route("/novo", methods=["GET", "POST"])
def novo():
    form = UsuarioForm()
    form.senha.description = "Mínimo de 8 caracteres, com letras e números."
    if form.validate_on_submit():
        try:
            usuario = usuario_service.salvar_usuario(Usuario(), form.data, current_user)
        except RegraNegocioError as erro:
            aplicar_erro(form, erro)
        else:
            flash(f"Usuário {usuario.email} criado.", "sucesso")
            return redirect(url_for("usuarios.listar"))
    return render_template("usuarios/form.html", form=form, usuario=None)


@bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
def editar(usuario_id):
    usuario = obter_ou_404(Usuario, usuario_id)
    form = UsuarioForm(obj=usuario)
    if form.validate_on_submit():
        try:
            usuario_service.salvar_usuario(usuario, form.data, current_user)
        except RegraNegocioError as erro:
            db.session.rollback()
            aplicar_erro(form, erro)
        else:
            flash("Usuário atualizado.", "sucesso")
            return redirect(url_for("usuarios.listar"))
    return render_template("usuarios/form.html", form=form, usuario=usuario)


@bp.route("/<int:usuario_id>/alternar", methods=["POST"])
def alternar(usuario_id):
    usuario = obter_ou_404(Usuario, usuario_id)
    try:
        usuario_service.alternar_ativo(usuario, current_user)
    except RegraNegocioError as erro:
        flash(erro.mensagem, "erro")
    else:
        flash(f"Usuário {usuario.email} {'ativado' if usuario.ativo else 'desativado'}.", "sucesso")
    return redirect(url_for("usuarios.listar"))
