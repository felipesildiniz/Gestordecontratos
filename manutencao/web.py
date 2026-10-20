"""Tela de backup do sistema na nuvem (E4.2 item 4, decisão D-027).

Só o Admin acessa. O botão gera, no servidor, um .zip com a cópia do banco
(pg_dump), os PDFs e o manifesto de conferência (SHA-256), e o entrega para
download. O .zip NÃO leva o código nem o arquivo .env (o código está no GitHub
e o .env guarda segredos). O arquivo temporário é apagado depois do envio.
"""
import logging
import shutil
import tempfile
import threading
import zipfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.http import FileResponse
from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.perfis import eh_admin
from config.env import texto

from . import externo, nucleo
from .models import ExecucaoBackup

logger = logging.getLogger(__name__)

# Evita dois backups ao mesmo tempo (consumem disco e memória do servidor).
_em_andamento = threading.Lock()


class _RespostaTemporaria(FileResponse):
    """Resposta de arquivo que apaga a pasta temporária ao terminar o envio."""

    def __init__(self, *args, pasta_temporaria, **kwargs):
        super().__init__(*args, **kwargs)
        self._pasta_temporaria = pasta_temporaria

    def close(self):
        super().close()
        shutil.rmtree(self._pasta_temporaria, ignore_errors=True)


def _configuracao_do_banco():
    # Usa a conexão em uso: nos testes ela aponta para o banco de teste.
    c = connection.settings_dict
    return {
        "nome": c["NAME"],
        "usuario": c["USER"],
        "senha": c["PASSWORD"],
        "host": c["HOST"],
        "porta": c["PORT"],
    }


def _zipar_backup(pasta_backup, destino_zip):
    """Junta a pasta do backup em um único .zip (sem recompactar o que já é compactado)."""
    with zipfile.ZipFile(destino_zip, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for arquivo in sorted(pasta_backup.iterdir()):
            z.write(arquivo, f"{pasta_backup.name}/{arquivo.name}")


@login_required
def backup(request):
    if not eh_admin(request.user):
        raise PermissionDenied
    if request.method != "POST":
        return render(request, "backup.html", _contexto_externo())

    if not _em_andamento.acquire(blocking=False):
        return render(
            request, "backup.html",
            {"erro": "Já existe um backup sendo gerado. Aguarde e tente de novo.",
             **_contexto_externo()},
            status=409,
        )
    pasta = Path(tempfile.mkdtemp(prefix="backup-gestor-"))
    entregue = False
    try:
        resultado = nucleo.fazer_backup(
            _configuracao_do_banco(),
            pasta_projeto=settings.BASE_DIR,
            pasta_arquivos=settings.MEDIA_ROOT,
            pasta_backup=pasta / "pasta",
            manter=1,
            pg_bin=texto("PG_BIN") or None,
            incluir_projeto=False,
        )
        pasta_do_backup = Path(resultado["pasta"])
        zip_final = pasta / f"backup-gestor-{pasta_do_backup.name}.zip"
        _zipar_backup(pasta_do_backup, zip_final)
        logger.info("Backup gerado por %s: %s", request.user.get_username(), zip_final.name)
        resposta = _RespostaTemporaria(
            open(zip_final, "rb"),
            as_attachment=True,
            filename=zip_final.name,
            content_type="application/zip",
            pasta_temporaria=pasta,
        )
        resposta["Cache-Control"] = "no-store"
        entregue = True
        return resposta
    except nucleo.ErroBackup as erro:
        logger.error("Falha no backup pedido por %s: %s", request.user.get_username(), erro)
        return render(request, "backup.html", {"erro": str(erro)}, status=500)
    finally:
        _em_andamento.release()
        if not entregue:
            shutil.rmtree(pasta, ignore_errors=True)


def _contexto_externo():
    return {
        "externo_ativo": externo.ativo(),
        "execucoes": list(ExecucaoBackup.objects.all()[:5]),
    }


@login_required
def backup_externo(request):
    """Dispara agora o backup criptografado para o Google Drive (roda em segundo plano)."""
    if not eh_admin(request.user):
        raise PermissionDenied
    if request.method != "POST":
        return redirect("backup")

    def rodar():
        from django.db import close_old_connections

        try:
            externo.executar("manual")
        except externo.ErroExterno as erro:
            logger.warning("Backup externo manual: %s", erro)
        except Exception:  # noqa: BLE001
            logger.exception("Backup externo manual: erro inesperado")
        finally:
            close_old_connections()

    threading.Thread(target=rodar, daemon=True).start()
    messages.info(
        request,
        "Backup para o Google Drive iniciado. Ele leva alguns minutos; recarregue "
        "esta página para ver o resultado na lista abaixo.",
    )
    return redirect("backup")
