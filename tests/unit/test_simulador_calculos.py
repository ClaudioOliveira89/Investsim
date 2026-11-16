"""Testes do motor de cálculo com um cenário conferido à mão.

Cenário (CDI de 1% ao dia para facilitar a conta):
  D1  compra 10 ABCD3 a R$ 10 (fecha a 10)  -> patrimônio 100, cota 1,00
  D2  fecha a 11                            -> patrimônio 110, cota 1,10
  D3  compra 10 a R$ 11 (fecha a 12)        -> patrimônio 240, cota 1,30
  D4  vende 5 a R$ 12 com R$ 1 de taxa      -> recebe 59; patrimônio 180
"""
from datetime import date

import pytest

from app.simulador.calculos import preco_na_data, simular
from app.simulador.regras import COMPRA, VENDA, Movimento

D1, D2, D3, D4 = date(2026, 3, 2), date(2026, 3, 3), date(2026, 3, 4), date(2026, 3, 5)
CDI = {d: 1.0 for d in (D1, D2, D3, D4)}
PRECOS = {"ABCD3": {D1: 10.0, D2: 11.0, D3: 12.0, D4: 12.0}}
MOVS = [
    Movimento(D1, "ABCD3", "ACAO", COMPRA, 10, 10.0, id=1),
    Movimento(D3, "ABCD3", "ACAO", COMPRA, 10, 11.0, id=2),
    Movimento(D4, "ABCD3", "ACAO", VENDA, 5, 12.0, taxas=1.0, id=3),
]


@pytest.fixture()
def resultado():
    return simular(MOVS, PRECOS, {}, CDI, D4)


def test_serie_de_patrimonio_e_cotas(resultado):
    p = resultado.pontos
    assert [round(x.patrimonio, 2) for x in p] == [100, 110, 240, 180]
    assert [round(x.investido_liquido, 2) for x in p] == [100, 100, 210, 151]
    assert p[1].cota == pytest.approx(1.10)
    assert p[2].cota == pytest.approx(1.30)
    assert p[3].cota == pytest.approx(1.3 * (239 / 240))  # venda não distorce a rentabilidade


def test_cdi_acumulado_e_carteira_espelho(resultado):
    p = resultado.pontos
    assert p[0].cota_cdi == pytest.approx(1.0)  # o dinheiro só rende a partir do dia seguinte
    assert p[3].cota_cdi == pytest.approx(1.01**3)
    assert p[3].espelho_cdi == pytest.approx((100 * 1.01 * 1.01 + 110) * 1.01 - 59)


def test_preco_medio_e_resultado_realizado(resultado):
    (posicao,) = resultado.posicoes
    assert posicao.quantidade == 15
    assert posicao.preco_medio == pytest.approx(10.5)  # (100 + 110) / 20
    assert posicao.custo == pytest.approx(157.5)
    assert posicao.realizado == pytest.approx(6.5)  # 59 recebidos − 5 × 10,50
    assert posicao.resultado == pytest.approx(22.5)  # 15 × 12 − 157,50
    assert posicao.peso == pytest.approx(100)


def test_indicadores(resultado):
    i = resultado.indicadores
    assert i["patrimonio"] == pytest.approx(180)
    assert i["total_aportado"] == pytest.approx(210)
    assert i["total_resgatado"] == pytest.approx(59)
    assert i["lucro"] == pytest.approx(29)  # 22,50 não realizado + 6,50 realizado
    assert i["rentabilidade"] == pytest.approx((1.3 * 239 / 240 - 1) * 100)
    assert i["cdi_periodo"] == pytest.approx((1.01**3 - 1) * 100)
    assert i["pct_cdi"] == pytest.approx(i["rentabilidade"] / i["cdi_periodo"] * 100)
    assert i["diferenca_cdi"] == pytest.approx(180 - i["espelho_cdi"])
    assert i["max_drawdown"] == pytest.approx((239 / 240 - 1) * 100)
    assert i["volatilidade"] > 0


