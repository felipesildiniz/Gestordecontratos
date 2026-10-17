"""Inicia o servidor de produção (waitress), que funciona no Windows.

Uso normal: dê dois cliques em iniciar_servidor.bat.
"""
import os
from pathlib import Path

from config.env import carregar_env, texto

BASE_DIR = Path(__file__).resolve().parent
carregar_env(BASE_DIR / ".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def main():
    from waitress import serve

    from config.wsgi import application

    host = texto("SERVIDOR_HOST", "0.0.0.0")
    # Em hospedagens como o Railway a porta vem na variável PORT.
    porta = int(texto("PORT") or texto("SERVIDOR_PORTA", "8000"))
    print(f"Gestor de Contratos em execução na porta {porta}.")
    print("Acesse por http://localhost:%d neste computador, ou pelo IP do servidor nos demais." % porta)
    print("Para encerrar, feche esta janela ou pressione Ctrl+C.")
    serve(application, host=host, port=porta, threads=8)


if __name__ == "__main__":
    main()
