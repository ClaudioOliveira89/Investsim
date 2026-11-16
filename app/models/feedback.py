from datetime import date, datetime

from sqlalchemy import CheckConstraint, ForeignKey, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.extensions import db
from app.utils.tempo import agora


class FeedbackTeste(db.Model):
    """Laudo de um testador (Situação-Problema 3).

    Os campos seguem o mínimo exigido pelo enunciado: nome de quem testou, data,
    o que funcionou, o que não funcionou e o que não foi testado.
    """

    __tablename__ = "feedback_teste"
    __table_args__ = (
        CheckConstraint("nota BETWEEN 1 AND 5", name="ck_feedback_nota"),
        CheckConstraint(
            "status IN ('NOVO', 'EM_ANALISE', 'CORRIGIDO', 'DESCARTADO')",
            name="ck_feedback_status",
        ),
    )

    STATUS = {
        "NOVO": "Novo",
        "EM_ANALISE": "Em análise",
        "CORRIGIDO": "Corrigido",
        "DESCARTADO": "Não será corrigido",
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_testador: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(120))
    perfil_testador: Mapped[str | None] = mapped_column(String(80))
    data_teste: Mapped[date]
    funcionou: Mapped[str] = mapped_column(Text)
    nao_funcionou: Mapped[str | None] = mapped_column(Text)
    nao_testado: Mapped[str | None] = mapped_column(Text)
    sugestoes: Mapped[str | None] = mapped_column(Text)
    nota: Mapped[int]
    navegador: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(12), default="NOVO")
    tratativa: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(default=agora)

    anexos = relationship(
        "FeedbackAnexo",
        back_populates="feedback",
        cascade="all, delete-orphan",
        order_by="FeedbackAnexo.id",
    )

    @property
    def status_descricao(self) -> str:
        return self.STATUS.get(self.status, self.status)


class FeedbackAnexo(db.Model):
    """Print de tela enviado junto com o feedback.

    O arquivo fica no próprio banco (BYTEA) para não se perder em hospedagens
    com disco efêmero.
    """

    __tablename__ = "feedback_anexo"
    __table_args__ = (
        CheckConstraint("tamanho_bytes BETWEEN 1 AND 2097152", name="ck_anexo_tamanho"),
        CheckConstraint(
            "tipo_mime IN ('image/png', 'image/jpeg', 'image/webp', 'image/gif')",
            name="ck_anexo_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    feedback_id: Mapped[int] = mapped_column(
        ForeignKey("feedback_teste.id", ondelete="CASCADE"), index=True
    )
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    tipo_mime: Mapped[str] = mapped_column(String(50))
    tamanho_bytes: Mapped[int]
    conteudo: Mapped[bytes] = deferred(mapped_column(LargeBinary))

    feedback = relationship("FeedbackTeste", back_populates="anexos")
