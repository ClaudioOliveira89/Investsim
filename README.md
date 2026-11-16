# InvestSim — simulador de carteiras de investimento

Monte carteiras simuladas com **ações, BDRs, FIIs, ETFs e cripto**, registre quanto aplicou e quando,
e acompanhe como o mercado andou desde então. O **relatório compara a carteira com o CDI**:
rentabilidade pelo método de cotas, % do CDI, quanto o mesmo dinheiro teria rendido no CDI,
proventos recebidos, volatilidade, maior queda e o desempenho mês a mês.

Projeto Integrador Transdisciplinar em Engenharia de Software II — Cruzeiro do Sul Virtual.
Experimento para futura integração.

> Simulador educacional: não movimenta dinheiro real e não é recomendação de investimento.

![Relatório da carteira](docs/telas/04-relatorio.png)

## Funcionalidades

- **Carteiras simuladas**: cada usuário cria quantas quiser e só ele as enxerga.
- **Operações com preço real**: compra ou venda numa data passada, informando **valor em R$** (a
  quantidade é calculada) ou quantidade. O preço é o fechamento do dia (ou do último pregão).
- **Regras de mercado**: ações, BDRs, FIIs e ETFs em unidades inteiras; cripto com até 8 casas; venda nunca
  excede a posição (em nenhum momento do histórico); sem datas futuras.
- **Relatório × CDI**: veredito, KPIs, gráfico de rentabilidade e de patrimônio contra o CDI, posições
  com preço médio e resultado, alocação por classe, tabela mês a mês, extrato, **PDF** e **CSV**.
- **Terminal de mercado**: categorias separadas de ações, BDRs, FIIs, ETFs e cripto com contagem de ativos e ícones; listas com variação do dia/12 meses e minigráfico; página do
  ativo com histórico (1M a 5A), proventos e *dividend yield*, e botão "Simular compra".
- **Cadastro público** (para testadores), perfis investidor/administrador, catálogo de ativos,
  formulário de laudo de teste com prints.
- Tema **escuro/claro**, responsivo (celular) e acessível (teclado, leitores de tela).

## Como os números são calculados

| Indicador | Método |
|---|---|
| Rentabilidade | **Cotas (TWR)**: aportes e resgates não distorcem o resultado, como em fundos |
| CDI no período | Produto dos CDIs diários (série 12 do SGS/Banco Central) desde a 1ª aplicação |
| % do CDI | Rentabilidade da carteira ÷ CDI do período |
| "Se estivesse no CDI" | Cada aporte e resgate, nas mesmas datas, aplicado a 100% do CDI |
| Preço médio | Média ponderada das compras (com taxas); vendas não alteram o preço médio |
| Proventos | Dividendos/JCP/rendimentos por cota na data ex, creditados como caixa da carteira |
| Volatilidade / maior queda | Desvio-padrão anualizado dos retornos diários / *drawdown* máximo das cotas |

Esses cálculos ficam em **`app/simulador/`, em Python puro e sem dependência de framework**, prontos
para serem importados pelo Django.

## Dados de mercado

| Fonte | Uso |
|---|---|
| [brapi.dev](https://brapi.dev) | Cotações diárias e proventos da B3 e de cripto (requer token gratuito) |
| Banco Central (SGS, série 12) | CDI diário oficial |
| Modo demonstração | Mercado sintético e reproduzível: funciona sem token e sem internet |

Sem `BRAPI_TOKEN`, o sistema entra automaticamente em **modo demonstração**, com uma faixa de aviso
na tela. As cotações ficam em cache no banco: só é baixado o que falta ou está vencido, e, se a fonte
cair, o sistema segue com os últimos dados salvos e avisa o usuário.

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Back-end | Python 3 + Flask 3, padrão **MVC** (models · services · controllers · views) + núcleo `simulador` |
| Banco | **PostgreSQL** (domínios, CHECKs, FKs, visões) via SQLAlchemy 2 + psycopg 3; SQLite para desenvolvimento |
| Front-end | HTML5, CSS3 e JavaScript puros + Chart.js (local, MIT) |
| Segurança | Flask-Login, hash de senha, CSRF, isolamento de carteiras por usuário, cabeçalhos de segurança |
| Testes | pytest (unidade, integração, PostgreSQL) + Playwright (E2E) — 153 testes, 92% de cobertura |
| CI / Deploy | GitHub Actions · Render (gunicorn) |

## Como rodar

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env          # defina SECRET_KEY e DEMO_PASSWORD; BRAPI_TOKEN é opcional
python wsgi.py                       # cria o banco, carrega a demonstração e abre em http://127.0.0.1:5000
```

Na primeira inicialização, o sistema cria as contas de demonstração investidor@investsim.com.br e admin@investsim.com.br com a senha definida em DEMO_PASSWORD no ambiente do serviço. 
Configure essa variável no Render e não publique seu valor. 
Após entrar como administrador, altere a senha. 
Os demais usuários podem criar uma conta em Criar conta.

Para usar o **PostgreSQL** local:

```powershell
psql -U postgres -h localhost -f database/criar_banco.sql
# no .env: DATABASE_URL=postgresql+psycopg://investsim:investsim@localhost:5432/investsim
flask init-db; flask seed; flask run
```

## Testes

```powershell
pytest                                  # unidade + integração + E2E (Edge); modo demonstração, sem internet
$env:TEST_PG_URL = "postgresql+psycopg://investsim:investsim@localhost:5432/investsim_teste"
pytest -m postgres                      # valida database/schema.sql num PostgreSQL real
python scripts/gerar_evidencias.py      # salva saída e cobertura em docs/evidencias/
python scripts/capturar_telas.py        # capturas de todas as telas em docs/telas/
```

## Estrutura

```text
app/
  simulador/     núcleo puro: fontes de dados, regras das operações, motor de cálculo (portável)
  models/        Model: entidades (usuário, ativo, cotação, provento, CDI, carteira, operação)
  services/      Model: casos de uso (mercado com cache, carteiras, usuários, feedback)
  controllers/   Controller: rotas (carteiras, mercado, auth, admin) e API JSON
  forms/         validação de entrada + CSRF
  views/         View: templates, CSS, JavaScript e Chart.js
database/        schema.sql (projeto físico) e criação do banco
docs/            telas, dicionário de dados, evidências de teste (legado-agendafacil/ = versão anterior)
tests/           unit · integration · e2e
scripts/         capturas de tela, dicionário de dados, evidências
```

## Publicação (Render)

O `render.yaml` cria o PostgreSQL e o serviço web. No Render: **New → Blueprint → este repositório**,
e informe o `BRAPI_TOKEN` quando solicitado. A cada deploy, `flask init-db && flask seed` rodam sem
apagar dados.

## Autor

**Claudio Henrique De Oliveira Soares** · RGM · Engenharia de Software — Cruzeiro do Sul Virtual
