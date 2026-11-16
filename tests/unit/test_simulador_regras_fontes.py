"""Regras das operações e leitura das fontes de dados (sem acessar a internet)."""
from datetime import date

import pytest

from app.simulador import fontes
from app.simulador.regras import (
    COMPRA,
    VENDA,
    Movimento,
    RegraSimuladorError,
    quantidade_por_valor,
    validar_cronologia,
    validar_quantidade,
)

D1, D2, D3 = date(2026, 3, 2), date(2026, 3, 3), date(2026, 3, 4)


# ------------------------------------------------------------------ quantidades
@pytest.mark.parametrize(("classe", "qtd"), [("ACAO", 100), ("FII", 1), ("ETF", 3), ("CRIPTO", 0.00012345)])
def test_quantidades_validas(classe, qtd):
    validar_quantidade(classe, qtd)


@pytest.mark.parametrize(
    ("classe", "qtd", "mensagem"),
    [("ACAO", 0, "maior que zero"), ("FII", -1, "maior que zero"), ("ACAO", 1.5, "unidades inteiras"),
     ("CRIPTO", 0.123456789, "8 casas")],
)
def test_quantidades_invalidas(classe, qtd, mensagem):
    with pytest.raises(RegraSimuladorError, match=mensagem):
        validar_quantidade(classe, qtd)


def test_quantidade_por_valor_arredonda_para_baixo():
    assert quantidade_por_valor(1000, 37.5, "ACAO") == 26  # 26,67 -> 26 ações
    assert quantidade_por_valor(1000, 350000, "CRIPTO") == pytest.approx(0.00285714)
    with pytest.raises(RegraSimuladorError, match="mínimo de R\\$ 120,00"):
        quantidade_por_valor(100, 120, "FII")
    with pytest.raises(RegraSimuladorError, match="maior que zero"):
        quantidade_por_valor(0, 10, "ACAO")


# ------------------------------------------------------------------ cronologia
def test_venda_dentro_da_posicao_e_permitida():
    validar_cronologia([
        Movimento(D1, "ABCD3", "ACAO", COMPRA, 10, 10.0, id=1),
        Movimento(D2, "ABCD3", "ACAO", VENDA, 10, 11.0, id=2),
    ])


def test_venda_maior_que_a_posicao_e_bloqueada():
    with pytest.raises(RegraSimuladorError, match="excede a posição disponível nessa data \\(10\\)"):
        validar_cronologia([
            Movimento(D1, "ABCD3", "ACAO", COMPRA, 10, 10.0),
            Movimento(D2, "ABCD3", "ACAO", VENDA, 11, 11.0),
        ])


def test_venda_antes_da_compra_e_bloqueada_mesmo_que_o_total_feche():
    with pytest.raises(RegraSimuladorError, match="02/03/2026"):
        validar_cronologia([
            Movimento(D2, "ABCD3", "ACAO", COMPRA, 10, 10.0),
            Movimento(D1, "ABCD3", "ACAO", VENDA, 5, 11.0),
        ])


def test_compra_e_venda_no_mesmo_dia_compra_vem_antes():
    validar_cronologia([
        Movimento(D1, "ABCD3", "ACAO", VENDA, 5, 11.0, id=1),
        Movimento(D1, "ABCD3", "ACAO", COMPRA, 5, 10.0, id=2),
    ])


def test_posicoes_sao_por_ativo():
    with pytest.raises(RegraSimuladorError, match="WXYZ3"):
        validar_cronologia([
            Movimento(D1, "ABCD3", "ACAO", COMPRA, 10, 10.0),
            Movimento(D2, "WXYZ3", "ACAO", VENDA, 1, 11.0),
        ])


# ------------------------------------------------------------------ fontes
def test_preencher_para_frente():
    serie = {D1: 10.0, D3: 12.0}
    assert fontes.preencher_para_frente(serie, [date(2026, 3, 1), D1, D2, D3]) == {D1: 10.0, D2: 10.0, D3: 12.0}


def test_demonstracao_e_deterministica_e_tem_proventos_de_fii():
    demo = fontes.Demonstracao()
    a = demo.historico("KNRI11", date(2025, 1, 1), date(2025, 6, 30), classe="FII")
    b = demo.historico("KNRI11", date(2025, 3, 1), date(2025, 6, 30), classe="FII")
    assert a.fechamentos[date(2025, 4, 1)] == b.fechamentos[date(2025, 4, 1)]  # independe da janela
    assert len(a.dividendos) == 6  # um por mês
    assert all(d.weekday() < 5 for d in a.fechamentos)
    cripto = demo.historico("BTC", date(2025, 1, 4), date(2025, 1, 5), classe="CRIPTO")
    assert len(cripto.fechamentos) == 2  # cripto negocia no fim de semana
    cdi = demo.cdi(date(2025, 1, 1), date(2025, 1, 31))
    assert len(cdi) == 23 and 0.04 < next(iter(cdi.values())) < 0.05


