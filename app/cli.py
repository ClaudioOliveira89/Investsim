"""Comandos de terminal: flask init-db | flask seed | flask criar-admin."""
from pathlib import Path

import click
from sqlalchemy import select

from app.extensions import db
from app.models import Usuario
from app.utils.validadores import senha_forte

SCHEMA_SQL = Path(__file__).resolve().parent.parent / "database" / "schema.sql"


def criar_estrutura(recriar: bool = False) -> str:
    """Cria as tabelas.

    No PostgreSQL executa database/schema.sql (projeto físico oficial, com
    restrição de exclusão, comentários e índices). Em outros bancos (SQLite dos
    testes) usa os metadados dos models.
    """
    if db.engine.dialect.name == "postgresql":
        sql = SCHEMA_SQL.read_text(encoding="utf-8")
        if not recriar:
            # O script começa com DROPs; sem --recriar, ignoramos esse bloco.
            sql = sql.split("-- @@FIM_DROPS@@", 1)[-1]
        with db.engine.begin() as conexao:
            conexao.exec_driver_sql(sql)
        return f"PostgreSQL: estrutura criada a partir de {SCHEMA_SQL.name}"
    if recriar:
        db.drop_all()
    db.create_all()
    return f"{db.engine.dialect.name}: estrutura criada a partir dos models"


def registrar_comandos(app):
    @app.cli.command("init-db")
    @click.option("--recriar", is_flag=True, help="APAGA as tabelas existentes e recria.")
    def init_db(recriar):
        """Cria as tabelas do banco."""
        if recriar:
            click.confirm("Isso apaga TODOS os dados. Continuar?", abort=True)
        click.echo(criar_estrutura(recriar))

    @app.cli.command("seed")
    def seed():
        """Carrega dados de demonstração (contas, catálogo de ativos e carteira de exemplo)."""
        from app.seed import carregar_dados_demo

        resumo = carregar_dados_demo()
        click.echo(resumo)

    @app.cli.command("criar-admin")
    @click.option("--nome", prompt=True)
    @click.option("--email", prompt=True)
    @click.password_option("--senha")
    def criar_admin(nome, email, senha):
        """Cria um usuário administrador."""
        email = email.strip().lower()
        if not senha_forte(senha):
            raise click.ClickException("Senha fraca: use 8+ caracteres com letras e números.")
        if db.session.scalar(select(Usuario).where(Usuario.email == email)):
            raise click.ClickException("Já existe um usuário com esse e-mail.")
        usuario = Usuario(nome=nome, email=email, perfil=Usuario.PERFIL_ADMIN)
        usuario.definir_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Administrador {email} criado.")
