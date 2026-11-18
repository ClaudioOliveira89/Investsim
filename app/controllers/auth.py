from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select

from app.controllers._helpers import aplicar_erro, url_segura
from app.extensions import db
from app.forms import AlterarSenhaForm, CadastroForm, ExcluirContaForm, LoginForm
from app.models import Usuario
from app.services import usuario_service
from app.services.excecoes import RegraNegocioError

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("carteiras.painel"))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = db.session.scalar(
            select(Usuario).where(Usuario.email == form.email.data.strip().lower())
        )
        # Mensagem genérica: não revela se o e-mail existe (RNF de segurança).
        if usuario is None or not usuario.verificar_senha(form.senha.data):
            flash("E-mail ou senha incorretos.", "erro")
        elif not usuario.ativo:
            flash("Sua conta está desativada. Procure um administrador.", "erro")
        else:
            login_user(usuario, remember=form.lembrar.data)
            flash(f"Bem-vindo(a), {usuario.nome.split()[0]}!", "sucesso")
            destino = request.args.get("next")
            return redirect(destino if url_segura(destino) else url_for("carteiras.painel"))
    return render_template("auth/login.html", form=form)


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    """Cadastro público: os testadores criam a própria conta e as próprias carteiras."""
    if current_user.is_authenticated:
        return redirect(url_for("carteiras.painel"))
    form = CadastroForm()
    if form.validate_on_submit():
        try:
            usuario = usuario_service.registrar(form.data)
        except RegraNegocioError as erro:
            aplicar_erro(form, erro)
        else:
            login_user(usuario)
            flash(f"Conta criada. Bem-vindo(a), {usuario.nome.split()[0]}! Crie sua primeira carteira.", "sucesso")
            return redirect(url_for("carteiras.nova"))
    return render_template("auth/cadastro.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/minha-conta/excluir", methods=["GET", "POST"])
@login_required
def excluir_conta():
    form = ExcluirContaForm()
    if form.validate_on_submit():
        try:
            usuario_service.excluir_conta(current_user._get_current_object(), form.senha.data)
        except RegraNegocioError as erro:
            db.session.rollback()
            aplicar_erro(form, erro)
        else:
            logout_user()
            flash("Sua conta e todos os seus dados foram excluídos.", "info")
            return redirect(url_for("auth.login"))
    return render_template("auth/excluir_conta.html", form=form)


@bp.route("/minha-senha", methods=["GET", "POST"])
@login_required
def alterar_senha():
    form = AlterarSenhaForm()
    if form.validate_on_submit():
        if not current_user.verificar_senha(form.senha_atual.data):
            form.senha_atual.errors.append("Senha atual incorreta.")
        else:
            current_user.definir_senha(form.nova_senha.data)
            db.session.commit()
            flash("Senha alterada com sucesso.", "sucesso")
            return redirect(url_for("carteiras.painel"))
    return render_template("auth/alterar_senha.html", form=form)
