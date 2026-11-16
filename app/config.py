"""Configurações da aplicação.

Os valores sensíveis (chave secreta, URL do banco) vêm de variáveis de
ambiente, nunca do código-fonte (RNF de segurança).
"""
import os

from dotenv import load_dotenv

# Precisa acontecer antes das classes abaixo lerem os.environ (vale para
# "python wsgi.py", "flask run", gunicorn e testes).
load_dotenv()


def _normalizar_url_banco(url: str) -> str:
    """Provedores de hospedagem costumam entregar 'postgres://...'.

    O SQLAlchemy exige o nome do dialeto + driver, então convertemos para
    'postgresql+psycopg://...'.
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-inseguro-troque-no-.env")
    # Senha inicial das contas de demonstração. Em produção, configure como variável secreta.
    DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "").strip()
    SQLALCHEMY_DATABASE_URI = _normalizar_url_banco(
        os.environ.get(
            "DATABASE_URL",
            "sqlite:///investsim.db",  # produção define DATABASE_URL (PostgreSQL)
        )
    )
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Segurança de sessão
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True

    # Uploads (prints do formulário de feedback): 3 arquivos x 2 MB + folga
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    ANEXO_TAMANHO_MAX = 2 * 1024 * 1024
    ANEXO_QTD_MAX = 3
    ANEXO_TIPOS_PERMITIDOS = {"image/png", "image/jpeg", "image/webp", "image/gif"}

    FUSO_HORARIO = os.environ.get("FUSO_HORARIO", "America/Sao_Paulo")

    # Dados de mercado:
    #   "brapi" = cotações reais da B3/cripto (brapi.dev) + CDI oficial do Banco Central
    #   "demo"  = mercado simulado, funciona sem token e sem internet
    # Sem FONTE_DADOS definido: usa "brapi" se houver BRAPI_TOKEN, senão "demo".
    BRAPI_TOKEN = os.environ.get("BRAPI_TOKEN", "").strip()
    FONTE_DADOS = (os.environ.get("FONTE_DADOS") or ("brapi" if BRAPI_TOKEN else "demo")).strip().lower()
    # Por quantos minutos as cotações salvas valem antes de buscar de novo
    COTACAO_VALIDADE_MIN = int(os.environ.get("COTACAO_VALIDADE_MIN", "60"))

    ITENS_POR_PAGINA = 10


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "chave-de-teste"
    DEMO_PASSWORD = "Senha123"
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    FONTE_DADOS = "demo"  # testes nunca acessam a internet
