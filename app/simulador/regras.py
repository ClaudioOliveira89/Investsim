"""Regras de negócio das operações do simulador (Python puro)."""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

COMPRA = "COMPRA"
VENDA = "VENDA"
CLASSES = {
    "ACAO": "Ações e BDRs",
    "FII": "Fundos imobiliários",
    "ETF": "ETFs",
    "CRIPTO": "Criptoativos",
}
EPSILON = 1e-9


class RegraSimuladorError(Exception):
    def __init__(self, mensagem: str, campo: str | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.campo = campo


@dataclass(frozen=True)
class Movimento:
    data: date
    ticker: str
    classe: str
    tipo: str  # COMPRA ou VENDA
    quantidade: float
    preco: float
    taxas: float = 0.0
    id: int | None = None

    @property
    def valor_bruto(self) -> float:
        return self.quantidade * self.preco

    @property
    def fluxo(self) -> float:
        """Dinheiro que entra (+) ou sai (−) da carteira por causa da operação."""
        if self.tipo == COMPRA:
            return self.valor_bruto + self.taxas
        return -(self.valor_bruto - self.taxas)


def casas_decimais(classe: str) -> int:
    """Cripto aceita frações (8 casas); ações, FIIs e ETFs são negociados em unidades inteiras."""
    return 8 if classe == "CRIPTO" else 0


def validar_quantidade(classe: str, quantidade: float) -> None:
    if quantidade is None or quantidade <= 0:
        raise RegraSimuladorError("A quantidade precisa ser maior que zero.", campo="quantidade")
    casas = casas_decimais(classe)
    if casas == 0 and abs(quantidade - round(quantidade)) > EPSILON:
        raise RegraSimuladorError(
            f"{CLASSES.get(classe, classe)} são negociados em unidades inteiras.", campo="quantidade"
        )
    if casas and abs(quantidade * 10**casas - round(quantidade * 10**casas)) > 1e-6:
        raise RegraSimuladorError(f"Use no máximo {casas} casas decimais.", campo="quantidade")


def quantidade_por_valor(valor: float, preco: float, classe: str) -> float:
    """Quantas unidades cabem em um valor em reais (arredondando para baixo)."""
    if valor is None or valor <= 0:
        raise RegraSimuladorError("Informe um valor maior que zero.", campo="valor")
    if preco <= 0:
        raise RegraSimuladorError("Preço inválido para calcular a quantidade.")
    casas = casas_decimais(classe)
    fator = 10**casas
    quantidade = math.floor(valor / preco * fator + 1e-9) / fator
    if quantidade <= 0:
        minimo = preco / fator
        raise RegraSimuladorError(
            f"O valor não compra nem {'1 unidade' if casas == 0 else 'a fração mínima'} "
            f"(mínimo de R$ {minimo:,.2f}).".replace(",", "X").replace(".", ",").replace("X", "."),
            campo="valor",
        )
    return quantidade


def ordenar(movimentos: list[Movimento]) -> list[Movimento]:
    """Ordem cronológica; no mesmo dia, compras antes de vendas, depois pela ordem de registro."""
    return sorted(movimentos, key=lambda m: (m.data, 0 if m.tipo == COMPRA else 1, m.id or 0))


def validar_cronologia(movimentos: list[Movimento]) -> None:
    """Garante que nenhuma venda (em nenhum momento da história) exceda a posição."""
    posicao: dict[str, float] = defaultdict(float)
    for m in ordenar(movimentos):
        if m.tipo not in (COMPRA, VENDA):
            raise RegraSimuladorError("Tipo de operação inválido.", campo="tipo")
        if m.tipo == COMPRA:
            posicao[m.ticker] += m.quantidade
            continue
        if m.quantidade > posicao[m.ticker] + EPSILON:
            disponivel = posicao[m.ticker]
            if disponivel <= EPSILON:
                raise RegraSimuladorError(
                    f"Você não tem posição em {m.ticker} nesta carteira em {m.data:%d/%m/%Y}: "
                    "registre uma compra antes de vender.",
                    campo="quantidade",
                )
            raise RegraSimuladorError(
                f"Venda de {m.quantidade:g} {m.ticker} em {m.data:%d/%m/%Y} excede a posição "
                f"disponível nessa data ({disponivel:g}).",
                campo="quantidade",
            )
        posicao[m.ticker] -= m.quantidade
