# 4. Roteiro do vídeo de demonstração (≈ 5 minutos)

> O enunciado pede um vídeo **narrado por você**, com **pelo menos cinco minutos**, mostrando a
> solução funcionando. Abaixo há um roteiro com tempos; adapte a fala ao seu jeito.
>
> **Dica de gravação:** OBS Studio (gratuito) ou a Barra de Jogo do Windows (`Win + Alt + R`).
> Antes de gravar, rode `flask init-db --recriar` e `flask seed` para ter dados limpos. Deixe o
> navegador em tela cheia, com zoom de 110–125%.

| Tempo | Tela | O que mostrar / falar |
|---|---|---|
| 0:00–0:30 | Slide ou README | Apresente-se. "O AgendaFácil resolve o problema de horários duplicados e sem controle em pequenos negócios de serviços." Stack: Python/Flask (MVC), PostgreSQL, HTML/CSS/JS, pytest. |
| 0:30–1:00 | Login | Tente entrar sem preencher (validação em português). Entre como **atendente**. |
| 1:00–1:30 | Painel | Explique os indicadores. Abra a **Agenda do dia** e troque de dia. |
| 1:30–2:15 | Clientes | Busque um cliente. Cadastre um novo digitando o telefone (máscara) e um CPF inválido (erro). Corrija e use **Salvar e agendar**. |
| 2:15–3:15 | Novo agendamento | Escolha o profissional → mostre que a lista de serviços é filtrada. Escolha a data → horários livres. Clique em um horário → resumo atualizado. Confirme. |
| 3:15–3:45 | Regra de conflito | Tente marcar o **mesmo profissional no mesmo horário**: mostre a mensagem no campo. Explique que o PostgreSQL também barra (restrição de exclusão). |
| 3:45–4:15 | Detalhe | Confirme a presença. Tente cancelar sem motivo (erro) e depois com motivo. Mostre que o horário voltou a ficar livre. |
| 4:15–4:45 | Administrador | Saia e entre como **admin**: serviços, profissionais (desativar com confirmação), usuários. Mostre que o atendente não acessa essas telas (403). |
| 4:45–5:15 | Celular | Abra no celular (ou DevTools `F12` → modo dispositivo): menu ☰ e tabelas em cartões. |
| 5:15–5:45 | Testes | No terminal: `pytest -q` mostrando os testes passando. Mostre rapidamente a estrutura MVC no VS Code e o repositório no GitHub. |
| 5:45–6:00 | Encerramento | Link do repositório e do sistema publicado. |

## Segundo vídeo (Situação-Problema 3) — até 5 minutos

Depois de receber os 5 laudos e fazer as correções:

| Tempo | Conteúdo |
|---|---|
| 0:00–0:30 | Quem testou (5 pessoas) e como: formulário de laudo dentro do sistema |
| 0:30–1:30 | Tela **Feedbacks de teste**: notas, problemas relatados, prints |
| 1:30–4:00 | Para cada correção: mostre o problema relatado (print), a mudança no código (commit no GitHub) e o sistema já corrigido |
| 4:00–4:30 | O que **não** foi corrigido e por quê (seja transparente) |
| 4:30–5:00 | `pytest` passando após as correções; o que você aprendeu |
