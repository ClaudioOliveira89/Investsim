"""Valida o projeto físico (database/schema.sql) em um PostgreSQL real.

ATENÇÃO: recria as tabelas do banco indicado. Use um banco SÓ para testes:

    $env:TEST_PG_URL = "postgresql+psycopg://investsim:investsim@localhost:5432/investsim_teste"
    pytest -m postgres
"""
import os
from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.cli import criar_estrutura
from app.config import TestConfig
from app.extensions import db
from app.models import Carteira
from app.seed import carregar_dados_demo
from app.services import carteira_service
from app.utils.tempo import hoje

URL = os.environ.get("TEST_PG_URL")
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(not URL, reason="defina TEST_PG_URL para testar no PostgreSQL"),
]


@pytest.fixture()
def pg():
    class ConfigPG(TestConfig):
        SQLALCHEMY_DATABASE_URI = URL

    app = create_app(ConfigPG)
    with app.app_context():
        criar_estrutura(recriar=True)
        carregar_dados_demo()
        yield app
        db.session.remove()
        db.engine.dispose()


def test_objetos_do_schema_existem(pg):
    tabelas = set(db.session.scalars(text("select table_name from information_schema.tables where table_schema = 'public'")))
    assert {"usuario", "ativo", "carteira", "operacao", "cotacao", "provento", "taxa_cdi", "sincronizacao",
            "feedback_teste", "feedback_anexo", "vw_operacoes_detalhadas", "vw_posicao_atual"} <= tabelas
    dominios = set(db.session.scalars(text("select domain_name from information_schema.domains")))
    assert {"dm_nome", "dm_email", "dm_ticker", "dm_preco", "dm_quantidade"} <= dominios


def test_seed_e_relatorio_funcionam_no_postgres(pg):
    carteira = db.session.scalar(db.select(Carteira))
    resultado, avisos = carteira_service.relatorio(carteira)
    assert avisos == [] and resultado.indicadores["patrimonio"] > 0
    linhas = db.session.execute(text("select ticker, quantidade from vw_posicao_atual order by ticker")).all()
    assert {t for t, _ in linhas} == {p.ticker for p in resultado.posicoes if p.quantidade > 0}
    detalhadas = db.session.scalar(text("select count(*) from vw_operacoes_detalhadas"))
    assert detalhadas == len(carteira.operacoes)


@pytest.mark.parametrize(
    ("sql", "restricao"),
    [
        ("insert into ativo (ticker, nome, classe, simbolo_fonte) values ('petr-4', 'X', 'ACAO', 'X')", "dm_ticker"),
        ("insert into ativo (ticker, nome, classe, simbolo_fonte) values ('ABCD3', 'X', 'OPCAO', 'X')", "ck_ativo_classe"),
        ("insert into usuario (nome, email, senha_hash) values ('Ze', 'sem-arroba', 'x')", "dm_email"),
        ("insert into operacao (carteira_id, ativo_id, tipo, data, quantidade, preco) "
         "values (1, 1, 'COMPRA', DATE '2026-01-05', 0, 10)", "dm_quantidade"),
        ("insert into operacao (carteira_id, ativo_id, tipo, data, quantidade, preco) "
         "values (1, 1, 'TROCA', DATE '2026-01-05', 1, 10)", "ck_operacao_tipo"),
        ("insert into operacao (carteira_id, ativo_id, tipo, data, quantidade, preco) "
         "values (1, 1, 'COMPRA', DATE '2026-01-05', 1, -10)", "dm_preco"),
        ("insert into carteira (usuario_id, nome) select usuario_id, nome from carteira limit 1", "uq_carteira_usuario_nome"),
        ("delete from ativo where id = (select ativo_id from operacao limit 1)", "fk_operacao_ativo"),
    ],
)
def test_restricoes_do_banco(pg, sql, restricao):
    with pytest.raises(IntegrityError, match=restricao):
        db.session.execute(text(sql))
        db.session.flush()
    db.session.rollback()


def test_excluir_usuario_apaga_carteiras_em_cascata(pg):
    carteira = db.session.scalar(db.select(Carteira))
    db.session.delete(carteira.usuario)
    db.session.commit()
    assert db.session.scalar(text("select count(*) from operacao")) == 0


def test_cache_de_mercado_respeita_chaves(pg):
    with pytest.raises(IntegrityError, match="pk_cotacao"):
        db.session.execute(text(
            "insert into cotacao (ativo_id, data, fechamento) "
            "select ativo_id, data, fechamento from cotacao limit 1"
        ))
        db.session.flush()
    db.session.rollback()
    carteira_service.relatorio(db.session.scalar(db.select(Carteira)))  # o CDI é baixado ao gerar o relatório
    assert db.session.scalar(text("select count(*) from taxa_cdi where data >= :d"), {"d": hoje() - timedelta(days=30)}) > 10