class RespostaFalsa:
    def __init__(self, dados, status=200):
        self._dados, self.status_code = dados, status

    def json(self):
        return self._dados

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(str(self.status_code))


class SessaoFalsa:
    def __init__(self, respostas):
        self.respostas, self.headers, self.chamadas = respostas, {}, []

    def get(self, url, params=None, timeout=None):
        self.chamadas.append((url, params))
        for trecho, resposta in self.respostas.items():
            if trecho in url:
                return resposta
        raise AssertionError(f"URL inesperada: {url}")


def _brapi(fechamentos, proventos=None):
    base = 1772420400  # 2026-03-02 00:00 em Brasília (03:00 UTC)
    return {"results": [{
        "symbol": "KNRI11", "longName": "Kinea Renda Imobiliária",
        "historicalDataPrice": [
            {"date": base + i * 86400, "close": c} for i, c in enumerate(fechamentos)
        ],
        "dividendsData": {"cashDividends": proventos or []},
    }]}


def test_brapi_le_fechamentos_ignora_vazios_e_le_proventos_na_data_ex():
    proventos = [
        {"rate": 0.8, "exDate": "2026-03-03T03:00:00.000Z", "lastDatePrior": "2026-03-02T03:00:00.000Z"},
        {"rate": 0.5, "exDate": None, "lastDatePrior": "2026-03-03T03:00:00.000Z"},  # sem data ex: dia seguinte
        {"rate": 9.9, "exDate": "2025-01-10T03:00:00.000Z"},  # fora do período
    ]
    sessao = SessaoFalsa({"/quote/KNRI11": RespostaFalsa(_brapi([150.0, None, 152.5], proventos))})
    h = fontes.Brapi("tok", sessao).historico("KNRI11", D1, D3, classe="FII")
    assert h.fechamentos == {D1: 150.0, D3: 152.5}
    assert h.dividendos == {D2: 0.8, D3: 0.5}
    assert h.nome == "Kinea Renda Imobiliária"
    assert sessao.headers["Authorization"] == "Bearer tok"
    assert sessao.headers["User-Agent"].startswith("InvestSim")  # identificação honesta
    assert sessao.chamadas[0][1]["dividends"] == "true"


def test_brapi_cripto_usa_endpoint_proprio_em_reais():
    resposta = {"coins": [{"coinName": "Bitcoin", "historicalDataPrice": [{"date": 1772420400, "close": 350000.0}]}]}
    sessao = SessaoFalsa({"/v2/crypto": RespostaFalsa(resposta)})
    h = fontes.Brapi(None, sessao).historico("BTC", D1, D1, classe="CRIPTO")
    assert h.fechamentos == {D1: 350000.0}
    assert sessao.chamadas[0][1]["currency"] == "BRL"
    assert "Authorization" not in sessao.headers  # sem token, não envia cabeçalho


@pytest.mark.parametrize(
    ("dias", "faixa"), [(10, "1mo"), (80, "3mo"), (300, "1y"), (700, "2y"), (1500, "5y"), (5000, "max")]
)
def test_brapi_escolhe_a_menor_faixa_que_cobre_o_periodo(dias, faixa):
    from datetime import timedelta
    assert fontes.Brapi.faixa(date(2026, 11, 15) - timedelta(days=dias), date(2026, 11, 15)) == faixa


@pytest.mark.parametrize(
    ("resposta", "mensagem"),
    [(RespostaFalsa({}, status=401), "BRAPI_TOKEN"), (RespostaFalsa({}, status=429), "limitou"),
     (RespostaFalsa({}, status=404), "não encontrado"), (RespostaFalsa({"results": []}), "Sem dados")],
)
def test_brapi_erros_viram_fonte_indisponivel(resposta, mensagem):
    with pytest.raises(fontes.FonteIndisponivel, match=mensagem):
        fontes.Brapi(None, SessaoFalsa({"/quote/": resposta})).historico("XXXX3", D1, D2)


def test_banco_central_le_cdi():
    sessao = SessaoFalsa({"sgs.12": RespostaFalsa([
        {"data": "02/03/2026", "valor": "0.050788"}, {"data": "03/03/2026", "valor": "0.050788"},
    ])})
    assert fontes.BancoCentral(sessao).cdi(D1, D2) == {D1: 0.050788, D2: 0.050788}
    assert sessao.chamadas[0][1]["dataInicial"] == "02/03/2026"


def test_banco_central_fora_do_ar():
    with pytest.raises(fontes.FonteIndisponivel, match="Banco Central"):
        fontes.BancoCentral(SessaoFalsa({"sgs.12": RespostaFalsa([], status=500)})).cdi(D1, D2)
