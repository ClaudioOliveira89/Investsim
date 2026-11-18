"""Correções motivadas pelos feedbacks dos testadores (16-17/11/2026)."""
from app.models import Operacao, Usuario
from tests.integration.test_carteiras import _form, _operar


# --- Márcio: venda sem posição deve mostrar mensagem também no modo "valor em R$"
def test_venda_sem_posicao_por_valor_mostra_mensagem(logado_investidor, carteira, ativos, dias_atras):
    html = logado_investidor.post(
        f"/carteiras/{carteira.id}/operacoes/nova", data=_form(ativos["PETR4"], dias_atras(10), tipo="VENDA")
    ).get_data(as_text=True)
    assert "Você não tem posição em PETR4" in html


def test_venda_sem_posicao_por_cota_mostra_mensagem(logado_investidor, carteira, ativos, dias_atras):
    html = logado_investidor.post(
        f"/carteiras/{carteira.id}/operacoes/nova",
        data=_form(ativos["PETR4"], dias_atras(10), tipo="VENDA", modo="QUANTIDADE", quantidade="5", valor=""),
    ).get_data(as_text=True)
    assert "Você não tem posição em PETR4" in html


# --- Márcio: explicar a sobra quando o valor não fecha com o preço da cota
def test_compra_por_valor_avisa_sobra(logado_investidor, carteira, ativos, dias_atras):
    r = logado_investidor.post(
        f"/carteiras/{carteira.id}/operacoes/nova", data=_form(ativos["PETR4"], dias_atras(10), valor="100.00"),
        follow_redirects=True,
    )
    html = r.get_data(as_text=True)
    assert "informados" in html and "não foram usados" in html


# --- Márcio: tela de movimentações com busca e paginação
def test_movimentacoes_busca_e_paginacao(logado_investidor, carteira, ativos, dias_atras):
    for i in range(20):
        _operar(carteira, ativos["PETR4"], dias_atras(300 - i), quantidade=1)
    _operar(carteira, ativos["BTC"], dias_atras(5), modo="VALOR", valor=500)
    pagina1 = logado_investidor.get("/movimentacoes").get_data(as_text=True)
    assert "Página 1 de 2" in pagina1
    so_btc = logado_investidor.get("/movimentacoes?q=btc").get_data(as_text=True)
    assert "BTC" in so_btc and "PETR4" not in so_btc.split("<tbody>")[1]
    vendas = logado_investidor.get("/movimentacoes?tipo=VENDA").get_data(as_text=True)
    assert "Nenhuma movimentação encontrada" in vendas


def test_movimentacoes_nao_vaza_dados_de_outro_usuario(client, carteira, ativos, dias_atras, outro_investidor):
    _operar(carteira, ativos["PETR4"], dias_atras(30))
    client.post("/login", data={"email": outro_investidor.email, "senha": "Senha123"})
    assert "PETR4" not in client.get("/movimentacoes").get_data(as_text=True).split("<main")[1]


def test_detalhe_da_carteira_pagina_operacoes(logado_investidor, carteira, ativos, dias_atras):
    for i in range(12):
        _operar(carteira, ativos["PETR4"], dias_atras(100 - i), quantidade=1)
    html = logado_investidor.get(f"/carteiras/{carteira.id}").get_data(as_text=True)
    assert "Página 1 de 2" in html


# --- Eliseu: cards do ativo acompanham o período escolhido
def test_historico_devolve_estatisticas_do_periodo(logado_investidor, ativos):
    um = logado_investidor.get(f"/api/ativos/{ativos['PETR4'].id}/historico?periodo=1m").get_json()
    cinco = logado_investidor.get(f"/api/ativos/{ativos['PETR4'].id}/historico?periodo=5a").get_json()
    for corpo in (um, cinco):
        est = corpo["estatisticas"]
        assert est["minimo"] <= est["maximo"] and est["variacao"] is not None
    assert um["estatisticas"] != cinco["estatisticas"]


# --- Márcio: excluir a própria conta
def test_excluir_conta_exige_senha_e_confirmacao(logado_investidor, db, investidor):
    r = logado_investidor.post("/minha-conta/excluir", data={"senha": "errada", "confirmacao": "EXCLUIR"})
    assert "Senha incorreta." in r.get_data(as_text=True)
    r = logado_investidor.post("/minha-conta/excluir", data={"senha": "Senha123", "confirmacao": "talvez"})
    assert "Digite exatamente EXCLUIR." in r.get_data(as_text=True)
    assert db.session.get(Usuario, investidor.id) is not None


def test_excluir_conta_apaga_usuario_carteiras_e_operacoes(logado_investidor, db, investidor, carteira, ativos, dias_atras):
    _operar(carteira, ativos["PETR4"], dias_atras(30))
    r = logado_investidor.post("/minha-conta/excluir", data={"senha": "Senha123", "confirmacao": "excluir"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/login")
    assert db.session.get(Usuario, investidor.id) is None
    assert db.session.scalar(db.select(db.func.count(Operacao.id))) == 0
    assert logado_investidor.get("/").status_code == 302  # sessão encerrada


def test_unico_admin_nao_exclui_a_propria_conta(client, db, admin):
    client.post("/login", data={"email": admin.email, "senha": "Senha123"})
    r = client.post("/minha-conta/excluir", data={"senha": "Senha123", "confirmacao": "EXCLUIR"})
    assert "único administrador" in r.get_data(as_text=True)
    assert db.session.get(Usuario, admin.id) is not None


# --- Venda alcançável pela interface (qualquer perfil)
def test_posicao_tem_botao_vender_e_formulario_abre_como_venda(logado_investidor, carteira, ativos, dias_atras):
    _operar(carteira, ativos["PETR4"], dias_atras(30), quantidade=10)
    html = logado_investidor.get(f"/carteiras/{carteira.id}").get_data(as_text=True)
    link = f"/carteiras/{carteira.id}/operacoes/nova?ativo_id={ativos['PETR4'].id}&amp;tipo=VENDA"
    assert link in html
    form = logado_investidor.get(link.replace("&amp;", "&")).get_data(as_text=True)
    assert '<input checked id="tipo-1" name="tipo" required type="radio" value="VENDA">' in form


def test_pagina_do_ativo_tem_simular_venda(logado_investidor, carteira, ativos):
    assert "Simular venda" in logado_investidor.get("/mercado/PETR4").get_data(as_text=True)
