"""Camada Controller (MVC): recebe a requisição HTTP, aciona o Model e escolhe a View."""
from app.controllers import api, auth, carteiras, feedback, mercado, usuarios
from app.controllers.erros import registrar_tratadores


def registrar_controllers(app):
    for modulo in (auth, carteiras, mercado, usuarios, feedback, api):
        app.register_blueprint(modulo.bp)
    registrar_tratadores(app)
