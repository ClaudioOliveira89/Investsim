# 1. Revisão do projeto (ciclo de melhoria contínua — Kaizen)

> **Situação-Problema 1** — "Verifique e adeque seu escopo/ideia e a prepare para a execução."

## 1.1 O problema

Pequenos negócios de serviços (salões, barbearias, estúdios de estética, clínicas pequenas)
costumam controlar horários em caderno, planilha ou conversas de WhatsApp. Isso causa:

- **horários duplicados**: dois clientes marcados com o mesmo profissional no mesmo horário;
- **faltas sem registro**: não há histórico de quem faltou ou cancelou;
- **dificuldade para achar um horário livre**: a atendente precisa conferir tudo manualmente;
- **falta de histórico do cliente**: não se sabe o que ele já fez nem quanto pagou;
- **nenhum indicador**: o dono não sabe quanto faturou no mês.

## 1.2 A solução: AgendaFácil

Sistema web responsivo (funciona no computador e no celular) para a recepção do negócio
cadastrar clientes, serviços e profissionais e **agendar atendimentos sem conflito de horário**,
acompanhando cada atendimento do agendamento até a conclusão.

| Item | Definição |
|---|---|
| Usuários | **Administrador** (dono/gerente) e **Atendente** (recepção) |
| Plataforma | Aplicação web responsiva |
| Back-end | Python 3 + Flask, padrão **MVC** |
| Banco de dados | **PostgreSQL** (SGBD popular, livre e de fácil manutenção) |
| Front-end | HTML5, CSS3 e JavaScript (sem frameworks), codificação tradicional |
| Testes | pytest (unitários e integração) + Playwright (E2E no navegador) |

## 1.3 Escopo

**Dentro do escopo (implementado):**

1. Login com perfis de acesso (administrador e atendente).
2. Cadastro de clientes com busca, paginação e histórico de atendimentos.
3. Cadastro de serviços (duração e preço) e de profissionais (com os serviços que realizam).
4. Agendamento com **cálculo automático dos horários livres** e bloqueio de conflitos.
5. Ciclo de vida do atendimento: agendado → confirmado → concluído / não compareceu / cancelado.
6. Agenda do dia por profissional e lista de agendamentos com filtros.
7. Painel com indicadores (atendimentos do dia, pendentes de confirmação, faturamento do mês).
8. Gestão de usuários (somente administrador).
9. **Formulário de laudo de teste** para a validação com usuários (Situação-Problema 3), com envio de prints.

**Fora do escopo (evoluções futuras):** agendamento feito pelo próprio cliente, envio automático
de lembretes por WhatsApp/e-mail, pagamentos on-line, múltiplas unidades, bloqueio de agenda
(férias e folgas) por profissional.

## 1.4 O que mudou em relação ao planejamento do PIT I

> ✏️ **Para você completar:** cole aqui o link ou anexe os documentos originais do PIT I
> (escopo, diagramas e protótipo) em `docs/situacao-1-planejamento/pit-1-original/`,
> para que o(a) tutor(a) possa comparar o "antes" e o "depois".

As melhorias aplicadas nesta revisão (o "depois") estão abaixo. Cada uma tem a sua motivação:

| # | Melhoria | Motivo (por que mudou) |
|---|---|---|
| M1 | Requisitos reescritos com identificadores (RF, RNF, RN) e **matriz de rastreabilidade** ligando requisito → código → teste | Atender à validação de requisitos: cada requisito precisa ter "apenas um significado exato" e "vincular facilmente códigos e testes" |
| M2 | Regras de negócio da agenda formalizadas (RN01–RN11) | As regras estavam implícitas; sem elas não há como testar de forma objetiva |
| M3 | Diagrama de estados do agendamento | O ciclo de vida (confirmar, concluir, faltar, cancelar) não estava modelado |
| M4 | Diagrama de classes separado em **domínio** e **persistência**, mais o mapeamento classe → tabela | Exigência da Situação 1: projetos de dados a partir do diagrama de classes de persistência |
| M5 | Uso de **domínios** do PostgreSQL (e-mail, telefone, CPF, dinheiro) e de uma *exclusion constraint* contra sobreposição de horários | "Um domínio é muito mais do que um tipo de dados": a regra de dados passa a valer dentro do próprio banco |
| M6 | O valor do serviço passa a ser gravado no agendamento | Sem isso, mudar o preço de tabela alteraria o histórico financeiro |
| M7 | Exclusão lógica (ativar/desativar) para profissionais, serviços e usuários; clientes com histórico não podem ser excluídos | Interface "recuperável/reversível" e preservação do histórico |
| M8 | Protótipo transformado em telas reais, com catálogo de mensagens de erro | Situação 1 pede revisar telas e mensagens de erro |
| M9 | Formulário de laudo de teste dentro do próprio sistema | Facilitar a coleta dos 5 testes (Situação 3) com prints anexados |

## 1.5 Crítica dos colegas sobre o planejamento

O enunciado pede para "pedir aos colegas a crítica para a solução que você deve implementar".
Registre aqui as sugestões recebidas **antes** do desenvolvimento e o que foi decidido:

| Colega | Sugestão | Decisão | Onde foi aplicada |
|---|---|---|---|
| ✏️ _nome_ | ✏️ | Aceita / Recusada (motivo) | ✏️ |
| ✏️ _nome_ | ✏️ | | |

## 1.6 Riscos e mitigação

| Risco | Impacto | Mitigação adotada |
|---|---|---|
| Dois atendentes marcarem o mesmo horário ao mesmo tempo | Alto | Validação na aplicação **e** restrição de exclusão no PostgreSQL (dupla proteção) |
| Perda de dados ao excluir registros | Alto | Exclusão lógica + `ON DELETE RESTRICT` nas chaves estrangeiras de agendamento |
| Acesso indevido à área administrativa | Médio | Perfis de acesso verificados no servidor (HTTP 403) |
| Senhas vazadas | Alto | Hash com sal (Werkzeug), nunca texto puro; mensagem de login genérica |
| Hospedagem gratuita com disco temporário | Médio | Prints do feedback guardados no banco (bytea), não em disco |
