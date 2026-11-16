# 4. Laudo de qualidade

> Campo "Laudo de Qualidade" da atividade de entrega: "Insira o laudo de qualidade do sistema,
> apontando os erros e as correções. Não esqueça de coletar as evidências."

**Sistema:** AgendaFácil · **Versão avaliada:** 1.0 · **Responsável:** ✏️ _seu nome_

## Resumo

| Indicador | Valor |
|---|---|
| Testes automatizados | 172 (unitários, integração, PostgreSQL e E2E): 100% passando |
| Cobertura de código | 95% |
| Defeitos encontrados na verificação interna | 16 (16 corrigidos) |
| Defeitos relatados pelos testadores | ✏️ (✏️ corrigidos, ✏️ justificados) |
| Nota média dos testadores | ✏️ / 5 |

## Parte A — Defeitos encontrados na verificação interna

Severidade: **Alta** = impede o uso ou é falha de segurança · **Média** = atrapalha o uso ·
**Baixa** = visual ou de manutenção.

### D01 — Login recusava e-mail com espaço no final · Média · ✅ Corrigido

- **Como apareceu:** o teste `test_login_com_sucesso_e_logout` envia `"ADMIN@teste.com "` (com
  espaço, como acontece ao colar um e-mail). O sistema respondia "E-mail inválido.".
- **Causa:** o validador de e-mail recebia o texto sem remover os espaços das pontas.
- **Correção:** todos os campos de texto dos formulários passaram a remover espaços nas pontas
  (`filters=APARAR` em `app/forms/__init__.py`).
- **Evidência:** o teste passa; o mesmo vale para nomes e e-mails em todos os cadastros.

### D02 — Redirecionamento aberto (*open redirect*) ao alterar status · Alta (segurança) · ✅ Corrigido

- **Como apareceu:** revisão de código do controller `agendamentos.alterar_status`, que
  redirecionava para qualquer endereço recebido no campo `voltar_para`.
- **Risco:** um link malicioso poderia levar o usuário, já logado, para um site falso.
- **Correção:** o destino passa pela função `url_segura()`, que só aceita caminhos internos.
- **Evidência:** `test_alterar_status_nao_redireciona_para_site_externo`.

### D03 — Botão de menu ☰ aparecia no desktop · Baixa · ✅ Corrigido

- **Como apareceu:** inspeção visual das capturas geradas por `scripts/capturar_telas.py`.
- **Causa:** a regra genérica `.botao-icone` vinha depois de `.topo__menu` no CSS e a sobrescrevia.
- **Correção:** a regra ficou mais específica (`.topo .topo__menu`).

### D04 — Fundo do menu lateral cortado em páginas longas · Baixa · ✅ Corrigido

- **Como apareceu:** inspeção visual (tela de novo agendamento com a página rolada).
- **Correção:** o fundo da coluna do menu passou a ser pintado no contêiner `.layout`.

### D05 — Teste E2E dependente do fuso horário da máquina · Média (confiabilidade) · ✅ Corrigido

- **Como apareceu:** revisão dos testes antes de configurar o GitHub Actions (servidores em UTC).
- **Causa:** o teste calculava "amanhã" com o relógio do computador, e o sistema usa o fuso de
  São Paulo. Entre 21h e 0h, os dois "amanhãs" seriam dias diferentes e o teste falharia.
- **Correção:** os testes passaram a usar o mesmo relógio da aplicação (`app.utils.tempo.hoje`).

### D06 — Conexões não encerradas nos testes · Baixa · ✅ Corrigido

- **Como apareceu:** 90 avisos `ResourceWarning` ao rodar a suíte contra o PostgreSQL.
- **Correção:** `db.engine.dispose()` ao final de cada fixture.

### D07 — Página 2 da lista padrão de agendamentos mostrava atendimentos passados · Média · ✅ Corrigido

- **Como apareceu:** revisão de código independente.
- **Causa:** o filtro "a partir de hoje" só valia quando a URL não tinha nenhum parâmetro; o link "Próxima" (`?page=2`) o desligava.
- **Correção:** o filtro padrão ignora o parâmetro `page` e passa a constar nos links de paginação.
- **Evidência:** `test_d07_pagina_2_mantem_o_filtro_padrao_a_partir_de_hoje`.

### D08 — Parâmetros arbitrários da URL repassados aos links de paginação (`?endpoint=x` gerava erro 500) · Baixa · ✅ Corrigido

- **Como apareceu:** revisão de código independente.
- **Causa:** todas as chaves da URL iam para `url_for(**argumentos)`.
- **Correção:** só os filtros conhecidos (`data_inicio`, `data_fim`, `profissional_id`, `status`) seguem para os links.
- **Evidência:** `test_d08_chaves_desconhecidas_na_url_nao_quebram_a_paginacao`.

### D09 — Injeção de fórmulas na exportação CSV (*CSV injection*) · Média (segurança) · ✅ Corrigido

- **Como apareceu:** revisão de código independente.
- **Causa:** texto do formulário público começando com `=`, `+`, `-` ou `@` virava fórmula ativa no Excel do administrador.
- **Correção:** células de texto livre que começam com esses caracteres recebem um apóstrofo (`celula_segura`).
- **Evidência:** `test_d09_csv_neutraliza_formulas`.

