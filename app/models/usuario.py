from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.utils.tempo import agora


class Usuario(UserMixin, db.Model):
    """Pessoa que usa o simulador (investidor) ou o administra."""

    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint("perfil IN ('ADMIN', 'INVESTIDOR')", name="ck_usuario_perfil"),
    )

    PERFIL_ADMIN = "ADMIN"
    PERFIL_INVESTIDOR = "INVESTIDOR"
    PERFIS = {PERFIL_ADMIN: "Administrador", PERFIL_INVESTIDOR: "Investidor"}

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    perfil: Mapped[str] = mapped_column(String(10), default=PERFIL_INVESTIDOR)
    ativo: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(default=agora)

    carteiras = relationship(
        "Carteira", back_populates="usuario", cascade="all, delete-orphan", order_by="Carteira.nome"
    )

    def definir_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_admin(self) -> bool:
        return self.perfil == self.PERFIL_ADMIN

    @property
    def is_active(self) -> bool:  # usado pelo Flask-Login para bloquear contas inativas
        return self.ativo

    @property
    def perfil_descricao(self) -> str:
        return self.PERFIS.get(self.perfil, self.perfil)

    def __repr__(self) -> str:
        return f"<Usuario {self.email}>"
