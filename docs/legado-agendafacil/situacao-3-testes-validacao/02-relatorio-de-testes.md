# 2. Relatório de testes — verificação e validação

> Situação-Problema 3: "Realizar e documentar os testes (verificação e validação) mostrando que
> o comportamento esperado foi realizado."

## 2.1 Resumo da execução (verificação automatizada)

**Data:** 15/11/2026 · **Ambiente:** Windows 11, Python 3.14.10, PostgreSQL 18.4, Microsoft Edge 157

| Nível | Testes | Resultado |
|---|---:|---|
| Unitários (`tests/unit`) | 80 | ✅ 80 passaram |
| Integração (`tests/integration`, SQLite) | 71 | ✅ 71 passaram |
| Integração com PostgreSQL real (`-m postgres`) | 9 | ✅ 9 passaram |
| Sistema / E2E no navegador (`tests/e2e`) | 11 | ✅ 11 passaram |
| **Total** | **171** | **✅ 171 passaram, 0 falharam** |
| Cobertura de código (`app/`) | — | **95%** |

A suíte de unidade + integração também foi executada **inteira contra o PostgreSQL**
(`TEST_DATABASE_URL`): 160 passaram.

Após a correção D16 foi incluído mais 1 teste de regressão (total: **172**).

Evidências (execução das 15:49, antes de D16): [`evidencias/resultado-pytest.txt`](evidencias/resultado-pytest.txt) (saída completa,
teste a teste) e [`evidencias/cobertura.txt`](evidencias/cobertura.txt).

## 2.2 Casos de teste principais e resultado

| ID | Cenário | Entrada | Resultado esperado | Obtido | Teste automatizado |
|---|---|---|---|---|---|
| CT01 | Login válido | e-mail com maiúsculas/espaço + senha correta | Entra e vê "Olá, …!" | ✅ | `test_login_com_sucesso_e_logout` |
| CT02 | Login inválido | senha errada / e-mail inexistente | "E-mail ou senha incorretos." (mesma mensagem) | ✅ | `test_login_invalido_tem_mensagem_generica` |
| CT03 | Conta desativada | usuário inativo | Não entra; mensagem específica | ✅ | `test_usuario_inativo_nao_entra` |
| CT04 | Controle de acesso | atendente acessa 6 rotas de admin | HTTP 403 "Acesso negado" | ✅ | `test_atendente_nao_acessa_area_administrativa` |
| CT05 | Cadastro de cliente válido | dados completos | Salvo, telefone/CPF normalizados | ✅ | `test_cadastrar_cliente` |
| CT06 | Cadastro inválido | nome "A", tel "123", CPF com dígito errado | 4 mensagens nos campos; nada gravado | ✅ | `test_cadastro_de_cliente_mostra_erros_de_validacao` |
| CT07 | Máscaras no navegador | digita `11987654321` | Campo mostra `(11) 98765-4321` | ✅ | E2E `test_mascaras_e_validacao_*` |
| CT08 | Agendamento válido | amanhã 10:00, corte 60 min | Fim 11:00, valor R$ 80,00, status Agendado | ✅ | `test_cria_agendamento_calculando_fim_e_valor` |
| CT09 | Horários livres na tela | Ana / Corte feminino / amanhã | Não oferece 08:30, 09:00, 09:30 (ocupado 09:00–09:45) | ✅ | E2E `test_agendamento_com_horarios_livres` |
| CT10 | Conflito de profissional (RN03) | 10:30 com Ana já ocupada 10–11 | Recusado com mensagem no campo Horário | ✅ | `test_conflito_de_horario_aparece_no_campo_hora` |
| CT11 | Valor-limite do expediente (RN02) | início 19:00 (60 min) × 19:30 | 19:00 aceito; 19:30 recusado | ✅ | `test_rn02_*` |
| CT12 | Horários encostados | 10–11 e 11–12 | Ambos aceitos | ✅ | `test_rn03_horarios_encostados_nao_conflitam` |
| CT13 | Concorrência no banco | dois INSERTs sobrepostos | PostgreSQL rejeita o segundo; usuário vê mensagem amigável | ✅ | `test_postgres.py::test_exclusion_constraint_*`, `test_servico_converte_*` |
| CT14 | Transições de status (RN07) | Agendado → Concluído | Recusado | ✅ | `test_rn07_transicoes_invalidas` |
| CT15 | Cancelamento sem motivo (RN08) | motivo vazio | Recusado no navegador e no servidor | ✅ | `test_rn08_*`, E2E `test_cancelamento_exige_motivo_*` |
| CT16 | Preço muda depois (RN10) | preço 80 → 120 | Agendamento continua R$ 80,00 | ✅ | `test_rn10_*` |
| CT17 | Excluir cliente com histórico (RN11) | cliente com agendamento | Bloqueado com explicação | ✅ | `test_excluir_cliente` |
| CT18 | Confirmação antes de excluir | clicar em Excluir → Voltar | Nada excluído; depois Confirmar exclui | ✅ | E2E `test_cadastrar_cliente_e_excluir_com_modal_*` |
| CT19 | Upload malicioso | arquivo `.png` que é PDF/EXE | Recusado ("não é uma imagem válida") | ✅ | `test_feedback_rejeita_arquivo_que_nao_e_imagem` |
| CT20 | CSRF | POST sem token | HTTP 400 com mensagem amigável | ✅ | `test_formulario_sem_token_csrf_e_rejeitado` |
| CT21 | Erro interno | exceção no servidor | Página "Erro interno" sem detalhes técnicos; erro no log | ✅ | `test_erro_500_amigavel_e_registrado` |
| CT22 | Responsividade | tela 390 px | Menu recolhido no ☰, abre e fecha (Esc) | ✅ | E2E `test_menu_lateral_no_celular` |
| CT23 | Relatório de laudos | 1 laudo com print | Relatório com os 5 campos exigidos + imagem; CSV | ✅ | `test_admin_trata_feedback_e_gera_relatorio` |

