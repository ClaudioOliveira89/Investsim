"""Utilidades comuns aos controllers."""
from functools import wraps
from urllib.parse import urlsplit

from flask import abort, flash
from flask_login import current_user

from app.extensions import db
from app.services.excecoes import RegraNegocioError


def admin_obrigatorio(view):
    """Restringe a rota a administradores (RNF de controle de acesso)."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def obter_ou_404(modelo, registro_id):
    registro = db.session.get(modelo, registro_id)
    if registro is None:
        abort(404)
    return registro


def aplicar_erro(form, erro: RegraNegocioError) -> None:
    """Mostra o erro de negócio junto ao campo correspondente, ou como alerta geral."""
    campo = getattr(form, erro.campo, None) if erro.campo else None
    if campo is not None:
        campo.errors = [*campo.errors, erro.mensagem]
    else:
        flash(erro.mensagem, "erro")


def url_segura(destino: str | None) -> bool:
    """Evita open redirect no parâmetro ?next= do login."""
    if not destino:
        return False
    partes = urlsplit(destino)
    return not partes.scheme and not partes.netloc and destino.startswith("/")
