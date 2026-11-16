"""Gera o dicionário de dados em Markdown a partir do catálogo do PostgreSQL.

Uso:
    python scripts/gerar_dicionario.py "postgresql+psycopg://usuario:senha@localhost:5432/investsim"

Lê tabelas, colunas, tipos, domínios, nulidade, valores padrão, chaves, restrições e
comentários (COMMENT ON) diretamente do banco — assim o dicionário nunca fica
desatualizado em relação ao projeto físico.
"""
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

SAIDA = Path("docs/dicionario-de-dados.md")

COLUNAS = text("""
SELECT c.table_name, c.column_name, c.ordinal_position,
       COALESCE(c.domain_name, '') AS dominio,
       format_type(a.atttypid, a.atttypmod) AS tipo,
       c.is_nullable = 'YES' AS nulo,
       COALESCE(c.column_default, '') AS padrao,
       c.is_identity = 'YES' AS identidade,
       COALESCE(col_description(a.attrelid, a.attnum), '') AS comentario
  FROM information_schema.columns c
  JOIN pg_attribute a ON a.attrelid = (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass
                     AND a.attname = c.column_name
  JOIN information_schema.tables t ON t.table_name = c.table_name AND t.table_schema = c.table_schema
 WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE'
 ORDER BY c.table_name, c.ordinal_position
""")

CHAVES = text("""
SELECT tc.table_name, kcu.column_name, tc.constraint_type,
       ccu.table_name AS ref_tabela, ccu.column_name AS ref_coluna
  FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu
    ON kcu.constraint_name = tc.constraint_name AND kcu.table_schema = tc.table_schema
  LEFT JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name AND tc.constraint_type = 'FOREIGN KEY'
 WHERE tc.table_schema = 'public' AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE')
""")

RESTRICOES = text("""
SELECT conrelid::regclass::text AS tabela, conname AS nome, pg_get_constraintdef(oid) AS definicao,
       CASE contype WHEN 'c' THEN 'CHECK' WHEN 'f' THEN 'FOREIGN KEY' WHEN 'x' THEN 'EXCLUDE'
                    WHEN 'u' THEN 'UNIQUE' WHEN 'p' THEN 'PRIMARY KEY' END AS tipo
  FROM pg_constraint
 WHERE connamespace = 'public'::regnamespace AND conrelid <> 0
 ORDER BY 1, contype, 2
""")

DOMINIOS = text("""
SELECT t.typname AS nome, format_type(t.typbasetype, t.typtypmod) AS base,
       string_agg(pg_get_constraintdef(c.oid), ' AND ') AS regra
  FROM pg_type t LEFT JOIN pg_constraint c ON c.contypid = t.oid
 WHERE t.typtype = 'd' AND t.typnamespace = 'public'::regnamespace
 GROUP BY 1, 2 ORDER BY 1
""")

TABELAS = text("""
SELECT c.relname AS tabela, COALESCE(obj_description(c.oid, 'pg_class'), '') AS comentario
  FROM pg_class c
 WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r'
 ORDER BY 1
""")

INDICES = text("""
SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY 1, 2
""")


def esc(valor) -> str:
    return str(valor).replace("|", "\\|").replace("\n", " ")


def main(url: str) -> None:
    engine = create_engine(url)
    with engine.connect() as con:
        colunas = con.execute(COLUNAS).mappings().all()
        chaves = con.execute(CHAVES).mappings().all()
        restricoes = con.execute(RESTRICOES).mappings().all()
        dominios = con.execute(DOMINIOS).mappings().all()
        tabelas = con.execute(TABELAS).mappings().all()
        indices = con.execute(INDICES).mappings().all()
    engine.dispose()

    bases = {d["nome"]: d["base"] for d in dominios}
    marcas: dict[tuple[str, str], list[str]] = {}
    for k in chaves:
        rotulo = {"PRIMARY KEY": "PK", "UNIQUE": "UQ"}.get(k["constraint_type"])
        if k["constraint_type"] == "FOREIGN KEY":
            rotulo = f"FK → {k['ref_tabela']}.{k['ref_coluna']}"
        marcas.setdefault((k["table_name"], k["column_name"]), [])
        if rotulo not in marcas[(k["table_name"], k["column_name"])]:
            marcas[(k["table_name"], k["column_name"])].append(rotulo)

    linhas = [
        "# Dicionário de dados — InvestSim",
        "",
        "> Gerado automaticamente a partir do catálogo do PostgreSQL por",
        "> `scripts/gerar_dicionario.py` (não edite à mão: altere o `database/schema.sql`,",
        "> recrie o banco e rode o script de novo).",
        "",
        "Legenda: **PK** chave primária · **FK** chave estrangeira · **UQ** valor único ·",
        "**Nulo** = aceita ficar em branco.",
        "",
        "## Domínios",
        "",
        "| Domínio | Tipo base | Regra de validação |",
        "|---|---|---|",
    ]
    linhas += [f"| `{d['nome']}` | {d['base']} | `{esc(d['regra'] or '—')}` |" for d in dominios]

    for t in tabelas:
        nome = t["tabela"]
        linhas += ["", f"## Tabela `{nome}`", "", t["comentario"] or "", ""]
        linhas += ["| Coluna | Tipo / domínio | Nulo | Padrão | Chave | Descrição |", "|---|---|---|---|---|---|"]
        for c in (c for c in colunas if c["table_name"] == nome):
            tipo = f"`{c['dominio']}` ({bases[c['dominio']]})" if c["dominio"] else c["tipo"]
            padrao = "identity" if c["identidade"] else esc(c["padrao"]) or "—"
            chave = ", ".join(marcas.get((nome, c["column_name"]), [])) or "—"
            linhas.append(
                f"| `{c['column_name']}` | {tipo} | {'Sim' if c['nulo'] else 'Não'} | {padrao} | {chave} | {esc(c['comentario']) or '—'} |"
            )
        regras = [r for r in restricoes if r["tabela"] == nome and r["tipo"] in ("CHECK", "EXCLUDE", "FOREIGN KEY")]
        if regras:
            linhas += ["", "**Restrições:**", ""]
            linhas += [f"- `{r['nome']}` ({r['tipo']}): `{esc(r['definicao'])}`" for r in regras]
        idx = [i for i in indices if i["tablename"] == nome and not i["indexname"].startswith(("pk_", "uq_"))]
        if idx:
            linhas += ["", "**Índices:**", ""]
            linhas += [f"- `{i['indexname']}`: `{esc(i['indexdef'])}`" for i in idx]

    SAIDA.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"Dicionário gerado em {SAIDA}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
