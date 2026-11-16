# 3. Instalação, testes e implantação

## 3.1 Pré-requisitos

- Python 3.12 ou superior
- PostgreSQL 14 ou superior
- Git

## 3.2 Rodando na sua máquina (Windows / PowerShell)

```powershell
git clone https://github.com/<seu-usuario>/agendafacil.git
cd agendafacil

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# Banco: cria o usuário "agendafacil" e os bancos (pede a senha do postgres)
psql -U postgres -h localhost -f database/criar_banco.sql

# Configuração
Copy-Item .env.example .env
#   edite o .env: SECRET_KEY e, se mudou a senha, DATABASE_URL

flask init-db      # cria tabelas, domínios, restrições, índices e visões
flask seed         # dados de demonstração (opcional)
flask run          # http://127.0.0.1:5000
```

**Atalho para desenvolvimento:** `python wsgi.py` (ou o botão ▶ do VS Code com o `wsgi.py` aberto) cria as tabelas e os dados de demonstração se o banco estiver vazio e sobe o servidor em <http://127.0.0.1:5000>.

No Linux/macOS, troque a ativação do ambiente por `source .venv/bin/activate` e
`Copy-Item` por `cp`.

Comandos úteis:

| Comando | O que faz |
|---|---|
| `flask init-db` | Cria o que ainda não existe (pode rodar várias vezes) |
| `flask init-db --recriar` | **Apaga tudo** e recria (pede confirmação) |
| `flask seed` | Carrega dados de demonstração (ignora se já houver usuários) |
| `flask criar-admin` | Cria um administrador pedindo nome, e-mail e senha |

## 3.3 Rodando os testes

```powershell
pytest                       # unitários + integração + E2E (usa SQLite em memória)
pytest tests/unit            # só unitários
pytest -m "not e2e"          # sem navegador
pytest --cov=app --cov-report=html   # relatório de cobertura em htmlcov/index.html

# Validar o schema no PostgreSQL de verdade (recria as tabelas do banco indicado!)
$env:TEST_PG_URL = "postgresql+psycopg://agendafacil:agendafacil@localhost:5432/agendafacil_teste"
pytest -m postgres
```

Os testes E2E usam o **Microsoft Edge** instalado no Windows. Em outro sistema:
`python -m playwright install chromium` e `$env:E2E_CANAL = ""`.

O GitHub Actions (`.github/workflows/testes.yml`) roda a suíte completa — inclusive PostgreSQL
e E2E — a cada `push`.

## 3.4 Publicando na internet (Render — plano gratuito)

O repositório já tem o arquivo `render.yaml` (*blueprint*), que cria o banco PostgreSQL e o
serviço web.

1. Suba o código para o GitHub.
2. Crie uma conta em <https://render.com> e conecte o GitHub.
3. **New → Blueprint** → escolha o repositório → **Apply**.
4. Aguarde o deploy. O endereço fica parecido com `https://agendafacil-xxxx.onrender.com`.
5. Entre com `admin@agendafacil.com` / `Agenda@2026` e **troque a senha**.

A cada deploy, o comando de inicialização roda `flask init-db && flask seed` (os dois são
idempotentes: não apagam dados) e sobe o `gunicorn`.

**Limitações do plano gratuito do Render** (confira as regras atuais no site):

- o serviço "dorme" depois de um tempo sem acesso, e o primeiro acesso seguinte demora
  alguns segundos;
- o banco PostgreSQL gratuito tem prazo de validade. Para manter o sistema no ar depois da
  avaliação, use um PostgreSQL gratuito do **Neon** (<https://neon.tech>) e coloque a
  *connection string* dele na variável `DATABASE_URL` do serviço web.

## 3.5 Variáveis de ambiente

| Variável | Exemplo | Descrição |
|---|---|---|
| `SECRET_KEY` | (aleatória) | Assina sessões e tokens CSRF. **Obrigatória em produção** |
| `DATABASE_URL` | `postgresql+psycopg://u:s@host:5432/db` | Conexão (também aceita `postgres://`) |
| `FUSO_HORARIO` | `America/Sao_Paulo` | Fuso do estabelecimento |
| `HORA_ABERTURA` / `HORA_FECHAMENTO` | `08:00` / `20:00` | Expediente |
| `DIAS_FUNCIONAMENTO` | `0,1,2,3,4,5` | 0 = segunda … 6 = domingo |
| `INTERVALO_AGENDA_MIN` | `30` | Intervalo entre os horários oferecidos |
