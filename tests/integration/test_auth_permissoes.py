"""Autenticação, sessão e controle de acesso por perfil."""
import pytest

from tests.conftest import SENHA, login


def test_pagina_de_login(client):
    resposta = client.get("/login")
    assert resposta.status_code == 200
    assert "Entrar no" in resposta.get_data(as_text=True)


def test_rotas_protegidas_redirecionam_para_login(client):
    resposta = client.get("/mercado/")
    assert resposta.status_code == 302
    assert "/login?next=/mercado/" in resposta.headers["Location"]


def test_login_com_sucesso_e_logout(client, admin):
    resposta = login(client, "ADMIN@teste.com ")  # aceita maiúsculas/espaços
    html = resposta.get_data(as_text=True)
    assert "Bem-vindo(a), Ana!" in html
    assert "Olá, Ana!" in html
    resposta = client.post("/logout", follow_redirects=True)
    assert "Você saiu do sistema." in resposta.get_data(as_text=True)
    assert client.get("/").status_code == 302


@pytest.mark.parametrize(("email", "senha"), [("admin@teste.com", "errada123"), ("naoexiste@teste.com", SENHA)])
def test_login_invalido_tem_mensagem_generica(client, admin, email, senha):
    html = login(client, email, senha).get_data(as_text=True)
    assert "E-mail ou senha incorretos." in html


def test_usuario_inativo_nao_entra(client, db, investidor):
    investidor.ativo = False
    db.session.commit()
    html = login(client, investidor.email).get_data(as_text=True)
    assert "conta está desativada" in html


def test_login_valida_campos(client):
    html = client.post("/login", data={"email": "invalido", "senha": ""}).get_data(as_text=True)
    assert "E-mail inválido." in html and "Campo obrigatório." in html


def test_redireciona_para_next_seguro_e_bloqueia_open_redirect(client, admin):
    r = client.post("/login?next=/mercado/", data={"email": admin.email, "senha": SENHA})
    assert r.headers["Location"].endswith("/mercado/")
    client.post("/logout")
    r = client.post("/login?next=https://site-malicioso.com", data={"email": admin.email, "senha": SENHA})
    assert r.headers["Location"] == "/"


def test_alterar_senha(logado_investidor, investidor):
    r = logado_investidor.post(
        "/minha-senha",
        data={"senha_atual": "errada", "nova_senha": "NovaSenha1", "confirmacao": "NovaSenha1"},
    )
    assert "Senha atual incorreta." in r.get_data(as_text=True)
    r = logado_investidor.post(
        "/minha-senha",
        data={"senha_atual": SENHA, "nova_senha": "fraca", "confirmacao": "fraca"},
    )
    assert "ao menos 8 caracteres" in r.get_data(as_text=True)
    r = logado_investidor.post(
        "/minha-senha",
        data={"senha_atual": SENHA, "nova_senha": "NovaSenha1", "confirmacao": "NovaSenha1"},
        follow_redirects=True,
    )
    assert "Senha alterada com sucesso." in r.get_data(as_text=True)
    assert investidor.verificar_senha("NovaSenha1")


@pytest.mark.parametrize(
    "url",
    ["/mercado/ativos", "/mercado/ativos/novo", "/usuarios/", "/usuarios/novo", "/feedback/admin", "/feedback/admin/relatorio"],
)
def test_investidor_nao_acessa_area_administrativa(logado_investidor, url):
    resposta = logado_investidor.get(url)
    assert resposta.status_code == 403
    assert "Acesso negado" in resposta.get_data(as_text=True)


def test_investidor_nao_ve_menu_administrativo(logado_investidor):
    html = logado_investidor.get("/").get_data(as_text=True)
    assert "Catálogo de ativos" not in html and "Feedbacks de teste" not in html


@pytest.mark.parametrize("url", ["/mercado/ativos", "/mercado/ativos/novo", "/usuarios/", "/feedback/admin"])
def test_admin_acessa_area_administrativa(logado_admin, url):
    assert logado_admin.get(url).status_code == 200


def test_cabecalhos_de_seguranca(client):
    r = client.get("/login")
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["X-Content-Type-Options"] == "nosniff"
