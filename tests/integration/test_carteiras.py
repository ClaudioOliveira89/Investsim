"""Carteiras, operações e relatório pela interface web (fonte de dados de demonstração)."""
import csv
import io
from decimal import Decimal

import pytest

from app.models import Carteira, Operacao
from app.services import carteira_service, mercado_service


def _operar(carteira, ativo, dia, tipo="COMPRA", **extra):
    dados = {"ativo_id": ativo.id, "tipo": tipo, "data": dia, "modo": "QUANTIDADE", "quantidade": 10, **extra}
    return carteira_service.registrar_operacao(carteira, dados)[0]


def _form(ativo, dia, **extra):
    return {"ativo_id": ativo.id, "tipo": "COMPRA", "data": dia.isoformat(), "modo": "VALOR",
            "valor": "1000", "quantidade": "", "preco": "", "taxas": "0", "observacao": "", **extra}


# ------------------------------------------------------------------ carteiras
def test_painel_vazio_convida_a_criar_carteira(logado_investidor):
    html = logado_investidor.get("/").get_data(as_text=True)
    assert "Criar carteira" in html and "Modo demonstração" in html


def test_criar_carteira_leva_para_primeira_operacao(logado_investidor, db, investidor):
    r = logado_investidor.post("/carteiras/nova", data={"nome": " Aposentadoria ", "descricao": "longo prazo"})
    carteira = db.session.scalar(db.select(Carteira))
    assert carteira.nome == "Aposentadoria" and carteira.usuario == investidor
    assert r.headers["Location"].endswith(f"/carteiras/{carteira.id}/operacoes/nova")


def test_nome_de_carteira_unico_por_usuario(logado_investidor, carteira):
    r = logado_investidor.post("/carteiras/nova", data={"nome": "LONGO PRAZO"})
    assert "Você já tem uma carteira com esse nome." in r.get_data(as_text=True)


def test_carteira_de_outro_usuario_e_invisivel(client, carteira, outro_investidor, ativos, dias_atras):
    op = _operar(carteira, ativos["PETR4"], dias_atras(30))
    from tests.conftest import login
    login(client, outro_investidor.email)
    for url in (f"/carteiras/{carteira.id}", f"/carteiras/{carteira.id}/imprimir", f"/carteiras/{carteira.id}/exportar.csv",
                f"/carteiras/{carteira.id}/editar", f"/carteiras/{carteira.id}/operacoes/nova", f"/operacoes/{op.id}/editar"):
        assert client.get(url).status_code == 404, url
    assert client.post(f"/carteiras/{carteira.id}/excluir").status_code == 404
    assert client.post(f"/operacoes/{op.id}/excluir").status_code == 404
    assert "Longo prazo" not in client.get("/").get_data(as_text=True)


def test_excluir_carteira(logado_investidor, db, carteira, ativos, dias_atras):
    _operar(carteira, ativos["PETR4"], dias_atras(30))
    r = logado_investidor.post(f"/carteiras/{carteira.id}/excluir", follow_redirects=True)
    assert "Carteira “Longo prazo” excluída." in r.get_data(as_text=True)
    assert db.session.scalar(db.select(db.func.count(Operacao.id))) == 0


