# 5. Registro de mudanças

> "Coletar as sugestões dadas, realizar correções e melhorias sugeridas (quando pertinente) e
> incorporá-las na documentação do projeto."

Formato: cada versão lista o que mudou e **por quê** (origem: verificação interna, laudo de
testador ou decisão de projeto).

## [1.1.0] — ✏️ data — após a validação com usuários

> Preencha depois de tratar os laudos. Exemplo de linha:
> `- Corrigido: telefone fixo era recusado no cadastro de profissional (laudo #3, commit abc123).`

### Corrigido
- ✏️

### Melhorado
- ✏️

### Não alterado (justificativa)
- ✏️

## [1.0.0] — 15/11/2026 — versão entregue para teste

### Adicionado
- Autenticação com perfis administrador/atendente; alteração de senha.
- Cadastros de clientes (busca, paginação, histórico), serviços, profissionais e usuários.
- Agendamento com horários livres calculados, filtro de serviços por profissional e resumo com valor.
- Ciclo de status (agendado, confirmado, concluído, não compareceu, cancelado com motivo) e reagendamento.
- Agenda do dia por profissional, lista com filtros e painel de indicadores.
- Formulário público de laudo de teste com prints, tratativa, relatório para PDF e exportação CSV.
- Banco PostgreSQL com domínios, CHECKs, restrição de exclusão, índices, visões e comentários.
- 172 testes automatizados (95% de cobertura) e integração contínua no GitHub Actions.

### Corrigido durante a verificação interna
- D01 — E-mail com espaço no final era recusado no login.
- D02 — Redirecionamento aberto no parâmetro `voltar_para` (segurança).
- D03 — Botão de menu ☰ visível no desktop.
- D04 — Fundo do menu lateral cortado em páginas longas.
- D05 — Teste E2E dependente do fuso horário da máquina.
- D06 — Conexões com o banco não encerradas nos testes.
- D07 — Página 2 da lista padrão de agendamentos mostrava atendimentos passados.
- D08 — Parâmetros arbitrários da URL repassados aos links de paginação (`?endpoint=x` gerava erro 500).
- D09 — Injeção de fórmulas na exportação CSV (*CSV injection*).
- D10 — Editar um profissional apagava o vínculo com serviços inativos.
- D11 — Erro 500 no PostgreSQL com e-mail de mais de 120 caracteres no laudo ou data de nascimento anterior a 1900.
- D12 — Datas extremas na URL (`?data=9999-12-31`) derrubavam a agenda e a lista (erro 500).
- D13 — A verificação das imagens no navegador não bloqueava o envio.
- D14 — Duplo clique em "Salvar" e "Salvar e agendar" podia enviar o formulário duas vezes.
- D15 — Era possível desativar um serviço com agendamentos futuros.
- D16 — Sem banco configurado, só aparecia "Erro interno"; `.env` ignorado ao iniciar por `python wsgi.py`.
