# Gestor de Contratos — Licitações

Sistema web para gerenciar contratos administrativos, atas, vigências, saldos, termos aditivos, documentos, alertas, auditoria e relatórios.

- **Stack:** Python + Django, PostgreSQL, servidor `waitress` (Windows).
- **Instalação:** veja `INSTALACAO_WINDOWS.md`.
- **Estado do projeto:** veja `PROJECT_STATE.md` (fonte oficial). Demais documentos: `ROADMAP.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `DATABASE.md`, `BUSINESS_RULES.md`, `CHANGELOG.md`.

## Estrutura

```
config/      configurações do Django, leitura do .env, URLs
accounts/    login, perfis Admin e Consulta, comando criar_usuario, testes
templates/   páginas HTML
static/      CSS
manutencao/  backup e restauração (sem Django), testes
serve.py     servidor de produção (waitress)
fazer_backup.py, restaurar_backup.py   backup e restauração (veja INSTALACAO_WINDOWS.md)
*.bat        atalhos para Windows
```

## Comandos úteis (com o ambiente ativado: `.venv\Scripts\activate`)

```
python manage.py test                 # roda os testes
python manage.py criar_usuario --usuario LOGIN --perfil admin
python manage.py criar_usuario --usuario LOGIN --perfil consulta
python fazer_backup.py                # backup do banco, PDFs e código
python restaurar_backup.py PASTA      # restaura em um banco novo
```
