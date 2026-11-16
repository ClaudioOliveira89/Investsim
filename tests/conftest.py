"""Fixtures compartilhadas pelos testes.

Os testes usam SQLite em memória e a fonte de dados de demonstração (sem internet).
Para rodar a suíte contra o PostgreSQL, defina TEST_DATABASE_URL.
"""
from datetime import timedelta

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db
from app.models import Ativo, Carteira, Usuario
from app.utils.tempo import hoje

SENHA = "Senha123"


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()  # fecha as conexões do pool


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def client(app):
    return app.test_client()


def _usuario(nome, email, perfil):
    usuario = Usuario(nome=nome, email=email, perfil=perfil)
    usuario.definir_senha(SENHA)
    _db.session.add(usuario)
    _db.session.commit()
    return usuario


@pytest.fixture()
def admin(app):
    return _usuario("Ana Admin", "admin@teste.com", Usuario.PERFIL_ADMIN)


@pytest.fixture()
def investidor(app):
    return _usuario("Bruno Investidor", "bruno@teste.com", Usuario.PERFIL_INVESTIDOR)


@pytest.fixture()
def outro_investidor(app):
    return _usuario("Carla Curiosa", "carla@teste.com", Usuario.PERFIL_INVESTIDOR)


@pytest.fixture()
def ativos(app):
    """Uma ação, um FII (paga proventos na demonstração) e um cripto."""
    lista = [
        Ativo(ticker="PETR4", nome="Petrobras PN", classe="ACAO", simbolo_fonte="PETR4"),
        Ativo(ticker="KNRI11", nome="Kinea Renda", classe="FII", simbolo_fonte="KNRI11"),
        Ativo(ticker="BTC", nome="Bitcoin", classe="CRIPTO", simbolo_fonte="BTC"),
    ]
    _db.session.add_all(lista)
    _db.session.commit()
    return {a.ticker: a for a in lista}


@pytest.fixture()
def carteira(investidor):
    carteira = Carteira(nome="Longo prazo", usuario=investidor)
    _db.session.add(carteira)
    _db.session.commit()
    return carteira


@pytest.fixture()
def dias_atras():
    """Data de N dias atrás (sempre em dia útil, para ter pregão)."""

    def _dia(n: int):
        dia = hoje() - timedelta(days=n)
        while dia.weekday() >= 5:
            dia -= timedelta(days=1)
        return dia

    return _dia


def login(client, email, senha=SENHA):
    return client.post("/login", data={"email": email, "senha": senha}, follow_redirects=True)


@pytest.fixture()
def logado_admin(client, admin):
    login(client, admin.email)
    return client


@pytest.fixture()
def logado_investidor(client, investidor):
    login(client, investidor.email)
    return client
