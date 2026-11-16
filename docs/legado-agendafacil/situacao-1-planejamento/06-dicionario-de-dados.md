# 6. Dicionário de dados

> Gerado automaticamente a partir do catálogo do PostgreSQL por
> `scripts/gerar_dicionario.py` (não edite à mão: altere o `database/schema.sql`,
> recrie o banco e rode o script de novo).

Legenda: **PK** chave primária · **FK** chave estrangeira · **UQ** valor único ·
**Nulo** = aceita ficar em branco.

## Domínios

| Domínio | Tipo base | Regra de validação |
|---|---|---|
| `dm_cpf` | character varying(11) | `CHECK (((VALUE)::text ~ '^[0-9]{11}$'::text))` |
| `dm_dinheiro` | numeric(10,2) | `CHECK ((VALUE >= (0)::numeric))` |
| `dm_email` | character varying(120) | `CHECK (((VALUE)::text ~* '^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$'::text))` |
| `dm_nome` | character varying(120) | `CHECK ((char_length(btrim((VALUE)::text)) >= 2))` |
| `dm_telefone` | character varying(11) | `CHECK (((VALUE)::text ~ '^[0-9]{10,11}$'::text))` |

## Tabela `agendamento`

Reserva de horário de um cliente com um profissional para um serviço.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador do agendamento. |
| `cliente_id` | integer | Não | — | FK → cliente.id | Cliente atendido. |
| `profissional_id` | integer | Não | — | FK → profissional.id | Profissional que realiza o atendimento. |
| `servico_id` | integer | Não | — | FK → servico.id | Serviço contratado. |
| `inicio` | timestamp(0) without time zone | Não | — | — | Data/hora de início (fuso America/Sao_Paulo). |
| `fim` | timestamp(0) without time zone | Não | — | — | Calculado pela aplicação: inicio + servico.duracao_min. |
| `status` | character varying(15) | Não | 'AGENDADO'::character varying | — | AGENDADO -> CONFIRMADO -> CONCLUIDO \| NAO_COMPARECEU; AGENDADO/CONFIRMADO -> CANCELADO. |
| `valor` | `dm_dinheiro` (numeric(10,2)) | Não | — | — | Preço praticado no momento do agendamento (histórico; não muda se a tabela de preços mudar). |
| `observacoes` | text | Sim | — | — | Observações do atendimento. |
| `motivo_cancelamento` | text | Sim | — | — | Obrigatório quando status = CANCELADO. |
| `criado_por_id` | integer | Sim | — | FK → usuario.id | Usuário que registrou o agendamento. |
| `criado_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora do registro. |
| `atualizado_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora da última alteração. |

**Restrições:**

- `ck_agendamento_motivo` (CHECK): `CHECK ((((status)::text <> 'CANCELADO'::text) OR (motivo_cancelamento IS NOT NULL)))`
- `ck_agendamento_periodo` (CHECK): `CHECK ((fim > inicio))`
- `ck_agendamento_status` (CHECK): `CHECK (((status)::text = ANY ((ARRAY['AGENDADO'::character varying, 'CONFIRMADO'::character varying, 'CONCLUIDO'::character varying, 'CANCELADO'::character varying, 'NAO_COMPARECEU'::character varying])::text[])))`
- `ck_agendamento_valor` (CHECK): `CHECK (((valor)::numeric >= (0)::numeric))`
- `fk_agendamento_cliente` (FOREIGN KEY): `FOREIGN KEY (cliente_id) REFERENCES cliente(id) ON DELETE RESTRICT`
- `fk_agendamento_profissional` (FOREIGN KEY): `FOREIGN KEY (profissional_id) REFERENCES profissional(id) ON DELETE RESTRICT`
- `fk_agendamento_servico` (FOREIGN KEY): `FOREIGN KEY (servico_id) REFERENCES servico(id) ON DELETE RESTRICT`
- `fk_agendamento_usuario` (FOREIGN KEY): `FOREIGN KEY (criado_por_id) REFERENCES usuario(id) ON DELETE SET NULL`
- `ex_agendamento_conflito_profissional` (EXCLUDE): `EXCLUDE USING gist (profissional_id WITH =, tsrange(inicio, fim, '[)'::text) WITH &&) WHERE (((status)::text = ANY ((ARRAY['AGENDADO'::character varying, 'CONFIRMADO'::character varying])::text[])))`

