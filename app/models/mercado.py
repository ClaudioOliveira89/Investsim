"""Dados de mercado: catálogo de ativos e cache local de cotações, proventos e CDI.

O cache evita consultar a fonte externa a cada tela e mantém o sistema funcionando
(com os últimos dados conhecidos) se a fonte sair do ar.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.simulador.regras import CLASSES
from app.utils.tempo import agora


class Ativo(db.Model):
    __tablename__ = "ativo"
    __table_args__ = (
        CheckConstraint("classe IN ('ACAO', 'FII', 'ETF', 'CRIPTO')", name="ck_ativo_classe"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True)
    nome: Mapped[str] = mapped_column(String(120))
    classe: Mapped[str] = mapped_column(String(10))
    simbolo_fonte: Mapped[str] = mapped_column(String(30))  # código na fonte (ex.: PETR4, BTC)
    ativo: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(default=agora)

    @property
    def classe_descricao(self) -> str:
        return CLASSES.get(self.classe, self.classe)

    @property
    def is_bdr(self) -> bool:
        """BDRs de ações usam códigos B3 com sufixo 31–39 e operam em unidades inteiras."""
        sufixo = self.ticker[-2:]
        return self.classe == "ACAO" and sufixo in {
            "31", "32", "33", "34", "35", "36", "37", "38", "39"
        }

    def __repr__(self) -> str:
        return f"<Ativo {self.ticker}>"


class Cotacao(db.Model):
    __tablename__ = "cotacao"

    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativo.id", ondelete="CASCADE"), primary_key=True)
    data: Mapped[date] = mapped_column(primary_key=True)
    fechamento: Mapped[Decimal] = mapped_column(Numeric(20, 8))


class Provento(db.Model):
    __tablename__ = "provento"

    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativo.id", ondelete="CASCADE"), primary_key=True)
    data: Mapped[date] = mapped_column(primary_key=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(20, 8))


class TaxaCDI(db.Model):
    __tablename__ = "taxa_cdi"

    data: Mapped[date] = mapped_column(primary_key=True)
    taxa_dia: Mapped[Decimal] = mapped_column(Numeric(12, 8))  # % ao dia


class Sincronizacao(db.Model):
    """Controle do cache: qual período já foi baixado e quando foi atualizado."""

    __tablename__ = "sincronizacao"

    chave: Mapped[str] = mapped_column(String(60), primary_key=True)
    desde: Mapped[date]
    ate: Mapped[date]
    atualizado_em: Mapped[datetime]
    fonte: Mapped[str] = mapped_column(String(20))