### D10 — Editar um profissional apagava o vínculo com serviços inativos · Baixa · ✅ Corrigido

- **Como apareceu:** revisão de código independente.
- **Causa:** a tela só listava serviços ativos e o salvamento substituía a lista inteira.
- **Correção:** serviços inativos já vinculados aparecem marcados, com a indicação "— inativo".
- **Evidência:** `test_d10_editar_profissional_preserva_servico_inativo`.

### D11 — Erro 500 no PostgreSQL com e-mail de mais de 120 caracteres no laudo ou data de nascimento anterior a 1900 · Baixa · ✅ Corrigido

- **Como apareceu:** revisão de código independente.
- **Causa:** o formulário aceitava valores que os domínios e CHECKs do banco recusam (o SQLite dos testes não acusava).
- **Correção:** limites de tamanho e de data nos formulários; mensagens padrão do WTForms passaram a sair em português.
- **Evidência:** `test_d11_campos_respeitam_os_limites_do_banco`.

### D12 — Datas extremas na URL (`?data=9999-12-31`) derrubavam a agenda e a lista (erro 500) · Baixa · ✅ Corrigido

- **Como apareceu:** revisão de código independente.
- **Causa:** somar ou subtrair um dia de datas-limite estoura o tipo `date`.
- **Correção:** datas aceitas entre 1900 e 2999 (`data_da_url`, validador `_data_na_faixa`) com aviso ao usuário.
- **Evidência:** `test_d12_datas_extremas_nao_derrubam_as_paginas`.

### D13 — A verificação das imagens no navegador não bloqueava o envio · Baixa · ✅ Corrigido

- **Como apareceu:** revisão de código independente.
- **Causa:** a validação geral limpava o erro dos prints ao sair do campo.
- **Correção:** a checagem das imagens passou a fazer parte da validação geral do campo.
- **Evidência:** E2E `test_feedback_bloqueia_mais_de_tres_prints_no_navegador`.

### D14 — Duplo clique em "Salvar" e "Salvar e agendar" podia enviar o formulário duas vezes · Baixa · ✅ Corrigido

- **Como apareceu:** revisão de código independente.
- **Causa:** o bloqueio de envio só desabilitava o botão clicado.
- **Correção:** o segundo envio é cancelado; ao voltar pelo histórico, o formulário é destravado.
- **Evidência:** E2E `test_segundo_envio_do_formulario_e_bloqueado`.

### D15 — Era possível desativar um serviço com agendamentos futuros · Baixa (regra de negócio) · ✅ Corrigido

- **Como apareceu:** revisão de código independente.
- **Causa:** a regra RN12 só valia para profissionais.
- **Correção:** RN12 estendida a serviços.
- **Evidência:** `test_d15_nao_desativa_servico_com_agendamento_futuro`.

### D16 — Primeira execução sem banco mostrava só "Erro interno" · Média · ✅ Corrigido

- **Como apareceu:** uso real — o sistema foi iniciado pelo botão ▶ do VS Code (`python wsgi.py`), sem `.env` e sem o banco PostgreSQL criado; o login exibia "500 — Erro interno".
- **Causa:** (1) falha de conexão com o banco caía no tratamento genérico de erro 500, sem orientar o usuário; (2) o `.env` era carregado depois de a configuração já ter sido lida, então era ignorado ao iniciar por `python wsgi.py`.
- **Correção:** página específica "Banco de dados indisponível" (HTTP 503) explicando o que verificar, sem consultar o banco ao renderizar; `.env` carregado no início de `app/config.py`; `python wsgi.py` agora prepara o banco (tabelas + dados de demonstração) quando está vazio.
- **Evidência:** `test_banco_indisponivel_mostra_mensagem_clara`.

## Parte B — Defeitos e sugestões relatados pelos testadores

> Preencha uma ficha por item relatado (copie o modelo). Não esconda as falhas: o enunciado
> pede transparência, e elas mostram o processo de melhoria contínua.

### T01 — ✏️ título curto do problema · Severidade ✏️ · Situação ✏️

- **Relatado por:** ✏️ (laudo #✏️, em ✏️/✏️/2026)
- **Descrição do testador:** ✏️
- **Evidência:** ✏️ salve o print em `evidencias/T01-antes.png` e insira aqui
- **Análise / causa:** ✏️
- **Correção:** ✏️ (commit `✏️`)
- **Evidência após a correção:** ✏️ `evidencias/T01-depois.png` e/ou teste automatizado

### Sugestões não implementadas (e por quê)

| Sugestão | Testador | Motivo |
|---|---|---|
| ✏️ | ✏️ | ✏️ ex.: fora do escopo desta versão (registrada como evolução futura) |

## Parecer final

✏️ Ex.: "O sistema atende aos requisitos funcionais RF01–RF17 e às regras RN01–RN14, comprovado por
172 testes automatizados e pela validação com 5 usuários. Os defeitos de severidade alta e média
foram corrigidos. Pendências: …"
