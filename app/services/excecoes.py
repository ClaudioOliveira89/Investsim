"""Exceções de domínio.

Os controllers capturam essas exceções e as transformam em mensagens amigáveis
para o usuário (flash ou JSON), sem expor detalhes técnicos.
"""


class RegraNegocioError(Exception):
    """Operação viola uma regra de negócio (ex.: horário já ocupado)."""

    def __init__(self, mensagem: str, campo: str | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.campo = campo


class NaoEncontradoError(RegraNegocioError):
    """Registro referenciado não existe (ou está inativo)."""
