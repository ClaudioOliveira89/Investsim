"""Gera capturas de tela de todas as páginas (para documentação e revisão visual).

Uso:  python scripts/capturar_telas.py [pasta_destino]
Sobe a aplicação com dados de demonstração em um banco temporário e usa o
Microsoft Edge (via Playwright) para fotografar cada tela, no desktop e no celular.
"""
import sys
import tempfile
import threading
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from app import create_app  # noqa: E402
from app.config import TestConfig  # noqa: E402
from app.extensions import db  # noqa: E402
from app.seed import SENHA_DEMO, carregar_dados_demo  # noqa: E402
from app.utils.tempo import hoje  # noqa: E402

DESTINO = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/telas")
PORTA = 5099


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    banco = Path(tempfile.mkdtemp()) / "telas.db"

    class Config(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{banco.as_posix()}"
        SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
        WTF_CSRF_ENABLED = True

    app = create_app(Config)
    with app.app_context():
        db.create_all()
        carregar_dados_demo()
    http = make_server("127.0.0.1", PORTA, app, threaded=True)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{PORTA}"

    with sync_playwright() as p:
        navegador = p.chromium.launch(channel="msedge")

        def nova_pagina(largura=1440, altura=900, escala=1, tema="escuro"):
            pagina = navegador.new_page(viewport={"width": largura, "height": altura}, device_scale_factor=escala)
            pagina.add_init_script(f"localStorage.setItem('tema', '{tema}')")
            return pagina

        def foto(pagina, nome, inteira=True):
            pagina.wait_for_timeout(450)  # animações dos gráficos
            pagina.screenshot(path=DESTINO / f"{nome}.png", full_page=inteira)
            print("ok", nome)

        def entrar(pagina, email="investidor@investsim.com.br"):
            pagina.goto(f"{base}/login")
            pagina.fill("#email", email)
            pagina.fill("#senha", SENHA_DEMO)
            pagina.click("button[type=submit]")
            pagina.wait_for_url(f"{base}/")

        pagina = nova_pagina()
        pagina.goto(f"{base}/login")
        foto(pagina, "01-login", False)
        pagina.goto(f"{base}/cadastro")
        foto(pagina, "02-cadastro", False)

        entrar(pagina)
        foto(pagina, "03-painel")
        pagina.click("text=Carteira exemplo")
        pagina.wait_for_load_state("networkidle")
        foto(pagina, "04-relatorio")
        pagina.get_by_role("button", name="Patrimônio R$").click()
        foto(pagina, "05-relatorio-patrimonio", False)

        carteira_url = pagina.url
        pagina.goto(carteira_url + "/imprimir")
        foto(pagina, "06-relatorio-pdf")

        pagina.goto(carteira_url + "/operacoes/nova")
        pagina.select_option("#ativo_id", label="KNRI11 — Kinea Renda Imobiliária")
        dia = hoje() - timedelta(days=90)
        while dia.weekday() >= 5:
            dia -= timedelta(days=1)
        pagina.fill("#data", dia.isoformat())
        pagina.locator("#data").dispatch_event("change")
        pagina.fill("#valor", "5000")
        pagina.wait_for_timeout(600)
        foto(pagina, "07-nova-operacao", False)

        pagina.select_option("#ativo_id", label="WEGE3 — WEG ON")
        pagina.locator(".segmentado label", has_text="Venda").click()
        pagina.locator(".segmentado label", has_text="Quantidade").click()
        pagina.fill("#quantidade", "99999")
        pagina.click("text=Registrar operação")
        foto(pagina, "08-venda-bloqueada", False)

        for classe, nome in (("ACAO", "09-mercado-acoes"), ("FII", "10-mercado-fiis"), ("CRIPTO", "11-mercado-cripto")):
            pagina.goto(f"{base}/mercado/?classe={classe}")
            foto(pagina, nome)
        pagina.goto(f"{base}/mercado/KNRI11")
        pagina.wait_for_selector("text=Variação no período")
        foto(pagina, "12-ativo")

        pagina.goto(carteira_url)
        pagina.locator("section:has(#titulo-operacoes) tbody tr").first.get_by_role("button").click()
        foto(pagina, "13-modal-confirmacao", False)

        claro = nova_pagina(tema="claro")
        entrar(claro)
        claro.click("text=Carteira exemplo")
        claro.wait_for_load_state("networkidle")
        foto(claro, "14-relatorio-tema-claro")

        admin = nova_pagina()
        entrar(admin, "admin@investsim.com.br")
        admin.goto(f"{base}/mercado/ativos")
        foto(admin, "15-catalogo")
        admin.goto(f"{base}/feedback/")
        foto(admin, "16-feedback-formulario")
        admin.goto(f"{base}/nao-existe")
        foto(admin, "17-erro-404", False)

        celular = nova_pagina(390, 844, 2)
        entrar(celular)
        foto(celular, "18-celular-painel")
        celular.click("text=Carteira exemplo")
        celular.wait_for_load_state("networkidle")
        foto(celular, "19-celular-relatorio")
        celular.click("[data-alternar-menu]")
        celular.wait_for_timeout(300)
        foto(celular, "20-celular-menu", False)
        navegador.close()
    http.shutdown()
    with app.app_context():
        db.engine.dispose()


if __name__ == "__main__":
    main()
