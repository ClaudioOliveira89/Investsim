"""Ponto de entrada da aplicação.

- Produção: `gunicorn wsgi:app` (só importa `app`; o bloco __main__ não roda).
- Desenvolvimento: `flask run` ou `python wsgi.py` (botão ▶ do VS Code).
"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Conveniência para desenvolvimento: prepara o banco se ainda estiver vazio.
    # Os dois passos são idempotentes (não apagam nem duplicam dados).
    from app.cli import criar_estrutura
    from app.seed import carregar_dados_demo

    with app.app_context():
        print(criar_estrutura())
        print(carregar_dados_demo())
    porta = int(os.environ.get("PORT", "5000"))
    print(f"Acesse http://127.0.0.1:{porta}  (Ctrl+C para parar)")
    app.run(host="127.0.0.1", port=porta, debug=os.environ.get("FLASK_DEBUG", "1") == "1")
