"""Gera docs/relatorio-correcoes-feedback.pdf (antes x depois dos feedbacks dos testadores).

Uso: python scripts/gerar_relatorio_feedback.py   (requer reportlab, ver requirements-dev.txt)
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

SAIDA = Path(__file__).resolve().parent.parent / "docs" / "relatorio-correcoes-feedback.pdf"

est = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=est["Heading1"], fontSize=16, textColor=colors.HexColor("#0f3d6e"), spaceBefore=10)
P = ParagraphStyle("P", parent=est["BodyText"], fontSize=9.5, leading=13)
C = ParagraphStyle("C", parent=P, fontSize=8.4, leading=10.8)
CH = ParagraphStyle("CH", parent=C, textColor=colors.white, fontName="Helvetica-Bold")
CAPA = ParagraphStyle("CAPA", parent=H1, fontSize=26, alignment=TA_CENTER, spaceBefore=140)
SUB = ParagraphStyle("SUB", parent=P, fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor("#444444"))


def tabela(linhas, larguras, cabecalho):
    dados = [[Paragraph(h, CH) for h in cabecalho]] + [[Paragraph(c, C) for c in linha] for linha in linhas]
    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3d6e")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c2cc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6fa")]),
    ]))
    return t


# (id, testador, feedback, antes, depois, arquivos, status)
ITENS = [
    ("1", "Stallone", "Calendário embutido do Firefox não permitia trocar a data; só digitando tudo.",
     "Campo de data dependia 100% do seletor nativo do navegador, sem alternativa.",
     "Botão “Calendário” (abre o seletor por JavaScript) e atalhos: Hoje, 1 mês atrás, 6 meses, 1 ano e 5 anos. "
     "O campo ganhou limites min/max explícitos e a dica foi reescrita.",
     "operacoes/form.html, operacao.js, app.css", "Corrigido"),
    ("2", "Stallone", "Não consegue representar retroativamente a carteira × CDI.",
     "Era preciso digitar cada data retroativa manualmente.",
     "Os atalhos de data retroativa (item 1) facilitam compras no passado; o relatório já compara com o CDI "
     "desde a primeira operação. Importação em lote (CSV) não foi implementada.",
     "operacoes/form.html, operacao.js", "Parcial"),
    ("3", "Eliseu", "Selecionou 5A e os cards continuaram mostrando 1A.",
     "Só o gráfico mudava com 1M/6M/1A/2A/5A; os cards eram fixos em 12 meses.",
     "A API de histórico passou a devolver estatísticas do período; os cards (variação, mínima, máxima, "
     "proventos/dividend yield) e seus rótulos mudam junto com o botão escolhido.",
     "api.py, ativo.html, graficos.js", "Corrigido"),
    ("4", "Eliseu", "Na venda, puxar o preço de fechamento da data da venda.",
     "O fechamento da data já era usado, mas a tela só dizia “Fechamento de dd/mm”, sem deixar claro que "
     "valia para a venda; mudar Compra/Venda não atualizava o resumo.",
     "Para vendas o texto passa a dizer “Preço de venda = fechamento de dd/mm/aaaa” e o resumo é "
     "recalculado ao alternar Compra/Venda.",
     "operacao.js", "Corrigido (clareza)"),
    ("5", "Márcio", "Comprar R$ 100 não totaliza R$ 100 e não mostra taxa.",
     "Em valor em R$, a quantidade é arredondada para baixo (unidades inteiras) e a sobra sumia sem explicação.",
     "O resumo mostra Valor informado, Quantidade, Sobra não usada, Taxas e Total, com nota explicativa; "
     "após salvar, uma mensagem informa quanto não foi utilizado. A dica do campo foi reescrita.",
     "operacao.js, operacoes/form.html, carteiras.py", "Corrigido"),
    ("6", "Márcio", "Venda sem posição por valor não exibiu nenhuma mensagem (por cota exibia).",
     "O erro era associado ao campo “quantidade”, escondido no modo valor, e ficava invisível. A mensagem "
     "também era técnica (“excede a posição disponível (0)”).",
     "No modo valor o erro é exibido no campo “valor”; nova mensagem: “Você não tem posição em X nesta "
     "carteira…: registre uma compra antes de vender.”. Erros de ativo inválido também deixaram de ser "
     "escondidos.",
     "carteira_service.py, regras.py, operacoes/form.html", "Corrigido"),
    ("7", "Márcio", "Lista de operações “infinita” e pesada; pediu listas paginadas.",
     "A carteira listava todas as operações de uma vez.",
     "Operações da carteira paginadas (10 por página) com consulta SQL paginada.",
     "carteiras.py, carteiras/relatorio.html", "Corrigido"),
    ("8", "Márcio", "Tela só para ver e pesquisar movimentações.",
     "Não existia.",
     "Nova página “Minhas movimentações” (menu lateral): todas as carteiras, busca por ticker/nome/observação, "
     "filtros por carteira, tipo e período, paginação de 15 itens e isolamento por usuário.",
     "carteiras.py, carteiras/movimentacoes.html, base.html", "Implementado"),
    ("9", "Márcio", "Não consegue excluir a própria conta.",
     "Não havia a opção.",
     "Menu do usuário > “Excluir minha conta”: exige senha e a palavra EXCLUIR; apaga carteiras e operações em "
     "cascata; impede que o único administrador se exclua.",
     "auth.py, usuario_service.py, forms, auth/excluir_conta.html", "Implementado"),
    ("10", "Márcio", "Token por e-mail ao criar conta (sistema profissional).",
     "Cadastro cria a conta e já faz login.",
     "Não implementado: exige provedor de e-mail (SMTP) e variáveis no Render. Fica no backlog (ver Pendências).",
     "—", "Backlog"),
    ("11", "Ricardo, John", "Sem problemas; John não testou outros navegadores/celular.",
     "—", "Nenhuma correção necessária. Recomendado testar em Chrome/Edge/Safari e no celular.", "—", "Sem ação"),
]


def montar():
    doc = SimpleDocTemplate(str(SAIDA), pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm,
                            topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                            title="InvestSim - Correções pós-feedback", author="Equipe InvestSim")
    h = [Paragraph("InvestSim", CAPA), Paragraph("Relatório de correções pós-feedback dos testadores", SUB),
         Spacer(1, 12), Paragraph("Antes × Depois · Testes realizados em 16 e 17/11/2026", SUB),
         Spacer(1, 6), Paragraph("Projeto Integrador — Cruzeiro do Sul", SUB), PageBreak()]

    h += [Paragraph("1. Resumo", H1),
          Paragraph("Cinco colegas testaram o InvestSim (Stallone, John, Ricardo, Eliseu e Márcio). Três deles "
                    "apontaram problemas ou sugestões. Este relatório lista cada ponto, o comportamento "
                    "<b>antes</b>, o comportamento <b>depois</b> e os arquivos alterados.", P), Spacer(1, 6)]
    contagem: dict[str, int] = {}
    for item in ITENS:
        chave = item[6].split(" ")[0]
        contagem[chave] = contagem.get(chave, 0) + 1
    h.append(tabela([[k, str(v)] for k, v in contagem.items()], [6 * cm, 3 * cm], ["Situação", "Itens"]))

    h.append(Paragraph("2. Antes × Depois por feedback", H1))
    h.append(tabela([[i[0], i[1], i[2], i[3], i[4], i[6]] for i in ITENS],
                    [0.7 * cm, 1.8 * cm, 3.6 * cm, 4 * cm, 5.7 * cm, 2 * cm],
                    ["#", "Quem", "Feedback", "Antes", "Depois", "Status"]))

    h.append(Paragraph("3. Arquivos alterados por item", H1))
    h.append(tabela([[i[0], i[5]] for i in ITENS if i[5] != "—"], [1 * cm, 16.8 * cm], ["#", "Arquivos"]))

    h += [Paragraph("4. Outras correções encontradas durante os testes", H1),
          Paragraph("Três testes automatizados já falhavam antes desta rodada: dois por mensagens de erro de ativo "
                    "inválido que não apareciam na tela (corrigido, ver item 6) e um por esperar a regra antiga de "
                    "“data futura recusada” (hoje datas futuras são projeções com preço manual); o teste foi "
                    "atualizado.", P)]

    h += [Paragraph("5. Verificação", H1),
          tabela([
              ["Suíte antes das mudanças", "125 aprovados, 3 falhas pré-existentes, 12 ignorados (PostgreSQL)"],
              ["Suíte depois das mudanças", "138 aprovados, 0 falhas, 12 ignorados (PostgreSQL)"],
              ["Novos testes", "10 testes em tests/integration/test_feedback_testadores.py (venda sem posição, "
                               "aviso de sobra, movimentações com busca/paginação/isolamento, estatísticas por "
                               "período, exclusão de conta)"],
              ["Lint", "ruff sem pendências"],
              ["Não verificado", "Aparência no Firefox real (calendário e atalhos): validar após o deploy"],
          ], [5 * cm, 12.8 * cm], ["Item", "Resultado"])]

    h += [Paragraph("6. Pendências e próximos passos", H1),
          Paragraph("• <b>Confirmação de e-mail por token</b> (item 10): escolher provedor de e-mail e configurar as "
                    "variáveis no Render.<br/>"
                    "• <b>Importação de operações em lote (CSV)</b> para simular carteiras retroativas (item 2).<br/>"
                    "• <b>Testes em outros navegadores e no celular</b> (sugestão do John).<br/>"
                    "• Validar o calendário e os atalhos de data no Firefox em produção.", P),
          Paragraph("7. Publicação", H1),
          Paragraph("As mudanças ficam no GitHub (branch main) e o Render reimplanta a cada push. Nenhuma migração "
                    "de banco é necessária: não houve alteração de tabelas.", P)]
    doc.build(h)
    print("Gerado:", SAIDA)


if __name__ == "__main__":
    montar()
