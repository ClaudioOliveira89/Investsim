# Documentação do projeto — AgendaFácil

Organizada em uma pasta por situação-problema, como pede o enunciado ("criando estruturas de
diretório no GIT para todas as situações de desafio além, é claro, da codificação").

## Situação-Problema 1 — Atualizar o plano de projeto

| Documento | Conteúdo |
|---|---|
| [01 · Revisão do projeto](situacao-1-planejamento/01-revisao-do-projeto.md) | Problema, escopo, o que mudou desde o PIT I (Kaizen), crítica dos colegas, riscos |
| [02 · Requisitos](situacao-1-planejamento/02-requisitos.md) | RF, RN, RNF e matriz de rastreabilidade requisito → código → teste |
| [03 · Modelagem UML](situacao-1-planejamento/03-modelagem-uml.md) | Casos de uso, classes, sequência, atividades, estados, implantação |
| [04 · IHC e protótipo](situacao-1-planejamento/04-ihc-prototipo.md) | Princípios de IHC, mapa de navegação, mapa conceitual, telas e catálogo de mensagens |
| [05 · Banco de dados](situacao-1-planejamento/05-banco-de-dados.md) | Projeto conceitual, lógico normalizado e físico |
| [06 · Dicionário de dados](situacao-1-planejamento/06-dicionario-de-dados.md) | Gerado do catálogo do PostgreSQL |
| [`database/schema.sql`](../database/schema.sql) | Script do projeto físico |

## Situação-Problema 2 — Desenvolver a solução

| Documento | Conteúdo |
|---|---|
| [01 · Arquitetura MVC](situacao-2-desenvolvimento/01-arquitetura-mvc.md) | Camadas, fluxo da requisição, bibliotecas, decisões |
| [02 · Manual de uso](situacao-2-desenvolvimento/02-manual-de-uso.md) | Guia do usuário com telas |
| [03 · Instalação e implantação](situacao-2-desenvolvimento/03-instalacao-e-implantacao.md) | Rodar local, testes, publicar no Render |
| [04 · Roteiro dos vídeos](situacao-2-desenvolvimento/04-roteiro-do-video.md) | Vídeo de demonstração e vídeo das mudanças |
| [telas/](situacao-2-desenvolvimento/telas/) | 20 capturas de tela (desktop e celular) |
| Código | [`app/`](../app) · [`tests/`](../tests) |

## Situação-Problema 3 — Testes, validação e correções

| Documento | Conteúdo |
|---|---|
| [01 · Plano de testes](situacao-3-testes-validacao/01-plano-de-testes.md) | Modelo V, níveis, técnicas, critérios |
| [02 · Relatório de testes](situacao-3-testes-validacao/02-relatorio-de-testes.md) | Verificação (172 testes, 95%) e validação com usuários |
| [03 · Guia da validação com usuários](situacao-3-testes-validacao/03-guia-validacao-com-usuarios.md) | Formulário/template do laudo e mensagem para os testadores |
| [04 · Laudo de qualidade](situacao-3-testes-validacao/04-laudo-de-qualidade.md) | Erros encontrados, correções e evidências |
| [05 · Registro de mudanças](situacao-3-testes-validacao/05-registro-de-mudancas.md) | O que mudou e por quê |
| [feedbacks/](situacao-3-testes-validacao/feedbacks/) | PDF com os 5 laudos |
| [evidencias/](situacao-3-testes-validacao/evidencias/) | Saída dos testes, cobertura e prints |

---

## Checklist do enunciado

| Exigência (PDF da disciplina) | Onde está | Situação |
|---|---|---|
| **S1** Verificar e adequar escopo/ideia | Revisão do projeto §1.2–1.4 | ✅ |
| **S1** Revisar UML (classes, casos de uso, sequência, atividades…) | Modelagem UML | ✅ |
| **S1** Revisar IHC: telas, mensagens de erro, mapas conceituais, protótipo | IHC e protótipo | ✅ |
| **S1** Projeto conceitual e lógico normalizado a partir do diagrama de classes | Banco de dados §5.1–5.3 | ✅ |
| **S1** Projeto físico documentado + dicionário de dados | `schema.sql`, §5.4, dicionário | ✅ |
| **S1** SGBD popular e de fácil manutenção | PostgreSQL | ✅ |
| **S1** Pedir crítica dos colegas sobre o planejamento | Revisão do projeto §1.5 | ✏️ preencher |
| **S1** Revisitar os documentos do PIT I | Revisão do projeto §1.4 | ✏️ anexar originais |
| **S2** Usuário no GitHub com o projeto | Este repositório | ✏️ publicar |
| **S2** Front-end em HTML, CSS e JavaScript | `app/views/` | ✅ |
| **S2** Back-end com padrão MVC | `app/models`, `services`, `controllers`, `views` | ✅ |
| **S2** Linguagem Java, PHP, C#, .NET ou Python | Python | ✅ |
| **S2** Front e back testados, funcionais, com erros tratados | 172 testes; `controllers/erros.py` | ✅ |
| **S2** Bibliotecas e manual de uso | Arquitetura §1.6, manual de uso | ✅ |
| **S2** Vídeo narrado (mín. 5 min) | Roteiro pronto | ✏️ gravar |
| **S3** Testes de verificação e validação documentados | Plano e relatório de testes | ✅ verificação · ✏️ validação |
| **S3** Formulário para 5 testadores (bugs, sugestões, prints) | `/feedback/` + template | ✅ |
| **S3** Coletar sugestões, corrigir e documentar | Laudo de qualidade, registro de mudanças | ✏️ após os laudos |
| **S3** PDF com as 5 opiniões (nome, data, funcionou, não funcionou, não testado) | Relatório para PDF do sistema | ✏️ após os laudos |
| **S3** Estrutura de diretórios no Git por situação | `docs/situacao-1…3` | ✅ |
| **S3** Vídeo das mudanças (até 5 min) | Roteiro pronto | ✏️ gravar |

## Preenchimento do arquivo de entrega (`PIT_atividade.docx`)

| Campo | Valor |
|---|---|
| Link do repositório | ✏️ `https://github.com/<seu-usuario>/agendafacil` |
| Linguagem do back-end | Python 3 (Flask, padrão MVC) |
| Banco de dados | PostgreSQL |
| Hospedagem | Render (serviço web + PostgreSQL) |
| Plataforma | Web responsiva (desktop e celular) |
| Modo de codificação | **(X) Tradicional** ( ) Low-code ( ) No-code |
| Link do GitHub com os códigos abertos | ✏️ mesmo link do repositório |
| Link da solução em funcionamento | ✏️ `https://<seu-app>.onrender.com` |
| Link do vídeo narrado (mín. 5 min) | ✏️ |
| Testes da solução (5 colegas) | Copiar do relatório para PDF / §2.4 do relatório de testes |
| Laudo de qualidade | Resumo do [laudo de qualidade](situacao-3-testes-validacao/04-laudo-de-qualidade.md) + prints |
| Vídeo da solução atualizada (até 5 min) | ✏️ |
