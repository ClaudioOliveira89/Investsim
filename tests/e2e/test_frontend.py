"""Testes E2E: o front-end (HTML + CSS + JavaScript) rodando num navegador de verdade."""
import re
import struct
import zlib
from datetime import timedelta

import pytest
from playwright.sync_api import expect

from app.utils.tempo import hoje

pytestmark = pytest.mark.e2e


def _png_minimo() -> bytes:
    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados))

    cabecalho = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", cabecalho) + bloco(b"IDAT", zlib.compress(b"\x00\x0f\x76\x6e")) + bloco(b"IEND", b"")


def _dia_util(dias_atras: int) -> str:
    dia = hoje() - timedelta(days=dias_atras)
    while dia.weekday() >= 5:
        dia -= timedelta(days=1)
    return dia.isoformat()


# ------------------------------------------------------------------ acesso
def test_login_valida_no_navegador_antes_de_enviar(page, servidor):
    page.goto(f"{servidor}/login")
    page.click("button[type=submit]")
    expect(page.locator("#email-erro-js")).to_have_text("Campo obrigatório.")
    expect(page).to_have_url(f"{servidor}/login")


def test_login_errado_mostra_mensagem(page, servidor):
    page.goto(f"{servidor}/login")
    page.fill("#email", "investidor@investsim.com.br")
    page.fill("#senha", "errada123")
    page.click("button[type=submit]")
    expect(page.get_by_role("alert")).to_contain_text("E-mail ou senha incorretos.")


def test_painel_com_carteira_exemplo(entrar):
    page = entrar()
    expect(page.get_by_role("heading", level=1)).to_have_text("Olá, Investidor!")
    expect(page.locator(".kpi")).to_have_count(4)
    expect(page.locator(".cartao-carteira", has_text="Carteira exemplo")).to_contain_text("% do CDI")


# ------------------------------------------------------------------ fluxo principal
def test_cadastro_carteira_compra_e_relatorio(page, servidor):
    page.goto(f"{servidor}/cadastro")
    page.fill("#nome", "Testadora E2E")
    page.fill("#email", "e2e@teste.com")
    page.fill("#senha", "Senha123")
    page.fill("#confirmacao", "Senha123")
    page.click("text=Criar minha conta")
    expect(page.get_by_role("status")).to_contain_text("Conta criada")

    page.fill("#nome", "Dividendos")
    page.click("text=Criar carteira")
    expect(page.get_by_role("heading", level=1)).to_have_text("Nova operação")

    page.select_option("#ativo_id", label="KNRI11 — Kinea Renda Imobiliária")
    page.fill("#data", _dia_util(200))
    page.locator("#data").dispatch_event("change")
    page.fill("#valor", "5000")
    expect(page.locator("[data-cotacao-preco]")).to_have_text(re.compile(r"R\$"))
    expect(page.locator("[data-resumo-quantidade]")).to_have_text(re.compile(r"^\d+$"))
    expect(page.locator("[data-resumo-total]")).to_have_text(re.compile(r"R\$\s?[\d.]+,\d{2}"))
    page.click("text=Registrar operação")

    expect(page.get_by_role("status").first).to_contain_text("Compra registrada")
    expect(page.locator(".veredito")).to_contain_text("CDI")
    expect(page.locator("#grafico-carteira")).to_be_visible()
    assert page.evaluate("() => !!Chart.getChart('grafico-carteira')")  # o gráfico foi desenhado
    expect(page.locator("text=Proventos recebidos")).to_be_visible()


def test_modo_quantidade_e_venda_maior_que_a_posicao(entrar, servidor):
    page = entrar()
    page.click("text=Carteira exemplo")
    page.click("text=Nova operação")
    page.select_option("#ativo_id", label="WEGE3 — WEG ON")
    page.locator(".segmentado label", has_text="Venda").click()
    page.locator(".segmentado label", has_text="Quantidade").click()
    expect(page.locator("#valor")).to_be_hidden()
    page.fill("#quantidade", "999999")
    page.click("text=Registrar operação")
    expect(page.locator(".campo--erro .campo__erro")).to_contain_text("excede a posição disponível")


def test_relatorio_alterna_grafico_de_patrimonio(entrar):
    page = entrar()
    page.click("text=Carteira exemplo")
    page.get_by_role("button", name="Patrimônio R$").click()
    expect(page.locator("[data-legenda-grafico]")).to_contain_text("Se estivesse no CDI")
    expect(page.get_by_role("button", name="Patrimônio R$")).to_have_attribute("aria-pressed", "true")
    assert page.evaluate("() => Chart.getChart('grafico-carteira').data.datasets.length") == 3


