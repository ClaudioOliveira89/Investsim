"""Tratamento centralizado de erros: o usuário sempre recebe uma página amigável
(ou JSON, nas rotas /api) e o detalhe técnico vai apenas para o log."""
from flask import jsonify, render_template, request
from flask_wtf.csrf import CSRFError
from sqlalchemy.exc import OperationalError

from app.extensions import db

MENSAGENS = {
    400: ("Requisição inválida", "Alguma informação enviada não pôde ser entendida."),
    403: ("Acesso negado", "Seu perfil não tem permissão para acessar esta área."),
    404: ("Página não encontrada", "O endereço acessado não existe ou o registro foi removido."),
    405: ("Ação não permitida", "Esta operação não pode ser feita dessa forma."),
    503: (
        "Banco de dados indisponível",
        "Não foi possível conectar ao banco de dados. Verifique se o PostgreSQL está ligado e se "
        "o DATABASE_URL do arquivo .env está correto (usuário, senha e nome do banco).",
    ),
    413: ("Arquivo muito grande", "O envio ultrapassou o limite de 8 MB. Reduza as imagens."),
    500: ("Erro interno", "Algo deu errado do nosso lado. A equipe foi avisada; tente novamente."),
}


def _resposta(codigo: int, descricao: str | None = None):
    titulo, texto = MENSAGENS.get(codigo, MENSAGENS[500])
    # Com o banco fora do ar, a página não pode consultar o usuário logado (menu lateral).
    sem_banco = codigo == 503
    if request.path.startswith("/api/"):
        return jsonify(erro=descricao or texto), codigo
    return render_template(
        "erros/erro.html", codigo=codigo, titulo=titulo, mensagem=descricao or texto,
        esconder_menu=sem_banco,
    ), codigo


def registrar_tratadores(app):
    for codigo in (400, 403, 404, 405, 413):
        app.register_error_handler(codigo, lambda e, c=codigo: _resposta(c))

    @app.errorhandler(CSRFError)
    def csrf(_erro):
        return _resposta(
            400, "O formulário expirou por segurança. Volte, recarregue a página e tente de novo."
        )

    @app.errorhandler(OperationalError)
    def banco_indisponivel(erro):
        db.session.rollback()
        app.logger.error("Falha de conexão com o banco: %s", erro.orig)
        return _resposta(503)

    @app.errorhandler(500)
    def interno(erro):
        db.session.rollback()
        app.logger.exception("Erro interno: %s", erro)
        return _resposta(500)
