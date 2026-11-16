"""Motor de cálculo da carteira simulada (Python puro, sem banco nem framework).

Convenções:
- Compras são aportes (dinheiro entra na carteira); vendas são resgates (dinheiro sai).
- Proventos (dividendos/rendimentos) ficam na carteira como caixa.
- Rentabilidade pelo método de cotas (TWR, *time-weighted return*), o mesmo usado por fundos:
  aportes e resgates não distorcem o resultado.
- "Carteira espelho CDI": o mesmo dinheiro, nas mesmas datas, aplicado a 100% do CDI.
"""
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from .fontes import preencher_para_frente
from .regras import COMPRA, EPSILON, Movimento, ordenar


@dataclass
class PontoDiario:
    data: date
    patrimonio: float
    investido_liquido: float
    cota: float
    cota_cdi: float
    espelho_cdi: float
    retorno_dia: float


@dataclass
class Posicao:
    ticker: str
    classe: str
    quantidade: float
    preco_medio: float
    custo: float
    preco_atual: float
    valor: float
    resultado: float
    resultado_pct: float | None
    realizado: float
    proventos: float
    peso: float = 0.0


@dataclass
class Mes:
    ano: int
    mes: int
    carteira: float
    cdi: float

    @property
    def pct_cdi(self) -> float | None:
        return self.carteira / self.cdi * 100 if self.cdi > EPSILON else None


@dataclass
class Resultado:
    pontos: list[PontoDiario] = field(default_factory=list)
    posicoes: list[Posicao] = field(default_factory=list)
    alocacao: dict[str, float] = field(default_factory=dict)
    mensal: list[Mes] = field(default_factory=list)
    indicadores: dict[str, float | None] = field(default_factory=dict)

    @property
    def vazio(self) -> bool:
        return not self.pontos


def preco_na_data(serie: dict[date, float], dia: date) -> tuple[date, float] | None:
    """Último fechamento disponível até a data (inclusive)."""
    anteriores = [d for d in serie if d <= dia]
    if not anteriores:
        return None
    ultimo = max(anteriores)
    return ultimo, serie[ultimo]


def simular(
    movimentos: list[Movimento],
    precos: dict[str, dict[date, float]],
    dividendos: dict[str, dict[date, float]],
    cdi: dict[date, float],
    fim: date,
) -> Resultado:
    movimentos = [m for m in ordenar(movimentos) if m.data <= fim]
    if not movimentos:
        return Resultado()
    inicio = movimentos[0].data

    # Calendário: dias com CDI (dias úteis), com cotação (cripto negocia todo dia) ou com operação.
    dias = {d for d in cdi if inicio <= d <= fim}
    for serie in precos.values():
        dias.update(d for d in serie if inicio <= d <= fim)
    dias.update(m.data for m in movimentos)
    calendario = sorted(dias)

    # Preços por dia (último conhecido); o preço da operação cobre lacunas da fonte.
    classes = {m.ticker: m.classe for m in movimentos}
    precos_dia: dict[str, dict[date, float]] = {}
    for ticker in classes:
        base = dict(precos.get(ticker, {}))
        for m in movimentos:
            if m.ticker == ticker:
                base.setdefault(m.data, m.preco)
        precos_dia[ticker] = preencher_para_frente(base, calendario)

    por_dia: dict[date, list[Movimento]] = defaultdict(list)
    for m in movimentos:
        por_dia[m.data].append(m)

    quantidade: dict[str, float] = defaultdict(float)
    custo: dict[str, float] = defaultdict(float)
    realizado: dict[str, float] = defaultdict(float)
    proventos: dict[str, float] = defaultdict(float)
    caixa = 0.0
    aportado = resgatado = 0.0
    valor_anterior = 0.0
    cota = cota_cdi = 1.0
    espelho = 0.0
    investido = 0.0
    pontos: list[PontoDiario] = []

    for indice, dia in enumerate(calendario):
        # 1) Proventos: quem tinha a cota antes das operações do dia recebe.
        for ticker, qtd in quantidade.items():
            valor_cota = dividendos.get(ticker, {}).get(dia)
            if valor_cota and qtd > EPSILON:
                caixa += qtd * valor_cota
                proventos[ticker] += qtd * valor_cota

        # 2) Operações do dia.
        fluxo = 0.0
        for m in por_dia.get(dia, []):
            if m.tipo == COMPRA:
                quantidade[m.ticker] += m.quantidade
                custo[m.ticker] += m.fluxo
                aportado += m.fluxo
            else:
                custo_medio = custo[m.ticker] / quantidade[m.ticker] if quantidade[m.ticker] > EPSILON else 0.0
                baixa = custo_medio * m.quantidade
                realizado[m.ticker] += -m.fluxo - baixa
                custo[m.ticker] -= baixa
                quantidade[m.ticker] -= m.quantidade
                if quantidade[m.ticker] <= EPSILON:
                    quantidade[m.ticker] = 0.0
                    custo[m.ticker] = 0.0
                resgatado += -m.fluxo
            fluxo += m.fluxo

        # 3) Valor de mercado no fechamento.
        patrimonio = caixa + sum(
            qtd * precos_dia[t].get(dia, 0.0) for t, qtd in quantidade.items() if qtd > EPSILON
        )

        # 4) Rentabilidade do dia pelo método de cotas.
        if valor_anterior > EPSILON:
            retorno = (patrimonio - fluxo) / valor_anterior - 1
        elif fluxo > EPSILON:
            retorno = patrimonio / fluxo - 1
        else:
            retorno = 0.0
        cota *= 1 + retorno

        taxa_cdi = cdi.get(dia, 0.0) / 100 if indice > 0 else 0.0
        cota_cdi *= 1 + taxa_cdi
        espelho = espelho * (1 + taxa_cdi) + fluxo
        investido += fluxo

        pontos.append(PontoDiario(dia, patrimonio, investido, cota, cota_cdi, espelho, retorno))
        valor_anterior = patrimonio

    ultimo = pontos[-1]
    posicoes = []
    for ticker, classe in classes.items():
        qtd = quantidade[ticker]
        if qtd <= EPSILON and abs(realizado[ticker]) < 0.005 and proventos[ticker] < 0.005:
            continue
        preco_atual = precos_dia[ticker].get(fim) or precos_dia[ticker].get(calendario[-1], 0.0)
        valor = qtd * preco_atual
        resultado = valor - custo[ticker]
        posicoes.append(
            Posicao(
                ticker=ticker,
                classe=classe,
                quantidade=qtd,
                preco_medio=custo[ticker] / qtd if qtd > EPSILON else 0.0,
                custo=custo[ticker],
                preco_atual=preco_atual,
                valor=valor,
                resultado=resultado,
                resultado_pct=resultado / custo[ticker] * 100 if custo[ticker] > EPSILON else None,
                realizado=realizado[ticker],
                proventos=proventos[ticker],
            )
        )
    total = ultimo.patrimonio
    alocacao: dict[str, float] = defaultdict(float)
    for p in posicoes:
        p.peso = p.valor / total * 100 if total > EPSILON else 0.0
        if p.valor > EPSILON:
            alocacao[p.classe] += p.valor
    if caixa > 0.005:
        alocacao["CAIXA"] = caixa
    posicoes.sort(key=lambda p: (-p.valor, p.ticker))

    return Resultado(
        pontos=pontos,
        posicoes=posicoes,
        alocacao=dict(alocacao),
        mensal=_mensal(pontos),
        indicadores=_indicadores(pontos, aportado, resgatado, caixa, sum(proventos.values())),
    )