def test_excluir_operacao_pede_confirmacao(entrar):
    page = entrar()
    page.click("text=Carteira exemplo")
    linhas = page.locator("#titulo-operacoes ~ * tbody tr, section:has(#titulo-operacoes) tbody tr")
    total = linhas.count()
    linhas.first.get_by_role("button").click()  # a mais recente (pode ser excluída sem afetar vendas)
    modal = page.locator("#modal-confirmacao")
    expect(modal).to_be_visible()
    modal.get_by_role("button", name="Voltar").click()
    expect(linhas).to_have_count(total)
    linhas.first.get_by_role("button").click()
    modal.get_by_role("button", name="Confirmar").click()
    expect(page.get_by_role("status").first).to_contain_text("Operação excluída")
    expect(linhas).to_have_count(total - 1)


# ------------------------------------------------------------------ mercado
def test_terminal_de_mercado_e_grafico_do_ativo(entrar, servidor):
    page = entrar()
    page.goto(f"{servidor}/mercado/?classe=FII")
    expect(page.locator("tbody tr")).not_to_have_count(0)
    page.locator("tbody tr", has_text="HGLG11").click()
    expect(page.get_by_role("heading", level=1)).to_contain_text("HGLG11")
    expect(page.locator("[data-grafico-status]")).to_contain_text("Variação no período")
    page.get_by_role("button", name="5A").click()
    expect(page.get_by_role("button", name="5A")).to_have_attribute("aria-pressed", "true")
    page.click("text=Simular compra")
    expect(page.get_by_role("heading", level=1)).to_have_text("Nova operação")
    expect(page.locator("#ativo_id option:checked")).to_contain_text("HGLG11")


# ------------------------------------------------------------------ interface
def test_tema_claro_persiste(entrar, servidor):
    page = entrar()
    expect(page.locator("html")).to_have_attribute("data-tema", "escuro")
    page.locator("[data-alternar-tema]").click()
    expect(page.locator("html")).to_have_attribute("data-tema", "claro")
    page.reload()
    expect(page.locator("html")).to_have_attribute("data-tema", "claro")


def test_menu_lateral_no_celular(entrar, page):
    page.set_viewport_size({"width": 390, "height": 800})
    entrar()
    menu = page.locator("#menu-lateral")
    botao = page.locator("[data-alternar-menu]")
    expect(menu).not_to_be_in_viewport()
    botao.click()
    expect(menu).to_be_in_viewport()
    page.keyboard.press("Escape")
    expect(botao).to_have_attribute("aria-expanded", "false")


def test_segundo_envio_do_formulario_e_bloqueado(entrar, servidor):
    page = entrar()
    page.goto(f"{servidor}/carteiras/nova")
    page.fill("#nome", "Duplo clique")
    cancelados = page.evaluate("""() => {
        const resultado = [];
        document.addEventListener("submit", (e) => { resultado.push(e.defaultPrevented); e.preventDefault(); });
        const botao = document.querySelector("form[data-validar] button[type=submit]");
        botao.click();
        botao.click();
        return resultado;
    }""")
    assert cancelados == [False, True]


# ------------------------------------------------------------------ feedback dos testadores
def test_feedback_publico_com_print(page, servidor, tmp_path):
    imagem = tmp_path / "print.png"
    imagem.write_bytes(_png_minimo())
    page.goto(f"{servidor}/feedback/")
    page.fill("#nome_testador", "Testador E2E")
    page.fill("#funcionou", "Criei carteira e comparei com o CDI.")
    page.locator(".nota__opcao", has_text="5").click()
    page.set_input_files("#prints", str(imagem))
    expect(page.locator("[data-previas] img")).to_have_count(1)
    page.click("text=Enviar laudo de teste")
    expect(page.get_by_role("heading", level=1)).to_have_text("Laudo recebido. Obrigado!")


def test_feedback_bloqueia_mais_de_tres_prints(page, servidor, tmp_path):
    arquivos = []
    for i in range(4):
        caminho = tmp_path / f"p{i}.png"
        caminho.write_bytes(_png_minimo())
        arquivos.append(str(caminho))
    page.goto(f"{servidor}/feedback/")
    envios = []
    page.on("request", lambda r: envios.append(r.url) if r.method == "POST" else None)
    page.fill("#nome_testador", "Testador Limite")
    page.fill("#funcionou", "Quase tudo funcionou.")
    page.locator(".nota__opcao", has_text="3").click()
    page.set_input_files("#prints", arquivos)
    page.locator("#nome_testador").focus()
    page.click("text=Enviar laudo de teste")
    expect(page.locator(".campo--erro .campo__erro")).to_contain_text("no máximo 3 imagens")
    page.wait_for_timeout(300)
    assert envios == []
