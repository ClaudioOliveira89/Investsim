"""Filtros Jinja para exibir números e datas no padrão brasileiro."""
from hashlib import sha256
from decimal import Decimal

from app.simulador.regras import CLASSES

DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def numero(valor, casas: int = 2) -> str:
    if valor is None:
        return "—"
    texto = f"{Decimal(str(valor)):,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def moeda(valor, casas: int = 2) -> str:
    if valor is None:
        return "—"
    sinal = "−" if float(valor) < 0 else ""
    return f"{sinal}R$ {numero(abs(float(valor)), casas)}"


def preco(valor) -> str:
    """Preço unitário: 2 casas, ou mais para ativos de centavos."""
    if valor is None:
        return "—"
    return moeda(valor, 2 if abs(float(valor)) >= 1 else 6)


def pct(valor, casas: int = 2, sinal: bool = True) -> str:
    if valor is None:
        return "—"
    prefixo = "+" if sinal and float(valor) > 0 else ""
    return f"{prefixo}{numero(valor, casas)}%".replace("-", "−")


def quantidade(valor) -> str:
    if valor is None:
        return "—"
    texto = f"{Decimal(str(valor)):f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    inteiro, _, fracao = texto.partition(".")
    inteiro = f"{int(inteiro):,}".replace(",", ".")
    return f"{inteiro},{fracao}" if fracao else inteiro


def tendencia(valor) -> str:
    """Classe CSS para colorir alta/baixa."""
    if valor is None:
        return ""
    return "positivo" if float(valor) > 0.0001 else "negativo" if float(valor) < -0.0001 else ""


def data_br(valor) -> str:
    return valor.strftime("%d/%m/%Y") if valor else "—"


def data_hora_br(valor) -> str:
    return valor.strftime("%d/%m/%Y %H:%M") if valor else "—"


def mes_ano(ano_mes) -> str:
    ano, mes = ano_mes
    return f"{MESES[mes - 1]}/{str(ano)[2:]}"


def dia_semana(valor) -> str:
    return DIAS_SEMANA[valor.weekday()] if valor else ""


def classe_ativo(classe: str) -> str:
    return {"CAIXA": "Proventos em caixa"}.get(classe) or CLASSES.get(classe, classe)


def cor_ticker(ticker: str) -> int:
    """Gera uma cor estável para o avatar de cada ativo no terminal."""
    digest = sha256(str(ticker).encode("utf-8")).hexdigest()
    return int(digest[:4], 16) % 360


def registrar_filtros(app):
    app.jinja_env.filters.update(
        numero=numero, moeda=moeda, preco=preco, pct=pct, quantidade=quantidade, tendencia=tendencia,
        data_br=data_br, data_hora_br=data_hora_br, mes_ano=mes_ano, dia_semana=dia_semana,
        classe_ativo=classe_ativo, cor_ticker=cor_ticker,
    )
