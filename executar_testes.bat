@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
python manage.py test -v 2
echo.
echo Se o final mostrar "OK", os testes passaram. Se mostrar FAILED ou ERROR, copie tudo e envie para suporte.
pause
