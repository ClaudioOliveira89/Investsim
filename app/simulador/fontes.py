"""Fontes de dados de mercado — sem dependência de framework (portável para o Django da Hadar).

- ``Brapi``: cotações diárias e proventos da B3 e de cripto pela API pública brapi.dev
  (feita para uso por programas; requer token gratuito para a maioria dos ativos).
- ``BancoCentral``: CDI diário (% a.d.) da série 12 do SGS (dados abertos oficiais).
- ``Demonstracao``: dados sintéticos e determinísticos, para testes e para o sistema
  funcionar sem token ou sem internet.

Qualquer outra fonte (inclusive a da Hadar) pode ser plugada: basta devolver um ``Historico``.
"""
from __future__ import annotations

import hashlib
import math
import random
from bisect import bisect_right
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests

# Identificação honesta do cliente (nunca se passar por navegador).
USER_AGENT = "InvestSim/1.0 (simulador educacional de carteiras)"
FUSO_B3 = ZoneInfo("America/Sao_Paulo")


class FonteIndisponivel(Exception):
    """A fonte externa não respondeu ou não tem dados para o pedido."""


@dataclass
class Historico:
    """Fechamentos diários (BRL) e proventos por cota (BRL) na data ex, indexados por data."""

    fechamentos: dict[date, float] = field(default_factory=dict)
    dividendos: dict[date, float] = field(default_factory=dict)
    nome: str | None = None


# --------------------------------------------------------------------------- utilidades
def preencher_para_frente(serie: dict[date, float], datas: list[date]) -> dict[date, float]:
    """Último valor conhecido em cada data (fins de semana/feriados repetem o anterior)."""
    conhecidas = sorted(serie)
    resultado = {}
    for dia in datas:
        pos = bisect_right(conhecidas, dia)
        if pos:
            resultado[dia] = serie[conhecidas[pos - 1]]
    return resultado


def _data_local(valor) -> date | None:
    """Converte epoch (segundos) ou ISO-8601 em data no fuso da B3."""
    if valor in (None, ""):
        return None
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(valor, tz=FUSO_B3).date()
    return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).astimezone(FUSO_B3).date()


# --------------------------------------------------------------------------- brapi
class Brapi:
    URL = "https://brapi.dev/api"
    FAIXAS = [(31, "1mo"), (92, "3mo"), (183, "6mo"), (366, "1y"), (731, "2y"), (1827, "5y"), (3653, "10y")]

    def __init__(self, token: str | None = None, sessao: requests.Session | None = None, timeout: int = 20):
        self.token = token
        self.sessao = sessao or requests.Session()
        self.sessao.headers["User-Agent"] = USER_AGENT
        if token:
            self.sessao.headers["Authorization"] = f"Bearer {token}"
        self.timeout = timeout

    @classmethod
    def faixa(cls, inicio: date, hoje: date) -> str:
        dias = (hoje - inicio).days + 1
        return next((nome for limite, nome in cls.FAIXAS if dias <= limite), "max")

    def _get(self, caminho: str, params: dict, rotulo: str) -> dict:
        try:
            resposta = self.sessao.get(f"{self.URL}{caminho}", params=params, timeout=self.timeout)
        except requests.RequestException as erro:
            raise FonteIndisponivel("A fonte de cotações (brapi) não respondeu.") from erro
        if resposta.status_code in (401, 402, 403):
            raise FonteIndisponivel(
                f"A brapi não liberou {rotulo} (token ausente ou sem permissão no plano). Configure BRAPI_TOKEN."
            )
        if resposta.status_code == 404:
            raise FonteIndisponivel(f"{rotulo} não encontrado na brapi.")
        if resposta.status_code == 429:
            raise FonteIndisponivel("A brapi limitou as consultas. Tente novamente em instantes.")
        try:
            resposta.raise_for_status()
            return resposta.json()
        except (requests.RequestException, ValueError) as erro:
            raise FonteIndisponivel(f"Resposta inválida da brapi para {rotulo}.") from erro

    @staticmethod
    def _extrair(item: dict, inicio: date, fim: date) -> Historico:
        historico = Historico(nome=item.get("longName") or item.get("coinName") or item.get("shortName"))
        for linha in item.get("historicalDataPrice") or []:
            dia, fechamento = _data_local(linha.get("date")), linha.get("close")
            if dia and fechamento and fechamento > 0 and inicio <= dia <= fim:
                historico.fechamentos[dia] = float(fechamento)
        for provento in ((item.get("dividendsData") or {}).get("cashDividends")) or []:
            data_ex = _data_local(provento.get("exDate"))
            if data_ex is None and provento.get("lastDatePrior"):
                data_ex = _data_local(provento["lastDatePrior"]) + timedelta(days=1)
            valor = provento.get("rate")
            if data_ex and valor and inicio <= data_ex <= fim:
                historico.dividendos[data_ex] = historico.dividendos.get(data_ex, 0.0) + float(valor)
        return historico

    def historico(self, simbolo: str, inicio: date, fim: date, classe: str = "ACAO") -> Historico:
        faixa = self.faixa(inicio, date.today())
        if classe == "CRIPTO":
            dados = self._get("/v2/crypto", {"coin": simbolo, "currency": "BRL", "range": faixa, "interval": "1d"}, simbolo)
            itens = dados.get("coins") or []
        else:
            dados = self._get(f"/quote/{simbolo}", {"range": faixa, "interval": "1d", "dividends": "true"}, simbolo)
            itens = dados.get("results") or []
        if not itens:
            raise FonteIndisponivel(f"Sem dados de {simbolo} na brapi.")
        historico = self._extrair(itens[0], inicio, fim)
        if not historico.fechamentos:
            raise FonteIndisponivel(f"Nenhuma cotação de {simbolo} no período.")
        return historico


