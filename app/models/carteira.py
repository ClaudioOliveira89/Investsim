from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.simulador.regras import Movimento
from app.utils.tempo import agora


class Carteira(db.Model):
    """Carteira simulada de um usuário (ele pode ter várias: "Aposentadoria", "Cripto"...)."""

    __tablename__ = "carteira"
    __table_args__ = (UniqueConstraint("usuario_id", "nome", name="uq_carteira_usuario_nome"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)
    nome: Mapped[str] = mapped_column(String(80))
    descricao: Mapped[str | None] = mapped_column(Text)
    criada_em: Mapped[datetime] = mapped_column(default=agora)

    usuario = relationship("Usuario", back_populates="carteiras")
    operacoes = relationship(
        "Operacao",
        back_populates="carteira",
        cascade="all, delete-orphan",
        order_by="(Operacao.data, Operacao.id)",
    )

    def movimentos(self) -> list[Movimento]:
        return [op.movimento() for op in self.operacoes]


class Operacao(db.Model):
    """Compra ou venda simulada de um ativo, em uma data, pelo preço de fechamento do dia."""

    __tablename__ = "operacao"
    __table_args__ = (
        CheckConstraint("tipo IN ('COMPRA', 'VENDA')", name="ck_operacao_tipo"),
        CheckConstraint("quantidade > 0", name="ck_operacao_quantidade"),
        CheckConstraint("preco > 0", name="ck_operacao_preco"),
        CheckConstraint("taxas >= 0", name="ck_operacao_taxas"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    carteira_id: Mapped[int] = mapped_column(ForeignKey("carteira.id", ondelete="CASCADE"), index=True)
    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativo.id", ondelete="RESTRICT"), index=True)
    tipo: Mapped[str] = mapped_column(String(6))
    data: Mapped[date]
    quantidade: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    preco: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    taxas: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    observacao: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(default=agora)

    carteira = relationship("Carteira", back_populates="operacoes")
    ativo = relationship("Ativo")

    @property
    def valor_total(self) -> Decimal:
        bruto = self.quantidade * self.preco
        return bruto + self.taxas if self.tipo == "COMPRA" else bruto - self.taxas

    def movimento(self) -> Movimento:
        return Movimento(
            data=self.data,
            ticker=self.ativo.ticker,
            classe=self.ativo.classe,
            tipo=self.tipo,
            quantidade=float(self.quantidade),
            preco=float(self.preco),
            taxas=float(self.taxas or 0),
            id=self.id,
        )
