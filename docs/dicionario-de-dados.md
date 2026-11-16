# Dicionário de dados — InvestSim

> Gerado automaticamente a partir do catálogo do PostgreSQL por
> `scripts/gerar_dicionario.py` (não edite à mão: altere o `database/schema.sql`,
> recrie o banco e rode o script de novo).

Legenda: **PK** chave primária · **FK** chave estrangeira · **UQ** valor único ·
**Nulo** = aceita ficar em branco.

## Domínios

| Domínio | Tipo base | Regra de validação |
|---|---|---|
| `dm_email` | character varying(120) | `CHECK (((VALUE)::text ~* '^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$'::text))` |
| `dm_nome` | character varying(120) | `CHECK ((char_length(btrim((VALUE)::text)) >= 2))` |
| `dm_preco` | numeric(20,8) | `CHECK ((VALUE > (0)::numeric))` |
| `dm_quantidade` | numeric(24,8) | `CHECK ((VALUE > (0)::numeric))` |
| `dm_ticker` | character varying(20) | `CHECK (((VALUE)::text ~ '^[A-Z0-9]{2,12}$'::text))` |

## Tabela `ativo`

Catálogo de ativos que podem ser simulados.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador do ativo. |
| `ticker` | `dm_ticker` (character varying(20)) | Não | — | UQ | Código de negociação exibido ao usuário (PETR4, KNRI11, BTC). |
| `nome` | character varying(120) | Não | — | — | Nome do ativo. |
| `classe` | character varying(10) | Não | — | — | ACAO, FII, ETF ou CRIPTO; define regras (cripto aceita frações). |
| `simbolo_fonte` | character varying(30) | Não | — | — | Código do ativo na fonte de dados (brapi). |
| `ativo` | boolean | Não | true | — | Ativo oculto não aparece para novas operações; carteiras existentes não mudam. |
| `criado_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora de cadastro. |

**Restrições:**

- `ck_ativo_classe` (CHECK): `CHECK (((classe)::text = ANY ((ARRAY['ACAO'::character varying, 'FII'::character varying, 'ETF'::character varying, 'CRIPTO'::character varying])::text[])))`

## Tabela `carteira`

Carteira simulada de um usuário.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador da carteira. |
| `usuario_id` | integer | Não | — | UQ, FK → usuario.id | Dono da carteira (só ele a enxerga). |
| `nome` | character varying(80) | Não | — | UQ | Nome da carteira (único por usuário). |
| `descricao` | text | Sim | — | — | Objetivo da carteira. |
| `criada_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora de criação. |

**Restrições:**

- `fk_carteira_usuario` (FOREIGN KEY): `FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE`

**Índices:**

- `ix_carteira_usuario_id`: `CREATE INDEX ix_carteira_usuario_id ON public.carteira USING btree (usuario_id)`

## Tabela `cotacao`

Cache de fechamentos diários (BRL) baixados da fonte de dados.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `ativo_id` | integer | Não | — | PK, FK → ativo.id | Ativo cotado. |
| `data` | date | Não | — | PK | Data do pregão. |
| `fechamento` | `dm_preco` (numeric(20,8)) | Não | — | — | Preço de fechamento em reais. |

**Restrições:**

- `fk_cotacao_ativo` (FOREIGN KEY): `FOREIGN KEY (ativo_id) REFERENCES ativo(id) ON DELETE CASCADE`

## Tabela `feedback_anexo`

Prints de tela enviados com o laudo.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador do print. |
| `feedback_id` | integer | Não | — | FK → feedback_teste.id | Laudo ao qual o print pertence. |
| `nome_arquivo` | character varying(255) | Não | — | — | Nome do arquivo (sanitizado). |
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

Laudos dos testadores (validação com usuários).

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador do laudo. |
| `nome_testador` | `dm_nome` (character varying(120)) | Não | — | — | Nome de quem testou. |
| `email` | `dm_email` (character varying(120)) | Sim | — | — | Contato do testador (opcional). |
| `perfil_testador` | character varying(80) | Sim | — | — | Colega de curso, profissional de TI etc. |
| `data_teste` | date | Não | — | — | Data do teste. |
| `funcionou` | text | Não | — | — | O que foi testado e funcionou. |
| `nao_funcionou` | text | Sim | — | — | O que não funcionou e o que deve ser corrigido. |
| `nao_testado` | text | Sim | — | — | Funcionalidades não testadas e o motivo. |
| `sugestoes` | text | Sim | — | — | Sugestões de melhoria. |
| `nota` | smallint | Não | — | — | Nota geral de 1 a 5. |
| `navegador` | character varying(255) | Sim | — | — | User-Agent do navegador usado no teste. |
| `status` | character varying(12) | Não | 'NOVO'::character varying | — | NOVO, EM_ANALISE, CORRIGIDO ou DESCARTADO. |
| `tratativa` | text | Sim | — | — | O que foi feito com o feedback. |
| `criado_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora de envio. |

**Restrições:**

- `ck_feedback_nota` (CHECK): `CHECK (((nota >= 1) AND (nota <= 5)))`
- `ck_feedback_status` (CHECK): `CHECK (((status)::text = ANY ((ARRAY['NOVO'::character varying, 'EM_ANALISE'::character varying, 'CORRIGIDO'::character varying, 'DESCARTADO'::character varying])::text[])))`

## Tabela `operacao`

Compra ou venda simulada, pelo preço de fechamento da data.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador da operação. |
| `carteira_id` | integer | Não | — | FK → carteira.id | Carteira da operação. |
| `ativo_id` | integer | Não | — | FK → ativo.id | Ativo negociado. |
| `tipo` | character varying(6) | Não | — | — | COMPRA (aporte) ou VENDA (resgate). |
| `data` | date | Não | — | — | Data da operação (não pode estar no futuro). |
| `quantidade` | `dm_quantidade` (numeric(24,8)) | Não | — | — | Quantidade negociada; inteira para ações, FIIs e ETFs. |
| `preco` | `dm_preco` (numeric(20,8)) | Não | — | — | Preço unitário: fechamento do dia (ou informado manualmente). |
| `taxas` | numeric(14,2) | Não | 0 | — | Corretagem e emolumentos, em reais. |
| `observacao` | text | Sim | — | — | Anotação livre do usuário. |
| `criado_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora do registro. |

