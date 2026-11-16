"""Catálogo inicial de ativos, usuários e carteira de demonstração."""
from datetime import timedelta

from flask import current_app
from sqlalchemy import func, select

from app.extensions import db
from app.models import Ativo, Carteira, Usuario
from app.services import carteira_service
from app.services.excecoes import RegraNegocioError
from app.utils.tempo import hoje

USUARIOS = [
    ("Administrador", "admin@investsim.com.br", Usuario.PERFIL_ADMIN),
    ("Investidor Demo", "investidor@investsim.com.br", Usuario.PERFIL_INVESTIDOR),
]

# (ticker, nome, classe) — o símbolo na brapi é o próprio ticker
CATALOGO = [
    ("PETR4", "Petrobras PN", "ACAO"),
    ("VALE3", "Vale ON", "ACAO"),
    ("ITUB4", "Itaú Unibanco PN", "ACAO"),
    ("BBAS3", "Banco do Brasil ON", "ACAO"),
    ("BBDC4", "Bradesco PN", "ACAO"),
    ("WEGE3", "WEG ON", "ACAO"),
    ("ABEV3", "Ambev ON", "ACAO"),
    ("B3SA3", "B3 ON", "ACAO"),
    ("RENT3", "Localiza ON", "ACAO"),
    ("SUZB3", "Suzano ON", "ACAO"),
    ("PRIO3", "PRIO ON", "ACAO"),
    ("EGIE3", "Engie Brasil ON", "ACAO"),
    ("TAEE11", "Taesa Unit", "ACAO"),
    ("MGLU3", "Magazine Luiza ON", "ACAO"),
    ("KNRI11", "Kinea Renda Imobiliária", "FII"),
    ("HGLG11", "CSHG Logística", "FII"),
    ("XPML11", "XP Malls", "FII"),
    ("BTLG11", "BTG Pactual Logística", "FII"),
    ("MXRF11", "Maxi Renda", "FII"),
    ("KNCR11", "Kinea Rendimentos Imobiliários", "FII"),
    ("HGRU11", "CSHG Renda Urbana", "FII"),
    ("VISC11", "Vinci Shopping Centers", "FII"),
    ("BOVA11", "iShares Ibovespa", "ETF"),
    ("IVVB11", "iShares S&P 500 (em reais)", "ETF"),
    ("SMAL11", "iShares Small Cap", "ETF"),
    ("DIVO11", "It Now IDIV (dividendos)", "ETF"),
    ("HASH11", "Hashdex Nasdaq Crypto Index", "ETF"),
    ("GOLD11", "Trend Ouro", "ETF"),
    ("BTC", "Bitcoin", "CRIPTO"),
    ("ETH", "Ethereum", "CRIPTO"),
    ("SOL", "Solana", "CRIPTO"),
    # Ações brasileiras adicionais (seleção diversificada por setor).
    ("PETR3", "Petrobras ON", "ACAO"),
    ("ITSA4", "Itaúsa PN", "ACAO"),
    ("ITUB3", "Itaú Unibanco ON", "ACAO"),
    ("BBDC3", "Bradesco ON", "ACAO"),
    ("BPAC11", "BTG Pactual Unit", "ACAO"),
    ("SANB11", "Santander Brasil Unit", "ACAO"),
    ("BBSE3", "BB Seguridade ON", "ACAO"),
    ("CXSE3", "Caixa Seguridade ON", "ACAO"),
    ("PSSA3", "Porto Seguro ON", "ACAO"),
    ("AXIA3", "AXIA Energia ON", "ACAO"),
    ("CPLE3", "Copel ON", "ACAO"),
    ("EQTL3", "Equatorial Energia ON", "ACAO"),
    ("SBSP3", "Sabesp ON", "ACAO"),
    ("VIVT3", "Telefônica Brasil ON", "ACAO"),
    ("TIMS3", "TIM ON", "ACAO"),
    ("ENEV3", "Eneva ON", "ACAO"),
    ("VBBR3", "Vibra Energia ON", "ACAO"),
    ("UGPA3", "Ultrapar ON", "ACAO"),
    ("BRAV3", "Brava Energia ON", "ACAO"),
    ("GGBR4", "Gerdau PN", "ACAO"),
    ("GOAU4", "Metalúrgica Gerdau PN", "ACAO"),
    ("USIM5", "Usiminas PNA", "ACAO"),
    ("CMIN3", "CSN Mineração ON", "ACAO"),
    ("JBSS3", "JBS ON", "ACAO"),
    ("MBRF3", "MBRF Global Foods ON", "ACAO"),
    ("SLCE3", "SLC Agrícola ON", "ACAO"),
    ("SMTO3", "São Martinho ON", "ACAO"),
    ("EMBJ3", "Embraer ON", "ACAO"),
    ("RAIL3", "Rumo ON", "ACAO"),
    ("LREN3", "Lojas Renner ON", "ACAO"),
    ("ASAI3", "Assaí ON", "ACAO"),
    ("GMAT3", "Grupo Mateus ON", "ACAO"),
    ("RADL3", "Raia Drogasil ON", "ACAO"),
    ("HYPE3", "Hypera ON", "ACAO"),
    ("RDOR3", "Rede D'Or ON", "ACAO"),
    ("FLRY3", "Fleury ON", "ACAO"),
    ("TOTS3", "TOTVS ON", "ACAO"),
    ("YDUQ3", "Yduqs ON", "ACAO"),
    ("CYRE3", "Cyrela ON", "ACAO"),
    ("CURY3", "Cury ON", "ACAO"),
    ("DIRR3", "Direcional ON", "ACAO"),
    ("EZTC3", "EZTEC ON", "ACAO"),
    ("MULT3", "Multiplan ON", "ACAO"),
    ("ALOS3", "Allos ON", "ACAO"),
    ("CVCB3", "CVC Brasil ON", "ACAO"),
    ("VAMO3", "Vamos ON", "ACAO"),
    # BDRs da B3: mantidos na classe de ações e identificados visualmente no terminal.
    ("AAPL34", "BDR Apple", "ACAO"),
    ("MSFT34", "BDR Microsoft", "ACAO"),
    ("AMZO34", "BDR Amazon", "ACAO"),
    ("GOGL34", "BDR Alphabet (Google)", "ACAO"),
    ("NVDC34", "BDR NVIDIA", "ACAO"),
    ("TSLA34", "BDR Tesla", "ACAO"),
    ("M1TA34", "BDR Meta Platforms", "ACAO"),
    ("NFLX34", "BDR Netflix", "ACAO"),
    ("DISB34", "BDR Disney", "ACAO"),
    ("COCA34", "BDR Coca-Cola", "ACAO"),
    ("MCDC34", "BDR McDonald's", "ACAO"),
    ("AVGO34", "BDR Broadcom", "ACAO"),
    ("TSMC34", "BDR TSMC", "ACAO"),
    ("MUTC34", "BDR Micron Technology", "ACAO"),
    ("M2ST34", "BDR Strategy", "ACAO"),
    ("MELI34", "BDR Mercado Livre", "ACAO"),
    ("ROXO34", "BDR Nu Holdings", "ACAO"),
    ("INBR32", "BDR Inter & Co", "ACAO"),
    ("XPBR31", "BDR XP Inc.", "ACAO"),
    ("JBSS32", "BDR JBS N.V.", "ACAO"),
    ("AURA33", "BDR Aura Minerals", "ACAO"),
    ("JPMC34", "BDR JPMorgan Chase", "ACAO"),
    ("MSCD34", "BDR Mastercard", "ACAO"),
    ("ORCL34", "BDR Oracle", "ACAO"),
    ("ADBE34", "BDR Adobe", "ACAO"),
    ("ITLC34", "BDR Intel", "ACAO"),
    ("A1MD34", "BDR AMD", "ACAO"),
    ("QCOM34", "BDR Qualcomm", "ACAO"),
    ("BABA34", "BDR Alibaba", "ACAO"),
    ("DEFT31", "BDR DeFi Technologies", "ACAO"),
    ("SPCX34", "BDR SpaceX", "ACAO"),
    ("P2LT34", "BDR Palantir Technologies", "ACAO"),
    # FIIs: logística, recebíveis, shoppings, renda urbana e multiestratégia.
    ("ADSH11", "AD Shopping FII", "FII"),
    ("TRXF11", "TRX Real Estate FII", "FII"),
    ("VXXV11", "Genesis Multiestratégia FII", "FII"),
    ("GSFI11", "General Shopping e Outlets FII", "FII"),
    ("CPTS11", "Capitania Securities II FII", "FII"),
    ("XPLG11", "XP Log FII", "FII"),
    ("KNIP11", "Kinea Índices de Preços FII", "FII"),
    ("IRDM11", "Iridium Recebíveis Imobiliários FII", "FII"),
    ("GARE11", "Guardian Real Estate FII", "FII"),
    ("KNSC11", "Kinea Securities FII", "FII"),
    ("VGHF11", "Valora Hedge Fund FII", "FII"),
    ("HFOF11", "Hedge Top FOFII 3 FII", "FII"),
    ("HSML11", "HSI Malls FII", "FII"),
    ("PVBI11", "VBI Prime Properties FII", "FII"),
    ("BCFF11", "BTG Pactual Fundo de Fundos FII", "FII"),
    ("RBRR11", "RBR Rendimento High Grade FII", "FII"),
    ("HGCR11", "CSHG Recebíveis Imobiliários FII", "FII"),
    ("RECT11", "REC Renda Imobiliária FII", "FII"),
    ("RZTR11", "Riza Terrax FII", "FII"),
    ("MCCI11", "Mauá Capital Recebíveis Imobiliários FII", "FII"),
    ("RBRF11", "RBR Alpha Fundo de Fundos FII", "FII"),
    ("XPCI11", "XP Crédito Imobiliário FII", "FII"),
    ("RZAK11", "Riza Akin FII", "FII"),
    ("BCRI11", "Banestes Recebíveis Imobiliários FII", "FII"),
    ("VINO11", "Vinci Offices FII", "FII"),
    ("CPOF11", "Capitânia Office FII", "FII"),
    ("GGRC11", "GGR Covepi Renda FII", "FII"),
    ("PQDP11", "Parque Dom Pedro Shopping Center FII", "FII"),
    # ETFs: Ibovespa, exterior, renda fixa, setores e cripto.
    ("BOVV11", "It Now Ibovespa ETF", "ETF"),
    ("BOVB11", "Bradesco Ibovespa ETF", "ETF"),
    ("BOVX11", "Trend Ibovespa ETF", "ETF"),
    ("BBOV11", "BB ETF Ibovespa", "ETF"),
    ("NASD11", "Trend Nasdaq 100 ETF", "ETF"),
    ("LFTB11", "Investo Tesouro Selic ETF", "ETF"),
    ("LFTS11", "Investo Teva Tesouro Selic ETF", "ETF"),
    ("LLFT11", "BTG Pactual Teva Tesouro Selic ETF", "ETF"),
    ("SPXR11", "Trend S&P 500 com proteção cambial ETF", "ETF"),
    ("SPXI11", "It Now S&P 500 ETF", "ETF"),
    ("IBOV11", "It Now Ibovespa ETF", "ETF"),
    ("XBOV11", "Trend Ibovespa ETF", "ETF"),
    ("BOVS11", "Safra Ibovespa ETF", "ETF"),
    ("SOLH11", "Hashdex Nasdaq Solana ETF", "ETF"),
    ("TECK11", "It Now NYSE Fang+ ETF", "ETF"),
    ("BITH11", "Hashdex Nasdaq Bitcoin Reference ETF", "ETF"),
    ("QBTC11", "QR Bitcoin ETF", "ETF"),
    ("QETH11", "QR Ethereum ETF", "ETF"),
    ("BITI11", "Hashdex Bitcoin ETF", "ETF"),
    ("WRLD11", "Investo FTSE Global All Cap ETF", "ETF"),
    ("ACWI11", "Investo MSCI ACWI ETF", "ETF"),
    ("B5P211", "It Now IDA B5 P2 ETF", "ETF"),
    ("IMAB11", "It Now IMA-B ETF", "ETF"),
    ("IB5M11", "It Now IBrX-50 ETF", "ETF"),
    ("FIXA11", "Mirae Asset Renda Fixa ETF", "ETF"),
    # Criptoativos com suporte a frações no simulador.
    ("BNB", "BNB", "CRIPTO"),
    ("XRP", "XRP", "CRIPTO"),
    ("DOGE", "Dogecoin", "CRIPTO"),
    ("ADA", "Cardano", "CRIPTO"),
    ("LTC", "Litecoin", "CRIPTO"),
    ("BCH", "Bitcoin Cash", "CRIPTO"),
    ("TRX", "TRON", "CRIPTO"),
    ("AVAX", "Avalanche", "CRIPTO"),
    ("DOT1", "Polkadot", "CRIPTO"),
    ("LINK", "Chainlink", "CRIPTO"),
    ("XLM", "Stellar", "CRIPTO"),
    ("UNI3", "Uniswap", "CRIPTO"),
    ("ETC", "Ethereum Classic", "CRIPTO"),
    ("NEAR", "NEAR Protocol", "CRIPTO"),
    ("SUI", "Sui", "CRIPTO"),
    ("APT", "Aptos", "CRIPTO"),
    ("ATOM", "Cosmos", "CRIPTO"),
    ("TONCOIN", "Toncoin", "CRIPTO"),
    ("USDT", "Tether", "CRIPTO"),
    ("USDC", "USD Coin", "CRIPTO"),
    ("MATIC", "Polygon", "CRIPTO"),
]

