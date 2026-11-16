"""Terminal de mercado, API JSON, cadastro público e cache de cotações."""
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.models import Ativo, Cotacao, Sincronizacao, TaxaCDI, Usuario
from app.services import mercado_service
from app.simulador import fontes
from app.utils.tempo import hoje


# ------------------------------------------------------------------ mercado
@pytest.mark.parametrize(("classe", "ticker"), [("ACAO", "PETR4"), ("FII", "KNRI11"), ("CRIPTO", "BTC")])
def test_terminal_lista_ativos_por_classe(logado_investidor, ativos, classe, ticker):
    html = logado_investidor.get(f"/mercado/?classe={classe}").get_data(as_text=True)
    assert ticker in html and "12 meses" in html and "<svg class=\"minigrafico\"" in html


def test_classe_invalida_cai_em_acoes(logado_investidor, ativos):
    assert "PETR4" in logado_investidor.get("/mercado/?classe=XYZ").get_data(as_text=True)


def test_pagina_do_ativo(logado_investidor, ativos, carteira):
    html = logado_investidor.get("/mercado/knri11").get_data(as_text=True)
    assert "KNRI11" in html and "Proventos 12 meses" in html and "Dividend yield" in html
    assert "Simular compra" in html and f"/carteiras/{carteira.id}/operacoes/nova?ativo_id={ativos['KNRI11'].id}" in html
    assert logado_investidor.get("/mercado/NAOEXISTE").status_code == 404


# ------------------------------------------------------------------ API
def test_api_cotacao_usa_ultimo_pregao_no_fim_de_semana(logado_investidor, ativos):
    sabado = hoje() - timedelta(days=(hoje().weekday() - 5) % 7 or 7)
    corpo = logado_investidor.get(f"/api/cotacao?ativo_id={ativos['PETR4'].id}&data={sabado.isoformat()}").get_json()
    assert corpo["data_pedida"] == sabado.isoformat()
    assert corpo["data"] == (sabado - timedelta(days=1)).isoformat()  # sexta-feira
    assert corpo["preco"] > 0 and corpo["casas"] == 0
    corpo = logado_investidor.get(f"/api/cotacao?ativo_id={ativos['BTC'].id}&data={sabado.isoformat()}").get_json()
    assert corpo["data"] == sabado.isoformat() and corpo["casas"] == 8  # cripto negocia no sábado


@pytest.mark.parametrize(
    ("consulta", "status", "mensagem"),
    [("ativo_id=999&data=2026-01-05", 404, "Ativo não encontrado"),
     ("ativo_id={id}&data=05/01/2026", 400, "Data inválida"),
     ("ativo_id={id}&data=2999-01-01", 422, "futuro"),
     ("ativo_id={id}&data=2010-01-05", 422, "Não há cotação")],
)
def test_api_cotacao_erros(logado_investidor, ativos, consulta, status, mensagem):
    r = logado_investidor.get("/api/cotacao?" + consulta.format(id=ativos["PETR4"].id))
    assert r.status_code == status and mensagem in r.get_json()["erro"]


def test_api_historico(logado_investidor, ativos):
    corpo = logado_investidor.get(f"/api/ativos/{ativos['PETR4'].id}/historico?periodo=6m").get_json()
    assert 100 < len(corpo["pontos"]) < 140 and corpo["pontos"][0]["data"] < corpo["pontos"][-1]["data"]
    assert logado_investidor.get(f"/api/ativos/{ativos['PETR4'].id}/historico?periodo=9x").status_code == 400
    assert logado_investidor.get("/api/ativos/999/historico").status_code == 404


def test_api_exige_login(client, ativos):
    r = client.get(f"/api/cotacao?ativo_id={ativos['PETR4'].id}&data=2026-01-05")
    assert r.status_code == 401 and "Sessão expirada" in r.get_json()["erro"]


# ------------------------------------------------------------------ catálogo (admin)
def test_admin_cadastra_ativo_validando_na_fonte(logado_admin, db):
    dados = {"ticker": " itsa4 ", "nome": "Itaúsa PN", "classe": "ACAO", "simbolo_fonte": "itsa4"}
    r = logado_admin.post("/mercado/ativos/novo", data=dados, follow_redirects=True)
    assert "ITSA4 adicionado ao catálogo." in r.get_data(as_text=True)
    ativo = db.session.scalar(select(Ativo).where(Ativo.ticker == "ITSA4"))
    assert ativo.simbolo_fonte == "ITSA4" and ativo.ativo
    # as cotações são baixadas sob demanda, na primeira vez em que o ativo é exibido
    assert "ITSA4" in logado_admin.get("/mercado/ITSA4").get_data(as_text=True)
    assert db.session.scalar(select(func.count()).select_from(Cotacao).where(Cotacao.ativo_id == ativo.id)) > 0
    r = logado_admin.post("/mercado/ativos/novo", data=dados)
    assert "Esse ticker já está no catálogo." in r.get_data(as_text=True)


