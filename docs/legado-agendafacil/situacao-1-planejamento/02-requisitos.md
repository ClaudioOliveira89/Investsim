# 2. Requisitos

## 2.1 Atores

| Ator | Descrição |
|---|---|
| **Atendente** | Recepção. Cadastra clientes, agenda, confirma, conclui e cancela atendimentos. |
| **Administrador** | Dono/gerente. Faz tudo o que o atendente faz e também gerencia serviços, profissionais, usuários e os feedbacks de teste. |
| **Testador** | Colega ou profissional convidado. Acessa apenas o formulário público de laudo de teste. |

## 2.2 Requisitos funcionais

| ID | Requisito | Ator | Prioridade |
|---|---|---|---|
| RF01 | Autenticar usuário por e-mail e senha e encerrar a sessão | Todos | Alta |
| RF02 | Permitir que o usuário altere a própria senha | Todos | Média |
| RF03 | Cadastrar, editar, consultar e excluir clientes | Atendente | Alta |
| RF04 | Buscar clientes por nome, telefone, e-mail ou CPF, com paginação | Atendente | Alta |
| RF05 | Exibir o histórico de atendimentos do cliente | Atendente | Média |
| RF06 | Cadastrar, editar, ativar e desativar serviços (nome, duração, preço) | Administrador | Alta |
| RF07 | Cadastrar, editar, ativar e desativar profissionais e os serviços que cada um realiza | Administrador | Alta |
| RF08 | Criar agendamento (cliente, profissional, serviço, data e hora) | Atendente | Alta |
| RF09 | Exibir os horários livres do profissional para o serviço e a data escolhidos | Atendente | Alta |
| RF10 | Reagendar (trocar profissional, serviço, data ou hora) | Atendente | Alta |
| RF11 | Confirmar, concluir, registrar falta ou cancelar (com motivo) um agendamento | Atendente | Alta |
| RF12 | Listar agendamentos com filtros por período, profissional e status | Atendente | Alta |
| RF13 | Exibir a agenda do dia em colunas por profissional | Atendente | Média |
| RF14 | Exibir painel com indicadores (hoje, pendentes, próximos 7 dias, faturamento do mês) | Atendente | Média |
| RF15 | Gerenciar usuários e perfis | Administrador | Alta |
| RF16 | Receber laudos de teste por formulário público, com até 3 prints | Testador | Alta |
| RF17 | Registrar a tratativa de cada feedback e gerar o relatório para PDF e a exportação CSV | Administrador | Alta |

## 2.3 Regras de negócio

| ID | Regra |
|---|---|
| RN01 | Não é permitido agendar em data/hora que já passou. |
| RN02 | O atendimento precisa começar e terminar dentro do horário de funcionamento (padrão 08:00–20:00) em um dia de funcionamento (padrão segunda a sábado). |
| RN03 | Um profissional não pode ter dois atendimentos ativos (agendado ou confirmado) com horários sobrepostos. Horários encostados (um termina às 10:00 e outro começa às 10:00) são permitidos. |
| RN04 | Um cliente não pode ter dois atendimentos ativos sobrepostos. |
| RN05 | O profissional precisa estar habilitado para o serviço escolhido. |
| RN06 | Cliente, profissional e serviço precisam existir; profissional e serviço precisam estar ativos. |
| RN07 | Mudanças de status seguem a máquina de estados (ver diagrama de estados). Status finais (concluído, cancelado, não compareceu) não mudam mais. |
| RN08 | O cancelamento exige motivo. |
| RN09 | Só é possível concluir ou registrar falta depois do horário de início. |
| RN10 | O valor do agendamento é o preço do serviço no momento do agendamento (alterações futuras de preço não mudam o histórico). |
| RN11 | Cliente com agendamentos no histórico não pode ser excluído. |
| RN12 | Profissional ou serviço com agendamentos futuros ativos não pode ser desativado. |
| RN13 | O sistema precisa manter ao menos um administrador ativo; ninguém pode desativar a si mesmo nem retirar o próprio perfil de administrador. |
| RN14 | E-mail de usuário é único. CPF de cliente é opcional, mas único quando informado. |

