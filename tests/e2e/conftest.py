"""Infraestrutura dos testes de ponta a ponta (E2E).

Sobe a aplicação real em uma thread (com CSRF ligado, como em produção), carrega
os dados de demonstração e controla um navegador de verdade via Playwright.

Navegador: por padrão usa o Microsoft Edge instalado no Windows
(E2E_CANAL=msedge). Em outros sistemas use E2E_CANAL=chrome ou instale o
Chromium do Playwright com `playwright install chromium` e defina E2E_CANAL="".
"""
import os
import socket
import threading

import pytest

pytest.importorskip("playwright")

from werkzeug.serving import make_server  # noqa: E402

from app import create_app  # noqa: E402
from app.config import TestConfig  # noqa: E402
from app.extensions import db  # noqa: E402
from app.seed import carregar_dados_demo  # noqa: E402


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def servidor(tmp_path_factory):
    banco = tmp_path_factory.mktemp("e2e") / "e2e.db"

    class ConfigE2E(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{banco.as_posix()}"
        SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
        WTF_CSRF_ENABLED = True

    app = create_app(ConfigE2E)
    with app.app_context():
        db.create_all()
        carregar_dados_demo()

    porta = _porta_livre()
    http = make_server("127.0.0.1", porta, app, threaded=True)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{porta}"
    http.shutdown()
    with app.app_context():
        db.engine.dispose()


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    canal = os.environ.get("E2E_CANAL", "msedge")
    return {**browser_type_launch_args, **({"channel": canal} if canal else {})}


@pytest.fixture()
def entrar(page, servidor):
    """Faz login pela tela, como um usuário faria."""

    def _entrar(email="investidor@investsim.com.br", senha="Senha123"):
        page.goto(f"{servidor}/login")
        page.fill("#email", email)
        page.fill("#senha", senha)
        page.click("button[type=submit]")
        page.wait_for_url(f"{servidor}/")
        return page

    return _entrar