def test_admin_recusa_simbolo_sem_cotacao(logado_admin, db, monkeypatch):
    def falha(*_args, **_kwargs):
        raise fontes.FonteIndisponivel("símbolo desconhecido")

    monkeypatch.setattr(mercado_service, "_baixar_ativo", falha)
    dados = {"ticker": "XPTO3", "nome": "Inexistente", "classe": "ACAO", "simbolo_fonte": "XPTO3"}
    html = logado_admin.post("/mercado/ativos/novo", data=dados).get_data(as_text=True)
    assert "não retornou cotação" in html
    assert db.session.scalar(select(Ativo).where(Ativo.ticker == "XPTO3")) is None


def test_admin_oculta_ativo(logado_admin, ativos):
    logado_admin.post(f"/mercado/ativos/{ativos['BTC'].id}/alternar")
    assert ativos["BTC"].ativo is False


# ------------------------------------------------------------------ cadastro público
def test_cadastro_publico_cria_investidor_e_entra(client, db):
    dados = {"nome": "Dani Testadora", "email": "Dani@Email.com", "senha": "Senha123", "confirmacao": "Senha123"}
    r = client.post("/cadastro", data=dados, follow_redirects=True)
    assert "Conta criada. Bem-vindo(a), Dani!" in r.get_data(as_text=True)
    usuario = db.session.scalar(select(Usuario).where(Usuario.email == "dani@email.com"))
    assert usuario.perfil == Usuario.PERFIL_INVESTIDOR and not usuario.is_admin
    client.post("/logout")
    r = client.post("/cadastro", data=dados)
    assert "Já existe uma conta com este e-mail." in r.get_data(as_text=True)


def test_cadastro_valida_senha(client):
    r = client.post("/cadastro", data={"nome": "Zé", "email": "ze@x.com", "senha": "123", "confirmacao": "321"})
    html = r.get_data(as_text=True)
    assert "Use entre 3 e 120 caracteres." in html and "ao menos 8 caracteres" in html and "não conferem" in html


# ------------------------------------------------------------------ cache de cotações
def test_cache_baixa_uma_vez_e_reaproveita(app, ativos, monkeypatch):
    chamadas = []
    original = mercado_service._baixar_ativo

    def contar(*args, **kwargs):
        chamadas.append(args[2])
        return original(*args, **kwargs)

    monkeypatch.setattr(mercado_service, "_baixar_ativo", contar)
    inicio = hoje() - timedelta(days=100)
    assert mercado_service.sincronizar_ativos([ativos["PETR4"]], inicio) == []
    assert mercado_service.sincronizar_ativos([ativos["PETR4"]], inicio + timedelta(days=10)) == []
    assert chamadas == ["PETR4"]  # segunda chamada atendida pelo cache
    mercado_service.sincronizar_ativos([ativos["PETR4"]], inicio - timedelta(days=50))
    assert chamadas == ["PETR4", "PETR4"]  # período mais antigo: baixa de novo


def test_cache_vencido_atualiza_so_o_final(app, db, ativos, monkeypatch):
    inicio = hoje() - timedelta(days=100)
    mercado_service.sincronizar_ativos([ativos["PETR4"]], inicio)
    sync = db.session.get(Sincronizacao, f"cot:{ativos['PETR4'].id}")
    sync.atualizado_em -= timedelta(days=1)
    db.session.commit()
    janelas = []
    original = mercado_service._baixar_ativo

    def registrar(fonte, cliente, ticker, simbolo, classe, desde, fim):
        janelas.append(desde)
        return original(fonte, cliente, ticker, simbolo, classe, desde, fim)

    monkeypatch.setattr(mercado_service, "_baixar_ativo", registrar)
    mercado_service.sincronizar_ativos([ativos["PETR4"]], inicio)
    assert janelas == [hoje() - timedelta(days=7)]


def test_fonte_fora_do_ar_usa_dados_salvos_e_avisa(app, ativos, monkeypatch):
    inicio = hoje() - timedelta(days=30)
    mercado_service.sincronizar_ativos([ativos["PETR4"]], inicio)

    def falha(*_args, **_kwargs):
        raise fontes.FonteIndisponivel("fora do ar")

    monkeypatch.setattr(mercado_service, "_baixar_ativo", falha)
    avisos = mercado_service.sincronizar_ativos([ativos["PETR4"]], inicio - timedelta(days=30))
    assert len(avisos) == 1 and "usando dados salvos até" in avisos[0]
    assert mercado_service.precos([ativos["PETR4"]], inicio)["PETR4"]  # continua respondendo


def test_cdi_do_cache(app, db):
    inicio = hoje() - timedelta(days=60)
    assert mercado_service.sincronizar_cdi(inicio) == []
    total = db.session.scalar(select(func.count()).select_from(TaxaCDI))
    assert 35 < total < 50  # dias úteis em ~2 meses
    taxas = mercado_service.cdi(inicio)
    assert all(0.03 < v < 0.06 for v in taxas.values())


def test_cdi_fora_do_ar(app, monkeypatch):
    def falha(*_args, **_kwargs):
        raise fontes.FonteIndisponivel("BCB fora")

    monkeypatch.setattr(mercado_service, "_baixar_cdi", falha)
    assert "Banco Central indisponível" in mercado_service.sincronizar_cdi(hoje() - timedelta(days=10))[0]