**Restrições:**

- `ck_operacao_data` (CHECK): `CHECK ((data >= '1990-01-01'::date))`
- `ck_operacao_preco` (CHECK): `CHECK (((preco)::numeric > (0)::numeric))`
- `ck_operacao_quantidade` (CHECK): `CHECK (((quantidade)::numeric > (0)::numeric))`
- `ck_operacao_taxas` (CHECK): `CHECK ((taxas >= (0)::numeric))`
- `ck_operacao_tipo` (CHECK): `CHECK (((tipo)::text = ANY ((ARRAY['COMPRA'::character varying, 'VENDA'::character varying])::text[])))`
- `fk_operacao_ativo` (FOREIGN KEY): `FOREIGN KEY (ativo_id) REFERENCES ativo(id) ON DELETE RESTRICT`
- `fk_operacao_carteira` (FOREIGN KEY): `FOREIGN KEY (carteira_id) REFERENCES carteira(id) ON DELETE CASCADE`

**Índices:**

- `ix_operacao_ativo_id`: `CREATE INDEX ix_operacao_ativo_id ON public.operacao USING btree (ativo_id)`
- `ix_operacao_carteira_data`: `CREATE INDEX ix_operacao_carteira_data ON public.operacao USING btree (carteira_id, data)`
- `ix_operacao_carteira_id`: `CREATE INDEX ix_operacao_carteira_id ON public.operacao USING btree (carteira_id)`

## Tabela `provento`

Cache de proventos (dividendos/JCP/rendimentos) por cota, na data ex.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `ativo_id` | integer | Não | — | PK, FK → ativo.id | Ativo que pagou o provento. |
| `data` | date | Não | — | PK | Data ex: quem tinha o ativo no pregão anterior recebe. |
| `valor` | `dm_preco` (numeric(20,8)) | Não | — | — | Valor por cota/ação em reais. |

**Restrições:**

- `fk_provento_ativo` (FOREIGN KEY): `FOREIGN KEY (ativo_id) REFERENCES ativo(id) ON DELETE CASCADE`

## Tabela `sincronizacao`

Controle do cache: período baixado e momento da última atualização.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `chave` | character varying(60) | Não | — | PK | cot:<id do ativo> ou cdi. |
| `desde` | date | Não | — | — | Início do período já baixado. |
| `ate` | date | Não | — | — | Fim do período já baixado. |
| `atualizado_em` | timestamp without time zone | Não | — | — | Momento da última atualização. |
| `fonte` | character varying(20) | Não | — | — | brapi ou demo (trocar a fonte invalida o cache). |

**Restrições:**

- `ck_sincronizacao_periodo` (CHECK): `CHECK ((ate >= desde))`

## Tabela `taxa_cdi`

CDI diário (série 12 do SGS/Banco Central).

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `data` | date | Não | — | PK | Dia útil. |
| `taxa_dia` | numeric(12,8) | Não | — | — | Taxa do dia em percentual (ex.: 0,050788 = 0,050788 pct no dia). |

**Restrições:**

- `ck_taxa_cdi_faixa` (CHECK): `CHECK (((taxa_dia >= (0)::numeric) AND (taxa_dia < (1)::numeric)))`

## Tabela `usuario`

Pessoas que usam o simulador (investidores) ou o administram.

| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |
|---|---|---|---|---|---|
| `id` | integer | Não | identity | PK | Identificador do usuário. |
| `nome` | `dm_nome` (character varying(120)) | Não | — | — | Nome completo. |
| `email` | `dm_email` (character varying(120)) | Não | — | UQ | E-mail de login (minúsculas, único). |
| `senha_hash` | character varying(255) | Não | — | — | Hash da senha (Werkzeug); a senha nunca é gravada em texto puro. |
| `perfil` | character varying(10) | Não | 'INVESTIDOR'::character varying | — | INVESTIDOR: as próprias carteiras; ADMIN: também catálogo, usuários e feedbacks. |
| `ativo` | boolean | Não | true | — | Exclusão lógica: usuário inativo não consegue fazer login. |
| `criado_em` | timestamp(0) without time zone | Não | LOCALTIMESTAMP(0) | — | Data/hora de cadastro. |

**Restrições:**

- `ck_usuario_perfil` (CHECK): `CHECK (((perfil)::text = ANY ((ARRAY['ADMIN'::character varying, 'INVESTIDOR'::character varying])::text[])))`