def test_taxas_da_compra_entram_no_custo_e_na_rentabilidade():
    movs = [Movimento(D1, "ABCD3", "ACAO", COMPRA, 10, 10.0, taxas=5.0)]
    r = simular(movs, {"ABCD3": {D1: 10.0}}, {}, {D1: 0.05}, D1)
    assert r.posicoes[0].preco_medio == pytest.approx(10.5)
    assert r.indicadores["rentabilidade"] == pytest.approx((100 / 105 - 1) * 100)


def test_proventos_viram_caixa_de_quem_tinha_a_cota_antes():
    movs = [
        Movimento(D1, "FUND11", "FII", COMPRA, 10, 100.0),
        Movimento(D3, "FUND11", "FII", COMPRA, 10, 100.0),  # comprou no dia do provento: não recebe
    ]
    precos = {"FUND11": {d: 100.0 for d in (D1, D2, D3, D4)}}
    dividendos = {"FUND11": {D2: 1.0, D3: 1.0}}
    r = simular(movs, precos, dividendos, {}, D4)
    assert r.indicadores["proventos"] == pytest.approx(20)  # 10 cotas × R$ 1 em D2 e em D3
    assert r.indicadores["patrimonio"] == pytest.approx(2020)
    assert r.alocacao == {"FII": pytest.approx(2000), "CAIXA": pytest.approx(20)}
    assert r.posicoes[0].proventos == pytest.approx(20)


def test_zerar_e_recomprar_reinicia_preco_medio():
    movs = [
        Movimento(D1, "ABCD3", "ACAO", COMPRA, 10, 10.0, id=1),
        Movimento(D2, "ABCD3", "ACAO", VENDA, 10, 11.0, id=2),
        Movimento(D3, "ABCD3", "ACAO", COMPRA, 4, 12.0, id=3),
    ]
    r = simular(movs, PRECOS, {}, CDI, D4)
    (p,) = r.posicoes
    assert (p.quantidade, p.preco_medio, p.realizado) == (4, pytest.approx(12.0), pytest.approx(10.0))
    assert r.pontos[1].patrimonio == pytest.approx(0)  # zerado em D2
    assert r.pontos[2].retorno_dia == pytest.approx(0)  # recompra a 12 fechando a 12


def test_cripto_em_fim_de_semana_e_preco_da_operacao_cobre_lacunas():
    sabado, domingo = date(2026, 3, 7), date(2026, 3, 8)
    movs = [Movimento(sabado, "BTC", "CRIPTO", COMPRA, 0.5, 300000.0)]
    r = simular(movs, {"BTC": {domingo: 330000.0}}, {}, {}, domingo)
    assert [p.data for p in r.pontos] == [sabado, domingo]
    assert r.pontos[0].patrimonio == pytest.approx(150000)  # usa o preço da operação no sábado
    assert r.indicadores["rentabilidade"] == pytest.approx(10)
    assert r.indicadores["pct_cdi"] is None  # sem CDI no período


def test_retornos_mensais():
    marco, abril = date(2026, 3, 31), date(2026, 4, 30)
    movs = [Movimento(marco, "ABCD3", "ACAO", COMPRA, 1, 100.0)]
    precos = {"ABCD3": {marco: 100.0, date(2026, 4, 1): 105.0, abril: 110.0}}
    cdi = {date(2026, 4, 1): 1.0, abril: 1.0}
    r = simular(movs, precos, {}, cdi, abril)
    assert [(m.ano, m.mes) for m in r.mensal] == [(2026, 3), (2026, 4)]
    assert r.mensal[1].carteira == pytest.approx(10)
    assert r.mensal[1].cdi == pytest.approx((1.01**2 - 1) * 100)
    assert r.mensal[1].pct_cdi == pytest.approx(10 / ((1.01**2 - 1) * 100) * 100)


def test_sem_operacoes_resultado_vazio():
    assert simular([], {}, {}, {}, D4).vazio
    assert simular(MOVS, PRECOS, {}, CDI, date(2026, 1, 1)).vazio  # todas depois do fim


def test_preco_na_data():
    serie = {D1: 10.0, D3: 12.0}
    assert preco_na_data(serie, D2) == (D1, 10.0)  # usa o último pregão
    assert preco_na_data(serie, D4) == (D3, 12.0)
    assert preco_na_data(serie, date(2026, 1, 1)) is None
