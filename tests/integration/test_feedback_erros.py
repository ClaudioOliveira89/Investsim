"""Formulário público de testes, área de tratativa e tratamento de erros."""
import io

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db
from app.models import FeedbackTeste

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32

LAUDO = {
    "nome_testador": "Paulo Testador",
    "email": "paulo@email.com",
    "perfil_testador": "Colega de curso",
    "data_teste": "2026-11-20",
    "funcionou": "Login, cadastro de cliente e agendamento funcionaram.",
    "nao_funcionou": "Ao filtrar por data sem 'até', esperava ver só um dia.",
    "nao_testado": "Área de administrador.",
    "sugestoes": "Mostrar o telefone do cliente na agenda.",
    "nota": "4",
}


def test_formulario_publico_de_feedback_sem_login(client):
    html = client.get("/feedback/").get_data(as_text=True)
    assert "Laudo de teste do sistema" in html and 'enctype="multipart/form-data"' in html


def test_envia_feedback_com_print(client, db):
    dados = {**LAUDO, "prints": [(io.BytesIO(PNG), "erro tela.png")]}
    r = client.post("/feedback/", data=dados, content_type="multipart/form-data", follow_redirects=True)
    assert "Laudo recebido. Obrigado!" in r.get_data(as_text=True)
    fb = db.session.scalar(db.select(FeedbackTeste))
    assert fb.nome_testador == "Paulo Testador" and len(fb.anexos) == 1


def test_feedback_campos_obrigatorios(client):
    html = client.post("/feedback/", data={"nome_testador": "", "funcionou": "", "data_teste": ""}).get_data(as_text=True)
    assert html.count("Campo obrigatório.") >= 3
    assert "Escolha uma nota de 1 a 5." in html


def test_feedback_rejeita_arquivo_que_nao_e_imagem(client):
    dados = {**LAUDO, "prints": [(io.BytesIO(b"%PDF-1.4 conteudo"), "doc.png")]}
    html = client.post("/feedback/", data=dados, content_type="multipart/form-data").get_data(as_text=True)
    assert "não é uma imagem válida" in html


def test_admin_trata_feedback_e_gera_relatorio(logado_admin, client, db):
    client.post("/feedback/", data={**LAUDO, "prints": [(io.BytesIO(PNG), "p.png")]}, content_type="multipart/form-data")
    fb = db.session.scalar(db.select(FeedbackTeste))

    html = logado_admin.get("/feedback/admin").get_data(as_text=True)
    assert "Paulo Testador" in html and "★★★★☆" in html

    r = logado_admin.post(f"/feedback/admin/{fb.id}", data={"status": "CORRIGIDO", "tratativa": "Filtro ajustado."}, follow_redirects=True)
    assert "Tratativa registrada." in r.get_data(as_text=True)
    assert fb.status == "CORRIGIDO"

    html = logado_admin.get("/feedback/admin/relatorio").get_data(as_text=True)
    for trecho in ("Nome de quem testou", "Data do teste", "O que testou e funcionou",
                   "O que testou e não funcionou", "Funcionalidade não testada", "20/11/2026", "Filtro ajustado."):
        assert trecho in html

    imagem = logado_admin.get(f"/feedback/admin/anexo/{fb.anexos[0].id}")
    assert imagem.status_code == 200 and imagem.mimetype == "image/png" and imagem.data == PNG
    assert logado_admin.get("/feedback/admin/anexo/999").status_code == 404

    csv = logado_admin.get("/feedback/admin/exportar.csv")
    assert csv.mimetype == "text/csv"
    texto = csv.data.decode("utf-8-sig")
    assert texto.startswith("id;testador;") and "Paulo Testador" in texto


# ------------------------------------------------------------------ erros
def test_pagina_404_amigavel(client):
    r = client.get("/nao-existe")
    assert r.status_code == 404 and "Página não encontrada" in r.get_data(as_text=True)


def test_405_amigavel(logado_admin):
    r = logado_admin.get("/logout")
    assert r.status_code == 405 and "Ação não permitida" in r.get_data(as_text=True)


def test_erro_500_amigavel_e_registrado(caplog):
    app = create_app(TestConfig)
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/explodir")
    def explodir():
        raise RuntimeError("falha simulada")

    r = app.test_client().get("/explodir")
    with app.app_context():
        _db.engine.dispose()
    assert r.status_code == 500
    html = r.get_data(as_text=True)
    assert "Erro interno" in html and "falha simulada" not in html
    assert "falha simulada" in caplog.text


class ConfigComCSRF(TestConfig):
    WTF_CSRF_ENABLED = True


@pytest.fixture()
def app_csrf():
    app = create_app(ConfigComCSRF)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()
        _db.engine.dispose()


def test_formulario_sem_token_csrf_e_rejeitado(app_csrf):
    r = app_csrf.test_client().post("/login", data={"email": "a@a.com", "senha": "x"})
    assert r.status_code == 400
    assert "O formulário expirou por segurança" in r.get_data(as_text=True)


def test_upload_maior_que_o_limite_retorna_413(client):
    grande = {**LAUDO, "prints": [(io.BytesIO(b"0" * (9 * 1024 * 1024)), "g.png")]}
    r = client.post("/feedback/", data=grande, content_type="multipart/form-data")
    assert r.status_code == 413 and "Arquivo muito grande" in r.get_data(as_text=True)


class ConfigSemBanco(TestConfig):
    # Porta 1: nenhum PostgreSQL escutando -> conexão recusada na hora
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg://ninguem:senha@127.0.0.1:1/inexistente"
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"connect_timeout": 2}}


def test_banco_indisponivel_mostra_mensagem_clara():
    """Regressão D16: sem banco, o usuário via "Erro interno" genérico."""
    app = create_app(ConfigSemBanco)
    cliente = app.test_client()
    r = cliente.post("/login", data={"email": "admin@investsim.com.br", "senha": "Senha123"})
    html = r.get_data(as_text=True)
    assert r.status_code == 503
    assert "Banco de dados indisponível" in html and "DATABASE_URL" in html
    assert "psycopg" not in html  # detalhe técnico só no log
    r = cliente.get("/api/cotacao?ativo_id=1&data=2026-11-02")
    assert r.status_code in (401, 503)  # API nunca devolve página HTML de erro
    with app.app_context():
        _db.engine.dispose()
