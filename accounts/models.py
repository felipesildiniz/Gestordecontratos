"""O app accounts ainda não define tabelas próprias.

Usuários e perfis usam as tabelas padrão do Django (decisão D-010). Este
arquivo precisa existir para o Django enviar o sinal post_migrate ao app, que
é o que cria os perfis Admin e Consulta (veja apps.py).
"""
