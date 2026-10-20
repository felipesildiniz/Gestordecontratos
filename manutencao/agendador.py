"""Agenda o backup externo semanal dentro do próprio servidor (E4.4).

O volume dos PDFs só se liga ao serviço `gestor`, então o agendador roda aqui,
numa thread iniciada pelo serve.py quando BACKUP_EXTERNO_ATIVO=True (só na
produção). Regra: roda de madrugada (1h às 6h, horário local) quando o último
sucesso tem 6 dias e 20 horas ou mais; se falhar, tenta de novo depois de 6
horas (então no máximo uma vez por noite).
"""
import logging
import time
from datetime import timedelta

from django.db import close_old_connections
from django.utils import timezone

from . import externo
from .models import ExecucaoBackup

logger = logging.getLogger(__name__)

INTERVALO_SEMANAL = timedelta(days=6, hours=20)
ESPERA_APOS_TENTATIVA = timedelta(hours=6)
HORAS_PERMITIDAS = range(1, 7)
VERIFICAR_A_CADA = 15 * 60


def devido(agora=None):
    """True se já passou da hora de um novo backup externo."""
    agora = agora or timezone.now()
    if timezone.localtime(agora).hour not in HORAS_PERMITIDAS:
        return False
    if ExecucaoBackup.objects.filter(inicio__gte=agora - ESPERA_APOS_TENTATIVA).exists():
        return False
    ultimo = ExecucaoBackup.objects.filter(sucesso=True).order_by("-fim").first()
    return ultimo is None or agora - ultimo.fim >= INTERVALO_SEMANAL


def passo():
    """Uma verificação: roda o backup se for a hora. Devolve a execução ou None."""
    close_old_connections()
    try:
        if devido():
            return externo.executar("agendado")
    except externo.ErroExterno as erro:
        logger.warning("Agendador: %s", erro)
    except Exception:  # noqa: BLE001
        logger.exception("Agendador: erro inesperado")
    finally:
        close_old_connections()
    return None


def loop():
    try:
        externo.marcar_interrompidas()
    except Exception:  # noqa: BLE001
        logger.exception("Agendador: não foi possível limpar execuções interrompidas")
    logger.info("Agendador do backup externo ligado.")
    while True:
        passo()
        time.sleep(VERIFICAR_A_CADA)
