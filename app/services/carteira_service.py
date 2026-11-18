"""Casos de uso das carteiras: cadastrar, operar e gerar o relatório comparado ao CDI."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.extensions import db
from app.models import Ativo, Carteira, Operacao, Usuario
from app.services import mercado_service
from app.services.excecoes import RegraNegocioError
from app.simulador.calculos import Resultado, simular
from app.simulador.regras import (
    COMPRA,
    VENDA,
    Movimento,
    RegraSimuladorError,
    quantidade_por_valor,
    validar_cronologia,
    validar_quantidade,
)
from app.utils.tempo import hoje

MODO_QUANTIDADE = "QUANTIDADE"
MODO_VALOR = "VALOR"


def _regra(erro: RegraSimuladorError) -> RegraNegocioError:
    return RegraNegocioError(erro.mensagem, campo=erro.campo)


# --------------------------------------------------------------------------- carteiras
def salvar_carteira(carteira: Carteira, dados: dict, usuario: Usuario) -> Carteira:
    nome = dados["nome"].strip()
    existente = db.session.scalar(
        select(Carteira).where(Carteira.usuario_id == usuario.id, func.lower(Carteira.nome) == nome.lower())
    )
    if existente and existente.id != carteira.id:
        raise RegraNegocioError("Você já tem uma carteira com esse nome.", campo="nome")
    carteira.nome = nome
    carteira.descricao = (dados.get("descricao") or "").strip() or None
    carteira.usuario = usuario
    db.session.add(carteira)
    db.session.commit()
    return carteira


def excluir_carteira(carteira: Carteira) -> None:
    db.session.delete(carteira)
    db.session.commit()


# --------------------------------------------------------------------------- operações
def registrar_operacao(
    carteira: Carteira, dados: dict, operacao: Operacao | None = None
) -> tuple[Operacao, list[str]]:
    """Cria ou edita uma operação. Sem preço informado, usa o fechamento da data."""
    operacao = operacao or Operacao()
    avisos: list[str] = []

    ativo = db.session.get(Ativo, dados.get("ativo_id") or 0)
    if ativo is None or (not ativo.ativo and ativo.id != operacao.ativo_id):
        raise RegraNegocioError("Escolha um ativo disponível.", campo="ativo_id")
    if dados.get("tipo") not in (COMPRA, VENDA):
        raise RegraNegocioError("Escolha compra ou venda.", campo="tipo")
    dia: date = dados["data"]
    if dia > hoje():
        if not dados.get("preco"):
            raise RegraNegocioError("Informe manualmente o preço projetado para uma operação futura.", campo="preco")

    preco = dados.get("preco")
    if preco:
        preco = float(preco)
    else:
        _, preco, avisos = mercado_service.preco_em(ativo, dia)

    try:
        if dados.get("modo") == MODO_VALOR:
            quantidade = quantidade_por_valor(float(dados.get("valor") or 0), preco, ativo.classe)
        else:
            quantidade = float(dados.get("quantidade") or 0)
        validar_quantidade(ativo.classe, quantidade)
        taxas = float(dados.get("taxas") or 0)
        if taxas < 0:
            raise RegraSimuladorError("As taxas não podem ser negativas.", campo="taxas")

        nova = Movimento(dia, ativo.ticker, ativo.classe, dados["tipo"], quantidade, preco, taxas,
                         id=operacao.id or 10**12)
        outras = [op.movimento() for op in carteira.operacoes if op.id != operacao.id]
        validar_cronologia([*outras, nova])
    except RegraSimuladorError as erro:
        # No modo "valor em R$" o campo quantidade fica oculto: o erro precisa aparecer em "valor".
        if dados.get("modo") == MODO_VALOR and erro.campo == "quantidade":
            erro.campo = "valor"
        raise _regra(erro) from erro

    operacao.carteira = carteira
    operacao.ativo = ativo
    operacao.tipo = dados["tipo"]
    operacao.data = dia
    operacao.quantidade = Decimal(f"{quantidade:.8f}")
    operacao.preco = Decimal(f"{preco:.8f}")
    operacao.taxas = Decimal(f"{taxas:.2f}")
    operacao.observacao = (dados.get("observacao") or "").strip() or None
    db.session.add(operacao)
    db.session.commit()
    return operacao, avisos


def excluir_operacao(operacao: Operacao) -> None:
    restantes = [op.movimento() for op in operacao.carteira.operacoes if op.id != operacao.id]
    try:
        validar_cronologia(restantes)
    except RegraSimuladorError as erro:
        raise RegraNegocioError(
            "Não é possível excluir esta compra: uma venda posterior depende dela. "
            f"Detalhe: {erro.mensagem}"
        ) from erro
    db.session.delete(operacao)
    db.session.commit()


# --------------------------------------------------------------------------- relatório
def relatorio(carteira: Carteira, fim: date | None = None) -> tuple[Resultado, list[str]]:
    operacoes = carteira.operacoes
    if not operacoes:
        return Resultado(), []
    hoje_atual = hoje()
    fim = fim or max(hoje_atual, max(op.data for op in operacoes))
    inicio = min(op.data for op in operacoes)
    inicio_dados = min(inicio, hoje_atual)
    ativos = list({op.ativo.id: op.ativo for op in operacoes}.values())

    avisos = mercado_service.sincronizar_ativos(ativos, inicio_dados)
    avisos += mercado_service.sincronizar_cdi(inicio_dados)
    if fim > hoje_atual:
        avisos.append(
            "Projeção até "
            f"{fim:%d/%m/%Y}: operações futuras usam o preço manual informado e as demais cotações "
            "ficam no último fechamento disponível; o CDI não acumula após o último dado publicado."
        )
    resultado = simular(
        carteira.movimentos(),
        mercado_service.precos(ativos, inicio_dados),
        mercado_service.proventos(ativos, inicio_dados),
        mercado_service.cdi(inicio_dados),
        fim,
    )
    return resultado, avisos