## 2.4 Requisitos não funcionais

| ID | Categoria | Requisito | Como foi atendido |
|---|---|---|---|
| RNF01 | Segurança | Senhas armazenadas apenas como hash com sal | `werkzeug.security` (scrypt/PBKDF2) |
| RNF02 | Segurança | Proteção contra CSRF em todos os formulários | Flask-WTF `CSRFProtect` |
| RNF03 | Segurança | Controle de acesso por perfil verificado no servidor | Decorador `admin_obrigatorio` → HTTP 403 |
| RNF04 | Segurança | Sem *open redirect*, cabeçalhos `X-Frame-Options`, `nosniff`, cookies `HttpOnly`/`SameSite` | `url_segura()`, `after_request`, `config.py` |
| RNF05 | Segurança | Upload aceita só imagens reais (verificação da assinatura do arquivo), até 3 × 2 MB; exportação CSV protegida contra injeção de fórmulas | `feedback_service.detectar_tipo_imagem`, `feedback.celula_segura` |
| RNF06 | Integridade | Regras críticas também garantidas pelo SGBD | Domínios, CHECKs, FKs e *exclusion constraint* em `schema.sql` |
| RNF07 | Usabilidade | Interface responsiva (desktop e celular) | CSS com *breakpoints*; tabelas viram cartões no celular |
| RNF08 | Usabilidade | Mensagens de erro claras, em português, junto do campo com problema | Validação no navegador + no servidor (ver catálogo em 04-ihc) |
| RNF09 | Usabilidade | Ações destrutivas pedem confirmação; operações são reversíveis sempre que possível | Modal de confirmação; ativar/desativar; cancelamento preserva histórico |
| RNF10 | Acessibilidade | Navegação por teclado, foco visível, rótulos e `aria-*` nos formulários | Link "pular para o conteúdo", `aria-invalid`, `aria-describedby`, `aria-live` |
| RNF11 | Confiabilidade | Erros inesperados exibem página amigável e são registrados em log, sem expor detalhes técnicos | `controllers/erros.py` |
| RNF12 | Manutenibilidade | Arquitetura MVC em camadas; regras de negócio independentes de HTTP | `models/`, `services/`, `controllers/`, `views/` |
| RNF13 | Testabilidade | Cobertura de testes automatizados ≥ 80% | 95% (ver relatório de testes) |
| RNF14 | Portabilidade | Configuração por variáveis de ambiente; roda em qualquer hospedagem com Python + PostgreSQL | `.env`, `render.yaml` |
| RNF15 | Desempenho | Índices para as consultas da agenda; páginas com paginação | Índices em `agendamento(profissional_id, inicio)` etc. |

## 2.5 Matriz de rastreabilidade (requisito → código → teste)