# ------------------------------------------------------------------ operações
def test_comprar_por_valor_calcula_quantidade_pelo_fechamento(logado_investidor, db, carteira, ativos, dias_atras):
    dia = dias_atras(60)
    _, preco, _ = mercado_service.preco_em(ativos["KNRI11"], dia)
    r = logado_investidor.post(f"/carteiras/{carteira.id}/operacoes/nova", data=_form(ativos["KNRI11"], dia), follow_redirects=True)
    html = r.get_data(as_text=True)
    op = db.session.scalar(db.select(Operacao))
    assert op.quantidade == Decimal(int(1000 // preco))  # FII: unidades inteiras, arredonda para baixo
    assert op.preco == Decimal(f"{preco:.8f}")
    assert "Compra registrada" in html and "KNRI11" in html


def test_comprar_cripto_por_valor_aceita_fracao(logado_investidor, db, carteira, ativos, dias_atras):
    logado_investidor.post(f"/carteiras/{carteira.id}/operacoes/nova", data=_form(ativos["BTC"], dias_atras(10), valor="500"))
    op = db.session.scalar(db.select(Operacao))
    assert 0 < op.quantidade < 1 and op.quantidade * op.preco <= Decimal("500")


def test_preco_manual_e_taxas(logado_investidor, db, carteira, ativos, dias_atras):
    dados = _form(ativos["PETR4"], dias_atras(20), modo="QUANTIDADE", valor="", quantidade="100", preco="37.50", taxas="4.90")
    logado_investidor.post(f"/carteiras/{carteira.id}/operacoes/nova", data=dados)
    op = db.session.scalar(db.select(Operacao))
    assert (op.quantidade, op.preco, op.taxas, op.valor_total) == (100, Decimal("37.5"), Decimal("4.90"), Decimal("3754.90"))


@pytest.mark.parametrize(
    ("extra", "mensagem"),
    [
        ({"ativo_id": "0"}, "Escolha o ativo."),
        ({"valor": ""}, "Informe quanto quer aplicar"),
        ({"modo": "QUANTIDADE", "quantidade": ""}, "Informe a quantidade."),
        ({"modo": "QUANTIDADE", "quantidade": "1.5"}, "unidades inteiras"),
        ({"valor": "5"}, "O valor não compra nem 1 unidade"),
        ({"taxas": "-1"}, "não podem ser negativas"),
    ],
)
def test_validacoes_do_formulario(logado_investidor, db, carteira, ativos, dias_atras, extra, mensagem):
    dados = _form(ativos["PETR4"], dias_atras(20), **extra)
    html = logado_investidor.post(f"/carteiras/{carteira.id}/operacoes/nova", data=dados).get_data(as_text=True)
    assert mensagem in html
    assert db.session.scalar(db.select(db.func.count(Operacao.id))) == 0


def test_data_futura_e_recusada(logado_investidor, carteira, ativos):
    from datetime import timedelta

    from app.utils.tempo import hoje
    html = logado_investidor.post(
        f"/carteiras/{carteira.id}/operacoes/nova", data=_form(ativos["PETR4"], hoje() + timedelta(days=2))
    ).get_data(as_text=True)
    assert "preço projetado" in html  # data futura = projeção: exige preço manual


def test_venda_maior_que_a_posicao_e_bloqueada(logado_investidor, db, carteira, ativos, dias_atras):
    _operar(carteira, ativos["PETR4"], dias_atras(40), quantidade=10)
    dados = _form(ativos["PETR4"], dias_atras(10), tipo="VENDA", modo="QUANTIDADE", valor="", quantidade="11")
    html = logado_investidor.post(f"/carteiras/{carteira.id}/operacoes/nova", data=dados).get_data(as_text=True)
    assert "excede a posição disponível nessa data (10)" in html
    assert db.session.scalar(db.select(db.func.count(Operacao.id))) == 1


def test_nao_exclui_compra_da_qual_uma_venda_depende(logado_investidor, carteira, ativos, dias_atras):
    compra = _operar(carteira, ativos["PETR4"], dias_atras(40), quantidade=10)
    venda = _operar(carteira, ativos["PETR4"], dias_atras(10), tipo="VENDA", quantidade=5)
    r = logado_investidor.post(f"/operacoes/{compra.id}/excluir", follow_redirects=True)
    assert "uma venda posterior depende dela" in r.get_data(as_text=True)
    r = logado_investidor.post(f"/operacoes/{venda.id}/excluir", follow_redirects=True)
    assert "Operação excluída" in r.get_data(as_text=True)


def test_editar_operacao(logado_investidor, carteira, ativos, dias_atras):
    op = _operar(carteira, ativos["PETR4"], dias_atras(40), quantidade=10)
    html = logado_investidor.get(f"/operacoes/{op.id}/editar").get_data(as_text=True)
    assert 'value="QUANTIDADE" checked' in html or 'checked id="modo-1"' in html or "QUANTIDADE" in html
    dados = _form(ativos["PETR4"], dias_atras(35), modo="QUANTIDADE", valor="", quantidade="20")
    logado_investidor.post(f"/operacoes/{op.id}/editar", data=dados)
    assert (op.quantidade, op.data) == (20, dias_atras(35))


def test_ativo_oculto_nao_aparece_para_novas_operacoes(logado_investidor, db, carteira, ativos, dias_atras):
    ativos["BTC"].ativo = False
    db.session.commit()
    html = logado_investidor.get(f"/carteiras/{carteira.id}/operacoes/nova").get_data(as_text=True)
    assert "BTC — Bitcoin" not in html
    html = logado_investidor.post(f"/carteiras/{carteira.id}/operacoes/nova", data=_form(ativos["BTC"], dias_atras(5))).get_data(as_text=True)
    assert "Escolha um ativo disponível." in html or "Not a valid choice" in html or "inválid" in html.lower()


# ------------------------------------------------------------------ relatório
@pytest.fixture()
def carteira_com_historico(carteira, ativos, dias_atras):
    _operar(carteira, ativos["PETR4"], dias_atras(400), quantidade=100)
    _operar(carteira, ativos["KNRI11"], dias_atras(300), quantidade=20)
    _operar(carteira, ativos["BTC"], dias_atras(200), modo="VALOR", valor=2000)
    _operar(carteira, ativos["PETR4"], dias_atras(60), tipo="VENDA", quantidade=40)
    return carteira


def test_relatorio_completo(logado_investidor, carteira_com_historico):
    html = logado_investidor.get(f"/carteiras/{carteira_com_historico.id}").get_data(as_text=True)
    for trecho in ("Carteira × CDI", "Rentabilidade", "CDI no período", "Proventos recebidos", "Maior queda",
                   "Posições", "Alocação por classe", "Mês a mês", "Operações", 'id="dados-grafico"',
                   "Se estivesse no CDI" if False else "Com os mesmos aportes no CDI"):
        assert trecho in html, trecho
    assert "chart.umd.min.js" in html


def test_indicadores_do_relatorio_batem_com_o_motor(carteira_com_historico):
    resultado, avisos = carteira_service.relatorio(carteira_com_historico)
    i = resultado.indicadores
    assert avisos == []
    assert i["proventos"] > 0  # o FII paga proventos na demonstração
    assert i["total_resgatado"] > 0
    assert i["lucro"] == pytest.approx(i["patrimonio"] - i["investido_liquido"])
    assert {p.ticker for p in resultado.posicoes} == {"PETR4", "KNRI11", "BTC"}
    assert next(p for p in resultado.posicoes if p.ticker == "PETR4").quantidade == 60


def test_impressao_e_csv(logado_investidor, carteira_com_historico):
    html = logado_investidor.get(f"/carteiras/{carteira_com_historico.id}/imprimir").get_data(as_text=True)
    assert "Imprimir / Salvar em PDF" in html and "Metodologia" in html and "PETR4" in html
    r = logado_investidor.get(f"/carteiras/{carteira_com_historico.id}/exportar.csv")
    assert r.mimetype == "text/csv" and "longo-prazo-evolucao.csv" in r.headers["Content-Disposition"]
    linhas = list(csv.reader(io.StringIO(r.data.decode("utf-8-sig")), delimiter=";"))
    assert linhas[0][:3] == ["data", "patrimonio", "investido_liquido"] and len(linhas) > 250


def test_painel_consolida_carteiras(logado_investidor, carteira_com_historico):
    html = logado_investidor.get("/").get_data(as_text=True)
    assert "Patrimônio total" in html and "Longo prazo" in html and "% do CDI" in html
