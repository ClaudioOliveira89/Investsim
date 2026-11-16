# 2. Manual de uso — AgendaFácil

Este manual é para quem vai **usar** o sistema no dia a dia (recepção e gerência).

## Acesso

Abra o endereço do sistema no navegador (computador ou celular) e entre com seu e-mail e senha.

| Perfil | O que pode fazer |
|---|---|
| **Atendente** | Clientes, agendamentos, agenda do dia, painel |
| **Administrador** | Tudo o que o atendente faz, mais serviços, profissionais, usuários e feedbacks de teste |

**Usuários de demonstração** (criados por `flask seed`):

| E-mail | Senha | Perfil |
|---|---|---|
| `admin@agendafacil.com` | `Agenda@2026` | Administrador |
| `atendente@agendafacil.com` | `Agenda@2026` | Atendente |

> Em produção, troque essas senhas em **seu nome (canto superior direito) → Alterar minha senha**.

![Login](telas/01-login.png)

## Painel

A primeira tela mostra os atendimentos de hoje, quantos aguardam confirmação, quantos estão
marcados nos próximos 7 dias e o faturamento do mês (atendimentos concluídos). Clique nos
links dos cartões para ir direto à lista correspondente.

![Painel](telas/03-painel.png)

## Clientes

- **Buscar:** digite parte do nome, telefone, e-mail ou CPF e clique em **Buscar**.
- **Cadastrar:** **Novo cliente** → preencha → **Salvar cliente**. Use **Salvar e agendar** para
  ir direto ao agendamento com o cliente já escolhido.
- Telefone e CPF são formatados automaticamente enquanto você digita. Só nome e telefone são
  obrigatórios.
- Clique no nome do cliente para ver os dados e o **histórico de atendimentos**.
- Um cliente só pode ser **excluído** se não tiver nenhum atendimento no histórico.

![Validação](telas/10-cliente-validacao.png)

## Agendar um atendimento

1. Clique em **Novo agendamento** (no painel, na lista ou no cliente).
2. **Etapa 1** — escolha o cliente.
3. **Etapa 2** — escolha o profissional. A lista de serviços passa a mostrar só o que ele faz.
4. **Etapa 3** — escolha a data. Aparecem os **horários livres**: clique em um deles.
5. Confira o **Resumo** à direita (serviço, duração, horário de término e valor) e clique em
   **Confirmar agendamento**.

![Novo agendamento](telas/06-novo-agendamento.png)

Se o horário não puder ser usado (já ocupado, fora do expediente ou no passado), o sistema
avisa no próprio campo e nada é gravado:

![Conflito](telas/07-agendamento-conflito.png)

## Acompanhar o atendimento

Abra o agendamento (pela agenda, pela lista ou pelo histórico do cliente):

| Botão | Quando usar |
|---|---|
| **Confirmar presença** | O cliente confirmou que vem |
| **Marcar como concluído** | O atendimento foi realizado (disponível após o horário de início) |
| **Registrar falta** | O cliente não veio (disponível após o horário de início) |
| **Cancelar este agendamento…** | O cliente desmarcou. Informe o motivo. O horário volta a ficar livre |
| **Reagendar / editar** | Trocar profissional, serviço, data ou horário |

Atendimentos concluídos, cancelados ou com falta registrada não podem mais ser alterados:
eles fazem parte do histórico.

![Detalhe](telas/08-agendamento-detalhe.png)

## Agenda do dia e lista de agendamentos

- **Agenda do dia** mostra uma coluna por profissional. Use as setas, o calendário ou **Hoje**
  para trocar de dia. **Agendar com…** já abre o formulário com o profissional e a data.
- **Agendamentos** lista tudo a partir de hoje. Filtre por período, profissional e status.
  **Ver todos** remove o filtro de data.

![Agenda do dia](telas/04-agenda-do-dia.png)

## Área do administrador

- **Serviços:** cadastre nome, duração (define o fim do atendimento) e preço. Mudar o preço
  **não** altera agendamentos já feitos. Serviços podem ser desativados e reativados.
- **Profissionais:** cadastre e marque os serviços que cada um realiza. Não é possível
  desativar quem tem agendamentos futuros.
- **Usuários:** crie contas de atendente ou administrador, redefina senhas e desative acessos.
- **Feedbacks de teste:** veja os laudos dos testadores, registre a tratativa, exporte CSV ou
  gere o **Relatório para PDF** (botão "Imprimir / Salvar em PDF").

## No celular

O sistema se adapta à tela: o menu fica no botão ☰ do canto superior esquerdo e as tabelas
viram cartões.

<img src="telas/18-celular-painel.png" width="260" alt="Painel no celular"> <img src="telas/20-celular-menu.png" width="260" alt="Menu no celular">

## Encontrou um problema?

Clique em **Relatar problema** (no rodapé do menu) para preencher o laudo, com prints da tela.

## Perguntas frequentes

**O horário que eu quero não aparece na lista.** Ele já está ocupado, está fora do expediente
ou o serviço não cabe até o fechamento (ex.: serviço de 2 h não pode começar às 19:00 se o
salão fecha às 20:00).

**Errei o horário de um agendamento.** Use **Reagendar / editar**. Se já foi concluído ou
cancelado, crie um novo.

**Por que não consigo excluir um cliente?** Ele tem histórico de atendimentos, que é preservado
por segurança. Você pode editar os dados dele normalmente.