# Códigos substituídos ou incorretos que podem existir em bancos já usados.
# São desativados sem apagar operações e histórico vinculados a eles.
CATALOGO_INATIVOS = ("BRFS3", "MRFG3", "EMBR3", "SMALL11", "LTFS11")

# (dias atrás, ticker, operação, valor em R$ ou quantidade)
CARTEIRA_EXEMPLO = [
    (730, "BOVA11", "COMPRA", ("VALOR", 10000)),
    (730, "IVVB11", "COMPRA", ("VALOR", 5000)),
    (730, "KNRI11", "COMPRA", ("VALOR", 8000)),
    (730, "HGLG11", "COMPRA", ("VALOR", 4000)),
    (730, "PETR4", "COMPRA", ("VALOR", 3000)),
    (730, "BTC", "COMPRA", ("VALOR", 2000)),
    (540, "WEGE3", "COMPRA", ("VALOR", 3000)),
    (540, "ITUB4", "COMPRA", ("VALOR", 2000)),
    (365, "BOVA11", "COMPRA", ("VALOR", 5000)),
    (365, "MXRF11", "COMPRA", ("VALOR", 3000)),
    (180, "PETR4", "VENDA", ("METADE", None)),
    (180, "ETH", "COMPRA", ("VALOR", 2000)),
    (60, "IVVB11", "COMPRA", ("VALOR", 3000)),
]


