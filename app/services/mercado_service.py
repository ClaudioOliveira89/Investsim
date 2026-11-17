"""Dados de mercado com cache no banco.

Fluxo: tela pede cotações -> verifica o cache (tabela ``sincronizacao``) -> baixa só o que
falta/está velho (em paralelo) -> grava -> responde a partir do banco. Se a fonte externa
cair, segue com os últimos dados conhecidos e devolve um aviso para a tela.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from flask import current_app
from sqlalchemy import delete, insert, select

from app.extensions import db
from app.models import Ativo, Cotacao, Provento, Sincronizacao, TaxaCDI
from app.services.excecoes import RegraNegocioError
from app.simulador.fontes import BancoCentral, Brapi, Demonstracao, FonteIndisponivel, Historico
from app.utils.tempo import agora, hoje

_bcb = BancoCentral()
_demo = Demonstracao()
_brapi: dict[str, Brapi] = {}


def nome_fonte() -> str:
    return "demo" if current_app.config.get("FONTE_DADOS") == "demo" else "brapi"


def nome_fonte_cdi() -> str:
    return "demo" if current_app.config.get("FONTE_CDI", "bcb") == "demo" else "bcb"


def _cliente_brapi() -> Brapi:
    token = current_app.config.get("BRAPI_TOKEN") or ""
    if token not in _brapi:
        _brapi[token] = Brapi(token or None)
    return _brapi[token]


def modo_demonstracao() -> bool:
    return nome_fonte() == "demo"


# --------------------------------------------------------------------------- download (só rede)
def _baixar_ativo(fonte: str, cliente, ticker: str, simbolo: str, classe: str, inicio: date, fim: date) -> Historico:
    if fonte == "demo":
        return _demo.historico(ticker, inicio, fim, classe=classe)
    return cliente.historico(simbolo, inicio, fim, classe=classe)


def _baixar_cdi(fonte: str, inicio: date, fim: date) -> dict[date, float]:
    return _demo.cdi(inicio, fim) if fonte == "demo" else _bcb.cdi(inicio, fim)


# --------------------------------------------------------------------------- controle do cache
def _janela_para_baixar(chave: str, inicio: date, fonte: str, validade_min: int | None = None) -> date | None:
    """Data a partir da qual é preciso baixar, ou None se o cache já atende."""
    sync = db.session.get(Sincronizacao, chave)
    if sync is None or sync.fonte != fonte or inicio < sync.desde:
        return inicio
    minutos = validade_min if validade_min is not None else current_app.config["COTACAO_VALIDADE_MIN"]
    validade = timedelta(minutes=minutos)
    if agora() - sync.atualizado_em > validade and sync.ate <= hoje():
        return max(sync.desde, sync.ate - timedelta(days=7))
    return None


def _marcar(chave: str, desde: date, fonte: str) -> None:
    sync = db.session.get(Sincronizacao, chave)
    if sync is None or sync.fonte != fonte:
        sync = sync or Sincronizacao(chave=chave)
        sync.desde = desde
    else:
        sync.desde = min(sync.desde, desde)
    sync.ate, sync.atualizado_em, sync.fonte = hoje(), agora(), fonte
    db.session.add(sync)


def _descricao_data(chave: str) -> str:
    sync = db.session.get(Sincronizacao, chave)
    return f"usando dados salvos até {sync.ate:%d/%m/%Y}" if sync else "sem dados disponíveis"


# --------------------------------------------------------------------------- sincronização
def sincronizar_ativos(ativos: list[Ativo], inicio: date) -> list[str]:
    """Garante cotações e proventos de ``inicio`` até hoje. Devolve avisos para a tela."""
    fonte, fim = nome_fonte(), hoje()
    pendentes = []
    for ativo in {a.id: a for a in ativos}.values():
        desde = _janela_para_baixar(f"cot:{ativo.id}", inicio, fonte)
        if desde is not None:
            pendentes.append((ativo, desde))
    if not pendentes:
        return []
    cliente = None if fonte == "demo" else _cliente_brapi()

    def tarefa(item):
        ativo, desde = item
        try:
            return item, _baixar_ativo(fonte, cliente, ativo.ticker, ativo.simbolo_fonte, ativo.classe, desde, fim)
        except FonteIndisponivel as erro:
            return item, erro

    with ThreadPoolExecutor(max_workers=min(8, len(pendentes))) as executor:
        resultados = list(executor.map(tarefa, pendentes))

    avisos = []
    for (ativo, desde), historico in resultados:
        chave = f"cot:{ativo.id}"
        if isinstance(historico, Exception):
            current_app.logger.warning("Cotação de %s indisponível: %s", ativo.ticker, historico)
            avisos.append(f"{ativo.ticker}: fonte de cotações indisponível — {_descricao_data(chave)}.")
            continue
        sync = db.session.get(Sincronizacao, chave)
        corte = date.min if sync is None or sync.fonte != fonte else desde
        db.session.execute(delete(Cotacao).where(Cotacao.ativo_id == ativo.id, Cotacao.data >= corte))
        db.session.execute(delete(Provento).where(Provento.ativo_id == ativo.id, Provento.data >= corte))
        if historico.fechamentos:
            db.session.execute(insert(Cotacao), [
                {"ativo_id": ativo.id, "data": d, "fechamento": round(v, 8)} for d, v in historico.fechamentos.items()
            ])
        if historico.dividendos:
            db.session.execute(insert(Provento), [
                {"ativo_id": ativo.id, "data": d, "valor": round(v, 8)} for d, v in historico.dividendos.items()
            ])
        _marcar(chave, desde, fonte)
    db.session.commit()
    return avisos


def sincronizar_cdi(inicio: date) -> list[str]:
    fonte = nome_fonte_cdi()
    desde = _janela_para_baixar("cdi", inicio, fonte, current_app.config["CDI_VALIDADE_MIN"])
    if desde is None:
        return []
    try:
        taxas = _baixar_cdi(fonte, desde, hoje())
    except FonteIndisponivel as erro:
        current_app.logger.warning("CDI indisponível: %s", erro)
        return [f"CDI: Banco Central indisponível — {_descricao_data('cdi')}."]
    sync = db.session.get(Sincronizacao, "cdi")
    corte = date.min if sync is None or sync.fonte != fonte else desde
    db.session.execute(delete(TaxaCDI).where(TaxaCDI.data >= corte))
    if taxas:
        db.session.execute(insert(TaxaCDI), [{"data": d, "taxa_dia": round(v, 8)} for d, v in taxas.items()])
    _marcar("cdi", desde, fonte)
    db.session.commit()
    return []


def validar_simbolo(ticker: str, simbolo: str, classe: str) -> str | None:
    """Confere na fonte se o símbolo tem cotação recente (sem gravar nada). Devolve o erro ou None."""
    fonte = nome_fonte()
    cliente = None if fonte == "demo" else _cliente_brapi()
    try:
        _baixar_ativo(fonte, cliente, ticker, simbolo, classe, hoje() - timedelta(days=10), hoje())
    except FonteIndisponivel as erro:
        return str(erro)
    return None


# --------------------------------------------------------------------------- consultas (banco)
def precos(ativos: list[Ativo], inicio: date) -> dict[str, dict[date, float]]:
    ids = {a.id: a.ticker for a in ativos}
    linhas = db.session.execute(
        select(Cotacao.ativo_id, Cotacao.data, Cotacao.fechamento).where(
            Cotacao.ativo_id.in_(ids), Cotacao.data >= inicio - timedelta(days=15)
        )
    )
    serie: dict[str, dict[date, float]] = {t: {} for t in ids.values()}
    for ativo_id, dia, valor in linhas:
        serie[ids[ativo_id]][dia] = float(valor)
    return serie


def proventos(ativos: list[Ativo], inicio: date) -> dict[str, dict[date, float]]:
    ids = {a.id: a.ticker for a in ativos}
    linhas = db.session.execute(
        select(Provento.ativo_id, Provento.data, Provento.valor).where(
            Provento.ativo_id.in_(ids), Provento.data >= inicio
        )
    )
    serie: dict[str, dict[date, float]] = {t: {} for t in ids.values()}
    for ativo_id, dia, valor in linhas:
        serie[ids[ativo_id]][dia] = float(valor)
    return serie


def cdi(inicio: date) -> dict[date, float]:
    linhas = db.session.execute(select(TaxaCDI.data, TaxaCDI.taxa_dia).where(TaxaCDI.data >= inicio))
    return {dia: float(taxa) for dia, taxa in linhas}


def preco_em(ativo: Ativo, dia: date) -> tuple[date, float, list[str]]:
    """Fechamento do ativo na data (ou no último pregão antes dela)."""
    avisos = sincronizar_ativos([ativo], dia - timedelta(days=15))
    linha = db.session.execute(
        select(Cotacao.data, Cotacao.fechamento)
        .where(Cotacao.ativo_id == ativo.id, Cotacao.data <= dia)
        .order_by(Cotacao.data.desc())
        .limit(1)
    ).first()
    if linha is None or (dia - linha.data).days > 15:
        raise RegraNegocioError(
            f"Não há cotação de {ativo.ticker} em {dia:%d/%m/%Y} (o ativo pode não existir nessa data "
            "ou a fonte está indisponível). Informe o preço manualmente.",
            campo="preco",
        )
    return linha.data, float(linha.fechamento), avisos


def resumo(ativos: list[Ativo]) -> tuple[list[dict], list[str]]:
    """Linhas do terminal de mercado: último preço, variações e minigráfico de 3 meses."""
    referencia = hoje()
    avisos = sincronizar_ativos(ativos, referencia - timedelta(days=380))
    series = precos(ativos, referencia - timedelta(days=365))
    linhas = []
    for ativo in ativos:
        serie = series.get(ativo.ticker) or {}
        datas = sorted(serie)
        if not datas:
            # Mantém o mesmo formato da linha com cotação. A página do ativo usa
            # var_12m para estilizar o KPI mesmo quando ultimo é None.
            linhas.append({
                "ativo": ativo,
                "ultimo": None,
                "data": None,
                "var_dia": None,
                "var_12m": None,
                "minigrafico": [],
            })
            continue
        ultimo_dia = datas[-1]
        ultimo = serie[ultimo_dia]
        anterior = serie[datas[-2]] if len(datas) > 1 else None
        ha_um_ano = [d for d in datas if d <= ultimo_dia - timedelta(days=365)] or datas[:1]
        tres_meses = [serie[d] for d in datas if d >= ultimo_dia - timedelta(days=92)]
        linhas.append({
            "ativo": ativo,
            "ultimo": ultimo,
            "data": ultimo_dia,
            "var_dia": (ultimo / anterior - 1) * 100 if anterior else None,
            "var_12m": (ultimo / serie[ha_um_ano[-1]] - 1) * 100,
            "minigrafico": tres_meses,
        })
    return linhas, avisos


def historico_grafico(ativo: Ativo, dias: int) -> tuple[list[dict], list[str]]:
    inicio = hoje() - timedelta(days=dias)
    avisos = sincronizar_ativos([ativo], inicio)
    serie = precos([ativo], inicio)[ativo.ticker]
    pontos = [{"data": d.isoformat(), "valor": round(v, 8)} for d, v in sorted(serie.items()) if d >= inicio]
    return pontos, avisos