# --------------------------------------------------------------------------- Banco Central
class BancoCentral:
    URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
    JANELA_MAXIMA = timedelta(days=365 * 9)  # o SGS limita séries diárias a 10 anos por consulta

    def __init__(self, sessao: requests.Session | None = None, timeout: int = 20):
        self.sessao = sessao or requests.Session()
        self.sessao.headers["User-Agent"] = USER_AGENT
        self.timeout = timeout

    def cdi(self, inicio: date, fim: date) -> dict[date, float]:
        """CDI diário em % ao dia (ex.: 0.050788 = 0,050788% no dia)."""
        taxas: dict[date, float] = {}
        cursor = inicio
        while cursor <= fim:
            fatia_fim = min(fim, cursor + self.JANELA_MAXIMA)
            params = {
                "formato": "json",
                "dataInicial": cursor.strftime("%d/%m/%Y"),
                "dataFinal": fatia_fim.strftime("%d/%m/%Y"),
            }
            try:
                resposta = self.sessao.get(self.URL, params=params, timeout=self.timeout)
                if resposta.status_code == 404:  # período sem dias úteis
                    cursor = fatia_fim + timedelta(days=1)
                    continue
                resposta.raise_for_status()
                linhas = resposta.json()
            except (requests.RequestException, ValueError) as erro:
                raise FonteIndisponivel("O Banco Central não respondeu à consulta do CDI.") from erro
            for linha in linhas if isinstance(linhas, list) else []:
                dia = datetime.strptime(linha["data"], "%d/%m/%Y").date()
                taxas[dia] = float(linha["valor"])
            cursor = fatia_fim + timedelta(days=1)
        return taxas


# --------------------------------------------------------------------------- Demonstração
class Demonstracao:
    """Mercado sintético e reproduzível: o mesmo ticker gera sempre a mesma série."""

    CDI_ANUAL = 0.1215  # ~12,15% a.a.

    PERFIS = {  # classe: (preço inicial base, drift anual, volatilidade anual, dividend yield mensal)
        "ACAO": (30.0, 0.10, 0.30, 0.0),
        "FII": (100.0, 0.02, 0.12, 0.0085),
        "ETF": (110.0, 0.09, 0.20, 0.0),
        "CRIPTO": (50.0, 0.25, 0.65, 0.0),
    }
    PRECO_BASE = {"BTC": 250000.0, "ETH": 12000.0, "SOL": 600.0}  # ordem de grandeza em R$
    ORIGEM = date(2018, 1, 1)

    @staticmethod
    def _dias_uteis(inicio: date, fim: date, todos_os_dias: bool = False):
        dia = inicio
        while dia <= fim:
            if todos_os_dias or dia.weekday() < 5:
                yield dia
            dia += timedelta(days=1)

    def historico(self, simbolo: str, inicio: date, fim: date, classe: str = "ACAO") -> Historico:
        base, drift, vol, dy = self.PERFIS.get(classe, self.PERFIS["ACAO"])
        semente = int(hashlib.sha256(simbolo.encode()).hexdigest()[:12], 16)
        gerador = random.Random(semente)
        preco = self.PRECO_BASE.get(simbolo, base) * (0.5 + gerador.random())
        passos = 365 if classe == "CRIPTO" else 252
        mu, sigma = drift / passos, vol / math.sqrt(passos)
        historico = Historico(nome=f"{simbolo} (demonstração)")
        mes_anterior = None
        for dia in self._dias_uteis(self.ORIGEM, fim, todos_os_dias=classe == "CRIPTO"):
            preco *= math.exp(mu - sigma * sigma / 2 + sigma * gerador.gauss(0, 1))
            if dia >= inicio:
                historico.fechamentos[dia] = round(preco, 2)
                # FIIs: provento no primeiro pregão de cada mês
                if dy and (dia.year, dia.month) != mes_anterior:
                    historico.dividendos[dia] = round(preco * dy, 2)
            mes_anterior = (dia.year, dia.month)
        if not historico.fechamentos:
            raise FonteIndisponivel(f"Sem dados de demonstração para {simbolo} no período.")
        return historico

    def cdi(self, inicio: date, fim: date) -> dict[date, float]:
        taxa = ((1 + self.CDI_ANUAL) ** (1 / 252) - 1) * 100
        return {dia: round(taxa, 6) for dia in self._dias_uteis(inicio, fim)}
