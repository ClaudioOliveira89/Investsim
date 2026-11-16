"""Validações reutilizadas pelos formulários e testes."""
import re


def senha_forte(senha: str | None) -> bool:
    """Mínimo de 8 caracteres, com ao menos uma letra e um número."""
    if not senha or len(senha) < 8:
        return False
    return bool(re.search(r"[A-Za-z]", senha)) and bool(re.search(r"\d", senha))
