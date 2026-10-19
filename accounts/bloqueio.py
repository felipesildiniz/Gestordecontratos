"""Bloqueio de login temporário e progressivo (E4.3, decisão D-030).

Regras:
- 5 senhas erradas seguidas para o mesmo usuário bloqueiam o login dele;
- o 1º bloqueio dura 15 minutos, o 2º 1 hora, o 3º e os seguintes 24 horas;
- durante o bloqueio nem a senha certa entra, e novas tentativas não contam;
- a contagem de reincidência volta a zero se o último bloqueio terminou há
  mais de 7 dias; entrar com sucesso zera as senhas erradas seguidas;
- nunca há bloqueio permanente: o administrador pode desbloquear antes
  (comando `desbloquear_usuario` ou tela de administração).

O bloqueio é por nome de usuário (e não por IP), porque atrás do proxy do
Railway o IP de quem acessa não é confiável. Nomes que não existem também são
controlados, para a tela não revelar quem tem conta.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import BloqueioLogin

LIMITE_DE_FALHAS = 5
DURACOES = (timedelta(minutes=15), timedelta(hours=1), timedelta(hours=24))
ZERA_NIVEL_APOS = timedelta(days=7)
GUARDAR_REGISTROS = timedelta(days=30)


def _agora():
    return timezone.now()


def chave(nome):
    """Forma única do nome de usuário usada no controle (sem espaços e sem caixa)."""
    return (nome or "").strip().casefold()[:150]


def duracao_do_nivel(nivel):
    """Quanto dura o bloqueio de nível 1, 2, 3...; do 3º em diante, sempre 24 h."""
    return DURACOES[min(max(nivel, 1), len(DURACOES)) - 1]


def bloqueio_ativo(nome):
    """Devolve o registro se o login deste nome está bloqueado agora; senão, None."""
    k = chave(nome)
    if not k:
        return None
    return BloqueioLogin.objects.filter(usuario=k, bloqueado_ate__gt=_agora()).first()


def esta_bloqueado(nome):
    return bloqueio_ativo(nome) is not None


def registrar_falha(nome):
    """Conta uma senha errada. Devolve o registro, ou None se o nome for vazio."""
    k = chave(nome)
    if not k:
        return None
    agora = _agora()
    with transaction.atomic():
        BloqueioLogin.objects.filter(
            ultima_falha__lt=agora - GUARDAR_REGISTROS, avisos_pendentes=0
        ).delete()
        registro, _ = BloqueioLogin.objects.select_for_update().get_or_create(usuario=k)
        if registro.bloqueado_ate and registro.bloqueado_ate > agora:
            return registro  # já bloqueado: a tentativa não conta nem estende o prazo
        if (
            registro.nivel
            and registro.bloqueado_ate
            and agora - registro.bloqueado_ate > ZERA_NIVEL_APOS
        ):
            registro.nivel = 0
        registro.falhas += 1
        registro.ultima_falha = agora
        if registro.falhas >= LIMITE_DE_FALHAS:
            registro.nivel += 1
            registro.falhas = 0
            registro.bloqueado_ate = agora + duracao_do_nivel(registro.nivel)
            registro.ultimo_bloqueio_em = agora
            registro.avisos_pendentes += 1
        registro.save()
    return registro


def registrar_sucesso(nome):
    """Entrar com sucesso zera as senhas erradas seguidas (o nível é mantido)."""
    k = chave(nome)
    if k:
        BloqueioLogin.objects.filter(usuario=k).update(falhas=0)


def desbloquear(nome=None, todos=False):
    """Tira o bloqueio e zera a reincidência. Devolve quantos registros foram mexidos."""
    consulta = BloqueioLogin.objects.all() if todos else BloqueioLogin.objects.filter(
        usuario=chave(nome)
    )
    return consulta.update(bloqueado_ate=None, falhas=0, nivel=0)


def pegar_avisos(nome):
    """Devolve (quantos bloqueios ainda não foram avisados, quando foi o último) e zera."""
    k = chave(nome)
    if not k:
        return 0, None
    with transaction.atomic():
        registro = BloqueioLogin.objects.select_for_update().filter(usuario=k).first()
        if registro is None or not registro.avisos_pendentes:
            return 0, None
        quantos, quando = registro.avisos_pendentes, registro.ultimo_bloqueio_em
        registro.avisos_pendentes = 0
        registro.save(update_fields=["avisos_pendentes"])
    return quantos, quando