**Índices:**

- `ex_agendamento_conflito_profissional`: `CREATE INDEX ex_agendamento_conflito_profissional ON public.agendamento USING gist (profissional_id, tsrange(inicio, fim, '[)'::text)) WHERE ((status)::text = ANY ((ARRAY['AGENDADO'::character varying, 'CONFIRMADO'::character varying])::text[]))`
- `ix_agendamento_cliente`: `CREATE INDEX ix_agendamento_cliente ON public.agendamento USING btree (cliente_id)`
- `ix_agendamento_inicio`: `CREATE INDEX ix_agendamento_inicio ON public.agendamento USING btree (inicio)`
- `ix_agendamento_profissional_inicio`: `CREATE INDEX ix_agendamento_profissional_inicio ON public.agendamento USING btree (profissional_id, inicio)`

## Tabela `cliente`

Clientes atendidos pelo estabelecimento.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador do cliente. |
| `nome` | `dm_nome` (character varying(120)) | Não | — | — | Nome completo. |
| `telefone` | `dm_telefone` (character varying(11)) | Não | — | — | Somente dígitos, com DDD (10 ou 11 dígitos). |
| `email` | `dm_email` (character varying(120)) | Sim | — | — | E-mail para contato (opcional). |
| `cpf` | `dm_cpf` (character varying(11)) | Sim | — | UQ | Opcional; somente dígitos; único quando informado. |
| `data_nascimento` | date | Sim | — | — | Data de nascimento (opcional). |
| `observacoes` | text | Sim | — | — | Preferências, alergias e restrições do cliente. |
| `criado_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora de cadastro. |

**Restrições:**

- `ck_cliente_nascimento` (CHECK): `CHECK (((data_nascimento IS NULL) OR (data_nascimento > '1900-01-01'::date)))`

**Índices:**

- `ix_cliente_nome`: `CREATE INDEX ix_cliente_nome ON public.cliente USING btree (lower((nome)::text))`

## Tabela `feedback_anexo`

Prints de tela enviados com o feedback (armazenados em bytea).

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador do print. |
| `feedback_id` | integer | Não | — | FK → feedback_teste.id | Laudo ao qual o print pertence. |
| `nome_arquivo` | character varying(255) | Não | — | — | Nome do arquivo enviado (sanitizado). |
| `tipo_mime` | character varying(50) | Não | — | — | Tipo detectado pela assinatura do arquivo. |
| `tamanho_bytes` | integer | Não | — | — | Tamanho em bytes (máx. 2 MB). |
| `conteudo` | bytea | Não | — | — | Conteúdo binário da imagem. |

**Restrições:**

- `ck_anexo_tamanho` (CHECK): `CHECK (((tamanho_bytes >= 1) AND (tamanho_bytes <= 2097152)))`
- `ck_anexo_tipo` (CHECK): `CHECK (((tipo_mime)::text = ANY ((ARRAY['image/png'::character varying, 'image/jpeg'::character varying, 'image/webp'::character varying, 'image/gif'::character varying])::text[])))`
- `fk_anexo_feedback` (FOREIGN KEY): `FOREIGN KEY (feedback_id) REFERENCES feedback_teste(id) ON DELETE CASCADE`

**Índices:**

- `ix_feedback_anexo_feedback_id`: `CREATE INDEX ix_feedback_anexo_feedback_id ON public.feedback_anexo USING btree (feedback_id)`

## Tabela `feedback_teste`

Laudos dos testadores (validação com usuários — Situação-Problema 3).

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador do laudo. |
| `nome_testador` | `dm_nome` (character varying(120)) | Não | — | — | Nome de quem testou. |
| `email` | `dm_email` (character varying(120)) | Sim | — | — | Contato do testador (opcional). |
| `perfil_testador` | character varying(80) | Sim | — | — | Colega de curso, profissional de TI etc. |
| `data_teste` | date | Não | — | — | Data em que o teste foi feito. |
| `funcionou` | text | Não | — | — | O que foi testado e funcionou. |
| `nao_funcionou` | text | Sim | — | — | O que foi testado e não funcionou / o que deve ser corrigido. |
| `nao_testado` | text | Sim | — | — | Funcionalidades não testadas e o motivo. |
| `sugestoes` | text | Sim | — | — | Sugestões de melhoria. |
| `nota` | smallint | Não | — | — | Nota geral de 1 a 5. |
| `navegador` | character varying(255) | Sim | — | — | User-Agent do navegador usado no teste. |
| `status` | character varying(12) | Não | 'NOVO'::character varying | — | NOVO, EM_ANALISE, CORRIGIDO ou DESCARTADO. |
| `tratativa` | text | Sim | — | — | O que foi feito com o feedback (correção, justificativa). |
| `criado_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora de envio. |