| Requisito | Implementação principal | Testes automatizados |
|---|---|---|
| RF01 | `controllers/auth.py` | `test_auth_permissoes.py::test_login_*`, E2E `test_login_*` |
| RF02 | `controllers/auth.py::alterar_senha` | `test_auth_permissoes.py::test_alterar_senha` |
| RF03, RF05 | `controllers/clientes.py`, `services/cadastro_service.py` | `test_cadastros.py::test_cadastrar_cliente`, `test_editar_cliente`, `test_excluir_cliente`; E2E `test_cadastrar_cliente_e_excluir_*` |
| RF04 | `controllers/clientes.py::listar` | `test_buscar_cliente_*`, `test_paginacao_de_clientes` |
| RF06 | `controllers/servicos.py` | `test_admin_cadastra_e_desativa_servico`, `test_servico_com_duracao_invalida` |
| RF07 | `controllers/profissionais.py` | `test_admin_cadastra_profissional_*`, `test_editar_profissional_*` |
| RF08 | `services/agenda_service.py::criar_agendamento` | `test_agenda_service.py::test_cria_*`, `test_agendamentos.py::test_criar_*` |
| RF09 | `agenda_service.horarios_disponiveis`, `controllers/api.py`, `static/js/agendamento.js` | `test_horarios_disponiveis_*`, `test_api_horarios*`, E2E `test_agendamento_com_horarios_livres` |
| RF10 | `agenda_service.reagendar` | `test_reagendar_*` |
| RF11 | `agenda_service.alterar_status` | `test_fluxo_completo_de_status`, `test_ciclo_de_status_pela_interface`, E2E `test_cancelamento_exige_motivo_*` |
| RF12 | `controllers/agendamentos.py::listar` | `test_listagem_com_filtros` |
| RF13 | `controllers/agendamentos.py::agenda` | `test_agenda_do_dia` |
| RF14 | `services/painel_service.py` | `test_painel_mostra_indicadores`, E2E `test_login_e_painel` |
| RF15 | `controllers/usuarios.py` | `test_admin_cria_usuario`, `test_admin_desativa_atendente_*` |
| RF16 | `controllers/feedback.py::enviar`, `services/feedback_service.py` | `test_envia_feedback_com_print`, `test_feedback_*`, E2E `test_formulario_de_feedback_*` |
| RF17 | `controllers/feedback.py` (admin) | `test_admin_trata_feedback_e_gera_relatorio` |
| RN01 | `agenda_service.validar_horario` | `test_rn01_*`, `test_agendamento_no_passado_e_recusado` |
| RN02 | idem | `test_rn02_*` (3 testes) |
| RN03 | idem + `ex_agendamento_conflito_profissional` | `test_rn03_*`, `test_conflito_*`, `test_postgres.py::test_exclusion_constraint_*` |
| RN04 | idem | `test_rn04_*` |
| RN05 | idem | `test_rn05_*`, E2E (serviço indisponível fica desabilitado) |
| RN06 | `agenda_service._carregar` | `test_rn06_*` |
| RN07 | `StatusAgendamento.TRANSICOES` | `test_rn07_*` |
| RN08 | `agenda_service.alterar_status` | `test_rn08_*` |
| RN09 | idem | `test_rn09_*` |
| RN10 | `Agendamento.valor` | `test_rn10_*`, `test_reagendar_trocando_servico_*` |
| RN11 | `cadastro_service.excluir_cliente` | `test_rn11_*` |
| RN12 | `cadastro_service.alternar_ativo` | `test_nao_inativa_profissional_*`, `test_inativar_profissional_*`, `test_d15_nao_desativa_servico_*` |
| RN13 | `cadastro_service.salvar_usuario` / `alternar_ativo_usuario` | `test_admin_nao_pode_*`, `test_sistema_mantem_*` |
| RN14 | `cadastro_service`, `uq_*` no banco | `test_cpf_duplicado_*`, `test_usuario_email_unico_*` |
| RNF02 | `extensions.csrf` | `test_formulario_sem_token_csrf_e_rejeitado` |
| RNF03 | `_helpers.admin_obrigatorio` | `test_atendente_nao_acessa_area_administrativa` (6 rotas) |
| RNF04 | `_helpers.url_segura`, lista fixa de filtros na paginação | `test_redireciona_para_next_seguro_*`, `test_alterar_status_nao_redireciona_*`, `test_cabecalhos_de_seguranca` |
| RNF05 | `feedback_service.preparar_anexos`; `celula_segura` na exportação CSV | `test_rejeita_*`, `test_upload_maior_que_o_limite_retorna_413`, `test_d09_csv_neutraliza_formulas` |
| RNF06 | `database/schema.sql` | `test_postgres.py` (9 testes) |
| RNF07 | `static/css/app.css` | E2E `test_menu_lateral_no_celular` |
| RNF08 | `forms/` (base `Formulario` com mensagens em português), `static/js/app.js` | `test_cadastro_de_cliente_mostra_erros_*`, `test_d11_*`, E2E `test_mascaras_e_validacao_*`, `test_feedback_bloqueia_*` |
| RNF09 | `app.js` (modal, bloqueio de envio duplicado) | E2E `test_cadastrar_cliente_e_excluir_com_modal_*`, `test_segundo_envio_do_formulario_e_bloqueado` |
| RNF11 | `controllers/erros.py` | `test_pagina_404_amigavel`, `test_405_amigavel`, `test_erro_500_*` |
