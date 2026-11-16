"""InvestSim — simulador de carteiras de investimento comparadas ao CDI (padrão MVC).

  Model      -> app/models (entidades) + app/services (casos de uso) + app/simulador (núcleo puro)
  View       -> app/views/templates (HTML Jinja2) + app/views/static (CSS/JS)
  Controller -> app/controllers (blueprints Flask = rotas)
"""
import logging

try:
    # Usa os certificados do sistema operacional (Windows/macOS/Linux) nas conexões HTTPS,
    # como o navegador faz. Necessário em redes com antivírus/proxy que inspecionam TLS.
    import truststore

    truststore.inject_into_ssl()
except ImportError:  # pragma: no cover
    pass

from flask import Flask, flash, jsonify, redirect, request, url_for

from app.config import Config
from app.extensions import csrf, db, login_manager


def create_app(config_class=Config) -> Flask:
    app = Flask(
        __name__,
        template_folder="views/templates",
        static_folder="views/static",
    )
    app.config.from_object(config_class)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    _configurar_login()

    from app.utils.filtros import registrar_filtros

    registrar_filtros(app)

    from app.controllers import registrar_controllers

    registrar_controllers(app)

    from app.cli import registrar_comandos

    registrar_comandos(app)

    @app.context_processor
    def _globais():
        from app.utils.tempo import hoje

        return {
            "NOME_SISTEMA": "InvestSim",
            "MODO_DEMO": app.config.get("FONTE_DADOS") == "demo",
            "hoje_iso": hoje().isoformat(),
        }

    @app.after_request
    def _cabecalhos_seguranca(resposta):
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "same-origin")
        return resposta

    if not app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO)

    return app


def _configurar_login():
    from app.models import Usuario

    @login_manager.user_loader
    def carregar_usuario(usuario_id: str):
        return db.session.get(Usuario, int(usuario_id))

    @login_manager.unauthorized_handler
    def nao_autenticado():
        if request.path.startswith("/api/"):
            return jsonify(erro="Sessão expirada. Faça login novamente."), 401
        flash(login_manager.login_message, login_manager.login_message_category)
        return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