**Restrições:**

- `ck_feedback_nota` (CHECK): `CHECK (((nota >= 1) AND (nota <= 5)))`
- `ck_feedback_status` (CHECK): `CHECK (((status)::text = ANY ((ARRAY['NOVO'::character varying, 'EM_ANALISE'::character varying, 'CORRIGIDO'::character varying, 'DESCARTADO'::character varying])::text[])))`

## Tabela `profissional`

Profissionais que executam os serviços.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador do profissional. |
| `nome` | `dm_nome` (character varying(120)) | Não | — | — | Nome completo. |
| `especialidade` | character varying(80) | Sim | — | — | Ex.: cabeleireira, barbeiro. |
| `telefone` | `dm_telefone` (character varying(11)) | Sim | — | — | Somente dígitos, com DDD (opcional). |
| `email` | `dm_email` (character varying(120)) | Sim | — | — | E-mail para contato (opcional). |
| `ativo` | boolean | Não | true | — | Exclusão lógica: inativo não recebe novos agendamentos. |
| `criado_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora de cadastro. |

## Tabela `profissional_servico`

Quais serviços cada profissional está habilitado a realizar (N:N).

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `profissional_id` | integer | Não | — | PK, FK → profissional.id | Profissional habilitado. |
| `servico_id` | integer | Não | — | PK, FK → servico.id | Serviço que ele realiza. |

**Restrições:**

- `fk_ps_profissional` (FOREIGN KEY): `FOREIGN KEY (profissional_id) REFERENCES profissional(id) ON DELETE CASCADE`
- `fk_ps_servico` (FOREIGN KEY): `FOREIGN KEY (servico_id) REFERENCES servico(id) ON DELETE CASCADE`

## Tabela `servico`

Catálogo de serviços com duração e preço de tabela.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador do serviço. |
| `nome` | character varying(80) | Não | — | UQ | Nome do serviço (único). |
| `descricao` | text | Sim | — | — | Descrição exibida na lista de serviços. |
| `duracao_min` | integer | Não | — | — | Duração em minutos (5 a 480); define o fim do agendamento. |
| `preco` | `dm_dinheiro` (numeric(10,2)) | Não | — | — | Preço de tabela atual, em reais. |
| `ativo` | boolean | Não | true | — | Serviço inativo não aparece para novos agendamentos. |
| `criado_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora de cadastro. |

**Restrições:**

- `ck_servico_duracao` (CHECK): `CHECK (((duracao_min >= 5) AND (duracao_min <= 480)))`
- `ck_servico_preco` (CHECK): `CHECK (((preco)::numeric >= (0)::numeric))`

## Tabela `usuario`

Pessoas que operam o sistema (administradores e atendentes).

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador do usuário. |
| `nome` | `dm_nome` (character varying(120)) | Não | — | — | Nome completo. |
| `email` | `dm_email` (character varying(120)) | Não | — | UQ | E-mail de login (minúsculas, único). |
| `senha_hash` | character varying(255) | Não | — | — | Hash PBKDF2/scrypt gerado pelo Werkzeug; a senha nunca é gravada em texto puro. |
| `perfil` | character varying(10) | Não | 'ATENDENTE'::character varying | — | ADMIN: acesso total; ATENDENTE: clientes e agenda. |
| `ativo` | boolean | Não | true | — | Exclusão lógica: usuário inativo não consegue fazer login. |
| `criado_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora de cadastro. |

**Restrições:**

- `ck_usuario_perfil` (CHECK): `CHECK (((perfil)::text = ANY ((ARRAY['ADMIN'::character varying, 'ATENDENTE'::character varying])::text[])))`
