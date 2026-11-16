"""Cadastro de usuários (público e pela administração)."""
from sqlalchemy import func, select

from app.extensions import db
from app.models import Usuario
from app.services.excecoes import RegraNegocioError


def _email_em_uso(email: str, ignorar_id: int | None = None) -> bool:
    existente = db.session.scalar(select(Usuario).where(Usuario.email == email))
    return existente is not None and existente.id != ignorar_id


def registrar(dados: dict) -> Usuario:
    """Cadastro público: qualquer pessoa cria a própria conta de investidor."""
    email = dados["email"].strip().lower()
    if _email_em_uso(email):
        raise RegraNegocioError("Já existe uma conta com este e-mail. Faça login.", campo="email")
    usuario = Usuario(nome=dados["nome"].strip(), email=email, perfil=Usuario.PERFIL_INVESTIDOR)
    usuario.definir_senha(dados["senha"])
    db.session.add(usuario)
    db.session.commit()
    return usuario


def salvar_usuario(usuario: Usuario, dados: dict, usuario_logado: Usuario) -> Usuario:
    email = dados["email"].strip().lower()
    if _email_em_uso(email, usuario.id):
        raise RegraNegocioError("Este e-mail já está em uso por outro usuário.", campo="email")
    if usuario.id == usuario_logado.id and dados["perfil"] != Usuario.PERFIL_ADMIN:
        raise RegraNegocioError("Você não pode remover o seu próprio perfil de administrador.", campo="perfil")
    if usuario.id is None and not dados.get("senha"):
        raise RegraNegocioError("Informe uma senha para o novo usuário.", campo="senha")
    usuario.nome = dados["nome"].strip()
    usuario.email = email
    usuario.perfil = dados["perfil"]
    if dados.get("senha"):
        usuario.definir_senha(dados["senha"])
    db.session.add(usuario)
    db.session.commit()
    return usuario


def alternar_ativo(usuario: Usuario, usuario_logado: Usuario) -> None:
    if usuario.id == usuario_logado.id:
        raise RegraNegocioError("Você não pode desativar a sua própria conta.")
    if usuario.ativo and usuario.is_admin:
        admins = db.session.scalar(
            select(func.count(Usuario.id)).where(Usuario.perfil == Usuario.PERFIL_ADMIN, Usuario.ativo.is_(True))
        )
        if admins <= 1:
            raise RegraNegocioError("O sistema precisa ter ao menos um administrador ativo.")
    usuario.ativo = not usuario.ativo
    db.session.commit()
