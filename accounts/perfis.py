"""Perfis de acesso do sistema (decisão D-010).

- Admin: edita tudo, inclusive usuários.
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

    # Em um banco novo, as permissões do app auth podem ainda não existir.
    create_permissions(apps.get_app_config("auth"), verbosity=0, using=using)

    grupos = {
        nome: Group.objects.using(using).get_or_create(name=nome)[0]
        for nome in PERFIS
    }
    # Admin gerencia usuários (adicionar, alterar, excluir e ver).
    permissoes_usuario = Permission.objects.using(using).filter(
        content_type__app_label="auth", content_type__model="user"
    )
    grupos[ADMIN].permissions.set(permissoes_usuario)
    # Consulta não tem permissões de edição. As de visualização dos cadastros
    # serão acrescentadas aqui nas próximas etapas.
    grupos[CONSULTA].permissions.clear()
    return grupos
