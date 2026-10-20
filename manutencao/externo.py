"""Backup semanal criptografado no Google Drive (E4.4, D-029).

Passos: gera o backup (banco + PDFs), junta num .zip, criptografa com a chave
pública (cripto.py), envia ao Drive (drive.py) e aplica a retenção: guarda só
os 2 backups mais recentes de cada mês e apaga os mais antigos do mês, mas só
depois de o novo estar no Drive. Cada tentativa fica registrada em
ExecucaoBackup e aparece na tela de backup.
"""
import logging
import re
import shutil
import tempfile
import threading
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from config.env import booleano, texto

from . import cripto, drive, nucleo
from .models import ExecucaoBackup

logger = logging.getLogger(__name__)

MANTER_POR_MES = 2
PASTA_PADRAO = "Gestor de Contratos - Backups"
PADRAO_NOME = re.compile(r"^gestor-(\d{4})-(\d{2})-\d{2}_\d{6}\.zip\.age$")
# Uma tentativa "em andamento" há mais que isso é considerada morta.
LIMITE_EM_ANDAMENTO = timedelta(hours=3)

_trava = threading.Lock()


class ErroExterno(Exception):
    """Configuração ausente ou outra impossibilidade (mensagem em português)."""


def ativo():
    return booleano("BACKUP_EXTERNO_ATIVO", False)


def configuracao():
    """Lê as variáveis de ambiente. Levanta ErroExterno dizendo o que falta."""
    nomes = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN",
             "BACKUP_CHAVE_PUBLICA")
    faltam = [n for n in nomes if not texto(n).strip()]
    if faltam:
        raise ErroExterno("Faltam variáveis de ambiente: " + ", ".join(faltam) + ".")
    if not cripto.chave_publica_valida(texto("BACKUP_CHAVE_PUBLICA")):
        raise ErroExterno("BACKUP_CHAVE_PUBLICA inválida: deve começar com 'age1'.")
    return {
        "client_id": texto("GOOGLE_CLIENT_ID").strip(),
        "client_secret": texto("GOOGLE_CLIENT_SECRET").strip(),
        "refresh_token": texto("GOOGLE_REFRESH_TOKEN").strip(),
        "chave_publica": texto("BACKUP_CHAVE_PUBLICA").strip(),
        "pasta": texto("BACKUP_DRIVE_PASTA", PASTA_PADRAO).strip() or PASTA_PADRAO,
    }


def escolher_apagar(nomes, manter_por_mes=MANTER_POR_MES):
    """Dos nomes de backup, devolve os que devem ser apagados (retenção mensal).

    Em cada mês guarda os `manter_por_mes` mais recentes. Nomes que não seguem
    o padrão gestor-AAAA-MM-DD_HHMMSS.zip.age nunca são apagados.
    """
    por_mes = {}
    for nome in nomes:
        m = PADRAO_NOME.match(nome)
        if m:
            por_mes.setdefault((m.group(1), m.group(2)), []).append(nome)
    apagar = []
    for grupo in por_mes.values():
        grupo.sort(reverse=True)  # o nome começa pela data: mais recente primeiro
        apagar += grupo[manter_por_mes:]
    return sorted(apagar)


def _zipar(pasta_backup, destino_zip):
    import zipfile

    with zipfile.ZipFile(destino_zip, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for arquivo in sorted(Path(pasta_backup).iterdir()):
            z.write(arquivo, f"{Path(pasta_backup).name}/{arquivo.name}")


def _banco():
    from django.db import connection

    c = connection.settings_dict
    return {"nome": c["NAME"], "usuario": c["USER"], "senha": c["PASSWORD"],
            "host": c["HOST"], "porta": c["PORT"]}


def _fazer_e_enviar(cfg, cliente, tmp):
    resultado = nucleo.fazer_backup(
        _banco(),
        pasta_projeto=settings.BASE_DIR,
        pasta_arquivos=settings.MEDIA_ROOT,
        pasta_backup=tmp / "pasta",
        manter=1,
        pg_bin=texto("PG_BIN") or None,
        incluir_projeto=False,
    )
    pasta_backup = Path(resultado["pasta"])
    zip_simples = tmp / "backup.zip"
    _zipar(pasta_backup, zip_simples)
    shutil.rmtree(tmp / "pasta", ignore_errors=True)
    nome = f"gestor-{pasta_backup.name}.zip.age"
    cifrado = tmp / nome
    cripto.criptografar(zip_simples, cifrado, cfg["chave_publica"])
    zip_simples.unlink()
    pasta_id = cliente.achar_ou_criar_pasta(cfg["pasta"])
    enviado = cliente.enviar(cifrado, nome, pasta_id)
    apagados = 0
    existentes = {a["name"]: a["id"] for a in cliente.listar(pasta_id)}
    for velho in escolher_apagar(existentes):
        cliente.apagar(existentes[velho])
        apagados += 1
    return nome, int(enviado.get("size", 0)), apagados


def executar(origem="manual", cliente=None):
    """Faz um backup externo completo e registra o resultado. Devolve a execução."""
    if not _trava.acquire(blocking=False):
        raise ErroExterno("Já existe um backup externo em andamento.")
    registro = None
    tmp = None
    try:
        agora = timezone.now()
        if ExecucaoBackup.objects.filter(
            sucesso__isnull=True, inicio__gte=agora - LIMITE_EM_ANDAMENTO
        ).exists():
            raise ErroExterno("Já existe um backup externo em andamento.")
        registro = ExecucaoBackup.objects.create(inicio=agora, origem=origem)
        try:
            cfg = configuracao()
            if cliente is None:
                cliente = drive.ClienteDrive(
                    cfg["client_id"], cfg["client_secret"], cfg["refresh_token"])
            tmp = Path(tempfile.mkdtemp(prefix="backup-externo-"))
            nome, tamanho, apagados = _fazer_e_enviar(cfg, cliente, tmp)
            registro.sucesso, registro.arquivo = True, nome
            registro.bytes, registro.apagados = tamanho, apagados
            registro.mensagem = "Backup enviado ao Google Drive."
        except (ErroExterno, nucleo.ErroBackup, cripto.ErroCripto, drive.ErroDrive) as erro:
            registro.sucesso, registro.mensagem = False, str(erro)[:500]
            logger.error("Backup externo falhou: %s", erro)
        except Exception as erro:  # noqa: BLE001 - nunca derrubar o agendador
            registro.sucesso = False
            registro.mensagem = f"Erro inesperado ({type(erro).__name__}). Veja o log do servidor."
            logger.exception("Backup externo: erro inesperado")
        registro.fim = timezone.now()
        registro.save()
        return registro
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
        _trava.release()


def marcar_interrompidas():
    """Tentativas 'em andamento' sem processo vivo (servidor reiniciou) viram falha."""
    return ExecucaoBackup.objects.filter(sucesso__isnull=True).update(
        sucesso=False, fim=timezone.now(),
        mensagem="Interrompido (o servidor foi reiniciado durante o envio).",
    )