def _mensal(pontos: list[PontoDiario]) -> list[Mes]:
    meses: list[Mes] = []
    cota_base = cdi_base = 1.0
    for i, ponto in enumerate(pontos):
        fim_do_mes = i == len(pontos) - 1 or (pontos[i + 1].data.year, pontos[i + 1].data.month) != (
            ponto.data.year,
            ponto.data.month,
        )
        if fim_do_mes:
            meses.append(
                Mes(ponto.data.year, ponto.data.month,
                    (ponto.cota / cota_base - 1) * 100, (ponto.cota_cdi / cdi_base - 1) * 100)
            )
            cota_base, cdi_base = ponto.cota, ponto.cota_cdi
    return meses


def _indicadores(pontos, aportado, resgatado, caixa, total_proventos) -> dict[str, float | None]:
    ultimo = pontos[-1]
    rentabilidade = (ultimo.cota - 1) * 100
    cdi_periodo = (ultimo.cota_cdi - 1) * 100
    dias_corridos = (ultimo.data - pontos[0].data).days

    retornos = [p.retorno_dia for i, p in enumerate(pontos) if i > 0 and pontos[i - 1].patrimonio > EPSILON]
    volatilidade = statistics.stdev(retornos) * math.sqrt(252) * 100 if len(retornos) > 1 else None

    pico, max_drawdown = 0.0, 0.0
    for p in pontos:
        pico = max(pico, p.cota)
        max_drawdown = min(max_drawdown, (p.cota / pico - 1) * 100)

    anualizada = None
    if dias_corridos >= 30 and ultimo.cota > 0:
        anualizada = (ultimo.cota ** (365 / dias_corridos) - 1) * 100

    return {
        "patrimonio": ultimo.patrimonio,
        "total_aportado": aportado,
        "total_resgatado": resgatado,
        "investido_liquido": ultimo.investido_liquido,
        "lucro": ultimo.patrimonio - ultimo.investido_liquido,
        "proventos": total_proventos,
        "caixa": caixa,
        "rentabilidade": rentabilidade,
        "rentabilidade_anualizada": anualizada,
        "cdi_periodo": cdi_periodo,
        "pct_cdi": rentabilidade / cdi_periodo * 100 if cdi_periodo > EPSILON else None,
        "espelho_cdi": ultimo.espelho_cdi,
        "diferenca_cdi": ultimo.patrimonio - ultimo.espelho_cdi,
        "volatilidade": volatilidade,
        "max_drawdown": max_drawdown,
        "dias": dias_corridos,
        "inicio": pontos[0].data,
        "fim": ultimo.data,
    }
