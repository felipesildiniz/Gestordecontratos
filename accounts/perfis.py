"""Perfis de acesso do sistema (decisão D-010).

- Admin: edita tudo, inclusive usuários e o desbloqueio de logins.
- Consulta: somente visualiza.

Os perfis são grupos do Django. Um usuário sem perfil consegue entrar, mas não
tem acesso a nada. Um superusuário do Django é tratado como Admin.
"""

ADMIN = "Admin"
CONSULTA = "Consulta"
PERFIS = (ADMIN, CONSULTA)


def perfil_do_usuario(usuario):
    """Devolve ADMIN, CONSULTA ou None (sem perfil ou não autenticado)."""
    if not usuario.is_authenticated:
        return None
    if usuario.is_superuser:
        return ADMIN
    nomes = set(usuario.groups.values_list("name", flat=True))
    if ADMIN in nomes:
        return ADMIN
    if CONSULTA in nomes:
        return CONSULTA
    return None


def eh_admin(usuario):
    return perfil_do_usuario(usuario) == ADMIN


def garantir_perfis(using="default"):
    """Cria os grupos Admin e Consulta e ajusta suas permissões.

    Pode ser chamada quantas vezes for preciso. Devolve um dicionário
    {nome do perfil: grupo}.
    """
    from django.apps import apps
    from django.contrib.auth.management import create_permissions
    from django.contrib.auth.models import Group, Permission

    # Em um banco novo, as permissões dos apps auth e accounts podem ainda não existir.
    create_permissions(apps.get_app_config("auth"), verbosity=0, using=using)
    create_permissions(apps.get_app_config("accounts"), verbosity=0, using=using)

    grupos = {
        nome: Group.objects.using(using).get_or_create(name=nome)[0]
        for nome in PERFIS
    }
    # Admin gerencia usuários (adicionar, alterar, excluir e ver).
    permissoes_usuario = Permission.objects.using(using).filter(
        content_type__app_label="auth", content_type__model="user"
    )
    # Também vê e desbloqueia os bloqueios de login (D-030).
    permissoes_bloqueio = Permission.objects.using(using).filter(
        content_type__app_label="accounts",
        content_type__model="bloqueiologin",
        codename__in=["view_bloqueiologin", "change_bloqueiologin"],
    )
    # E redefine a verificação em duas etapas de quem perdeu o aplicativo.
    permissoes_mfa = Permission.objects.using(using).filter(
        content_type__app_label="accounts",
        content_type__model="dispositivomfa",
        codename__in=["view_dispositivomfa", "change_dispositivomfa"],
    )
    grupos[ADMIN].permissions.set(
        list(permissoes_usuario) + list(permissoes_bloqueio) + list(permissoes_mfa)
    )
    # Consulta não tem permissões de edição. As de visualização dos cadastros
    # serão acrescentadas aqui nas próximas etapas.
    grupos[CONSULTA].permissions.clear()
    return grupos


def sincronizar_staff(sender, instance, action, reverse, pk_set, using="default", **kwargs):
    """Mantém o acesso à área administrativa (is_staff) igual ao perfil Admin.

    Resolve P-016: antes era preciso marcar "staff" à mão ao criar um Admin em
    /admin/. Agora, quem entra no grupo Admin, por qualquer caminho (formulário
    do admin, shell, comando), recebe is_staff; quem sai do grupo Admin perde,
    exceto superusuário. O perfil Consulta nunca concede staff.

    Ligada ao sinal m2m_changed de User.groups (veja accounts/apps.py).
    """
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    Usuario = get_user_model()
    qs = Usuario.objects.using(using)

    if action == "pre_clear":
        # Depois do clear não dá mais para saber quem estava no grupo.
        if reverse and instance.name == ADMIN:
            instance._admins_antes_do_clear = list(
                instance.user_set.values_list("pk", flat=True)
            )
        return
    if action not in ("post_add", "post_remove", "post_clear"):
        return

    def revogar(ids):
        # Perde staff quem não é superusuário e não está mais no grupo Admin.
        ids = [
            pk for pk in ids
            if not Usuario.objects.using(using).filter(pk=pk, groups__name=ADMIN).exists()
        ]
        qs.filter(pk__in=ids, is_superuser=False).update(is_staff=False)

    if not reverse:  # instance é o usuário; pk_set são grupos
        if action == "post_add":
            if Group.objects.using(using).filter(pk__in=pk_set or [], name=ADMIN).exists():
                qs.filter(pk=instance.pk).update(is_staff=True)
                instance.is_staff = True
        else:
            if action == "post_clear" or Group.objects.using(using).filter(
                pk__in=pk_set or [], name=ADMIN
            ).exists():
                revogar([instance.pk])
                instance.is_staff = qs.filter(pk=instance.pk, is_staff=True).exists()
    else:  # instance é o grupo; pk_set são usuários
        if instance.name != ADMIN:
            return
        if action == "post_add":
            qs.filter(pk__in=pk_set or []).update(is_staff=True)
        elif action == "post_remove":
            revogar(list(pk_set or []))
        else:  # post_clear
            revogar(getattr(instance, "_admins_antes_do_clear", []))