def carregar_catalogo() -> int:
    novos = 0
    for ticker, nome, classe in CATALOGO:
        if db.session.scalar(select(Ativo).where(Ativo.ticker == ticker)) is None:
            db.session.add(Ativo(ticker=ticker, nome=nome, classe=classe, simbolo_fonte=ticker))
            novos += 1
    for ticker in CATALOGO_INATIVOS:
        obsoleto = db.session.scalar(select(Ativo).where(Ativo.ticker == ticker))
        if obsoleto is not None:
            obsoleto.ativo = False
    db.session.commit()
    return novos


def _carteira_exemplo(usuario: Usuario) -> tuple[int, list[str]]:
    carteira = carteira_service.salvar_carteira(
        Carteira(),
        {"nome": "Carteira exemplo", "descricao": "Diversificada: ETFs, FIIs, ações e cripto, com aportes ao longo de 2 anos."},
        usuario,
    )
    ativos = {a.ticker: a for a in db.session.scalars(select(Ativo))}
    criadas, falhas = 0, []
    for dias, ticker, tipo, (modo, valor) in CARTEIRA_EXEMPLO:
        dados = {"ativo_id": ativos[ticker].id, "tipo": tipo, "data": hoje() - timedelta(days=dias), "taxas": 0}
        if modo == "METADE":
            posicao = sum(float(o.quantidade) * (1 if o.tipo == "COMPRA" else -1)
                          for o in carteira.operacoes if o.ativo.ticker == ticker)
            dados.update(modo="QUANTIDADE", quantidade=int(posicao // 2) or posicao)
        else:
            dados.update(modo=modo, valor=valor)
        try:
            carteira_service.registrar_operacao(carteira, dados)
            criadas += 1
        except RegraNegocioError as erro:
            db.session.rollback()
            falhas.append(f"{ticker}: {erro.mensagem}")
    return criadas, falhas


def _resumo_catalogo() -> str:
    ativos = db.session.scalars(select(Ativo).where(Ativo.ativo.is_(True))).all()
    bdrs = sum(ativo.is_bdr for ativo in ativos)
    acoes = sum(ativo.classe == "ACAO" and not ativo.is_bdr for ativo in ativos)
    quantidades = {classe: sum(ativo.classe == classe for ativo in ativos) for classe in ("FII", "ETF", "CRIPTO")}
    return (
        f"Catálogo disponível: {len(ativos)} ativos — {acoes} ações, {bdrs} BDRs, "
        f"{quantidades['FII']} FIIs, {quantidades['ETF']} ETFs e {quantidades['CRIPTO']} criptoativos."
    )


def carregar_dados_demo() -> str:
    novos = carregar_catalogo()
    if db.session.scalar(select(func.count(Usuario.id))):
        return f"{_resumo_catalogo()} {novos} ativo(s) novo(s). Demonstração existente preservada."
    senha_demo = current_app.config.get("DEMO_PASSWORD", "").strip()
    if not senha_demo:
        raise RuntimeError(
            "Defina DEMO_PASSWORD no ambiente antes de criar as contas de demonstração."
        )
    for nome, email, perfil in USUARIOS:
        usuario = Usuario(nome=nome, email=email, perfil=perfil)
        usuario.definir_senha(senha_demo)
        db.session.add(usuario)
    db.session.commit()
    investidor = db.session.scalar(select(Usuario).where(Usuario.perfil == Usuario.PERFIL_INVESTIDOR))
    criadas, falhas = _carteira_exemplo(investidor)
    resumo = (
        f"{_resumo_catalogo()} Carteira exemplo: {criadas} operações. "
        f"Contas de demonstração criadas; senha inicial definida pela variável DEMO_PASSWORD."
    )
    if falhas:
        resumo += "\nOperações não criadas (fonte de dados): " + "; ".join(falhas)
    return resumo