## 2.3 Defeitos encontrados na verificação (antes dos testadores)

Os testes, a inspeção visual e uma revisão de código independente encontraram defeitos reais,
que foram corrigidos antes da entrega aos testadores. Cada correção ganhou um teste de regressão
(os testes E2E de D13 e D14 foram conferidos: falham sem a correção e passam com ela). Detalhes no [laudo de qualidade](04-laudo-de-qualidade.md#parte-a--defeitos-encontrados-na-verificação-interna).

| ID | Defeito | Como foi encontrado |
|---|---|---|
| D01 | Login recusava e-mail colado com espaço no final | Teste de integração `test_login_com_sucesso_e_logout` falhou |
| D02 | Redirecionamento aberto no parâmetro `voltar_para` | Revisão de código |
| D03 | Botão de menu ☰ aparecia no desktop | Inspeção visual das capturas de tela |
| D04 | Fundo do menu lateral terminava antes do fim em páginas longas | Inspeção visual |
| D05 | Teste E2E dependia do fuso do computador (falharia no GitHub Actions entre 21h e 0h) | Revisão dos testes |
| D06 | Conexões com o banco não eram fechadas ao fim dos testes | Avisos `ResourceWarning` do pytest |
| D07 | Página 2 da lista padrão de agendamentos mostrava atendimentos passados | Revisão de código independente |
| D08 | Parâmetros arbitrários da URL repassados aos links de paginação (`?endpoint=x` gerava erro 500) | Revisão de código independente |
| D09 | Injeção de fórmulas na exportação CSV (*CSV injection*) | Revisão de código independente |
| D10 | Editar um profissional apagava o vínculo com serviços inativos | Revisão de código independente |
| D11 | Erro 500 no PostgreSQL com e-mail de mais de 120 caracteres no laudo ou data de nascimento anterior a 1900 | Revisão de código independente |
| D12 | Datas extremas na URL (`?data=9999-12-31`) derrubavam a agenda e a lista (erro 500) | Revisão de código independente |
| D13 | A verificação das imagens no navegador não bloqueava o envio | Revisão de código independente |
| D14 | Duplo clique em "Salvar" e "Salvar e agendar" podia enviar o formulário duas vezes | Revisão de código independente |
| D16 | Sem banco configurado, o usuário via só "Erro interno"; e o `.env` não era lido ao iniciar por `python wsgi.py` | Uso real (primeira execução pelo botão ▶ do VS Code) |
| D15 | Era possível desativar um serviço com agendamentos futuros | Revisão de código independente |

## 2.4 Validação com usuários (teste de aceitação)

Resultado consolidado dos 5 testadores — preencher após receber os laudos
(veja o [guia](03-guia-validacao-com-usuarios.md)):

| # | Testador | Data | Nota | Funcionou | Não funcionou | Não testado |
|---|---|---|---|---|---|---|
| 1 | ✏️ | ✏️ | ✏️/5 | ✏️ | ✏️ | ✏️ |
| 2 | ✏️ | ✏️ | ✏️/5 | ✏️ | ✏️ | ✏️ |
| 3 | ✏️ | ✏️ | ✏️/5 | ✏️ | ✏️ | ✏️ |
| 4 | ✏️ | ✏️ | ✏️/5 | ✏️ | ✏️ | ✏️ |
| 5 | ✏️ | ✏️ | ✏️/5 | ✏️ | ✏️ | ✏️ |

> Os laudos completos ficam no PDF gerado por **Feedbacks de teste → Relatório para PDF**, salvo
> em `feedbacks/laudos-testadores.pdf`.
