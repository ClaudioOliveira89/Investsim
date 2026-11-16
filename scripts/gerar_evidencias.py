"""Roda a suíte de testes e salva as evidências em docs/evidencias/.

Uso:
    python scripts/gerar_evidencias.py
    (defina TEST_PG_URL antes para incluir os testes no PostgreSQL real)

Gera:
  - resultado-pytest.txt  saída completa, teste a teste, com cobertura
  - cobertura.txt         só o relatório de cobertura
Caminhos da máquina (com o nome do usuário) são removidos da saída.
"""
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "docs" / "evidencias"


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    comando = [
        sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider",
        "--cov=app", "--cov-report=term-missing",
    ]
    ambiente = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    execucao = subprocess.run(
        comando, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", env=ambiente
    )
    saida = execucao.stdout + execucao.stderr
    for base in (str(RAIZ), str(Path.home())):  # projeto primeiro, depois a pasta do usuário
        for forma in (base, base.replace("\\", "/"), base.replace("\\", "\\\\")):
            saida = saida.replace(forma, ".")
    saida = "\n".join(
        "rootdir: (projeto)" if linha.startswith("rootdir:") else linha for linha in saida.splitlines()
    )

    cabecalho = (
        f"# Execução: {datetime.now():%d/%m/%Y %H:%M} · Python {platform.python_version()} · "
        f"{platform.system()} {platform.release()} · "
        f"PostgreSQL real: {'sim' if os.environ.get('TEST_PG_URL') else 'não (TEST_PG_URL ausente)'}\n\n"
    )
    (DESTINO / "resultado-pytest.txt").write_text(cabecalho + saida + "\n", encoding="utf-8")
    inicio = saida.find("tests coverage")
    cobertura = saida[saida.rfind("\n", 0, inicio) + 1:] if inicio >= 0 else "cobertura não encontrada"
    (DESTINO / "cobertura.txt").write_text(cobertura + "\n", encoding="utf-8")

    resumo = [linha for linha in saida.splitlines() if " passed" in linha or " failed" in linha]
    print(resumo[-1] if resumo else saida[-500:])
    return execucao.returncode


if __name__ == "__main__":
    sys.exit(main())
