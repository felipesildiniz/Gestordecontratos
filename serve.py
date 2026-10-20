"""Inicia o servidor de produção (waitress), que funciona no Windows.

Uso normal: dê dois cliques em iniciar_servidor.bat.
"""
import os
from pathlib import Path

from config.env import booleano, carregar_env, texto

BASE_DIR = Path(__file__).resolve().parent
carregar_env(BASE_DIR / ".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def opcoes_de_proxy():
    """Faz o waitress aceitar X-Forwarded-Proto/For do proxy da hospedagem.

    Sem isso o waitress descarta o cabeçalho, o Django acha que a conexão é
    HTTP e, com DJANGO_USAR_HTTPS=True, redireciona para HTTPS sem fim
    (ERR_TOO_MANY_REDIRECTS). Só vale quando DJANGO_USAR_HTTPS=True; o
    servidor da hospedagem não é acessível sem passar pelo proxy dela.
    """
    if not booleano("DJANGO_USAR_HTTPS", False):
        return {}
    return {
        "trusted_proxy": texto("SERVIDOR_PROXY_CONFIAVEL", "*"),
        "trusted_proxy_headers": {"x-forwarded-proto", "x-forwarded-for", "x-forwarded-host", "x-forwarded-port"},
        "clear_untrusted_proxy_headers": True,
    }


def main():
    from waitress import serve

    from config.wsgi import application

    if booleano("BACKUP_EXTERNO_ATIVO", False):
        import threading

        from manutencao import agendador

        threading.Thread(target=agendador.loop, name="backup-externo", daemon=True).start()

    host = texto("SERVIDOR_HOST", "0.0.0.0")
    # Em hospedagens como o Railway a porta vem na variável PORT.
    porta = int(texto("PORT") or texto("SERVIDOR_PORTA", "8000"))
    print(f"Gestor de Contratos em execução na porta {porta}.")
    print("Acesse por http://localhost:%d neste computador, ou pelo IP do servidor nos demais." % porta)
    print("Para encerrar, feche esta janela ou pressione Ctrl+C.")
    serve(application, host=host, port=porta, threads=8, **opcoes_de_proxy())


if __name__ == "__main__":
    main()
