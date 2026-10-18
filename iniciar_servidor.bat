@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo O ambiente ainda nao foi criado. Execute criar_ambiente.bat primeiro.
  pause
  exit /b 1
)
call .venv\Scripts\activate
python manage.py migrate --noinput
if errorlevel 1 goto erro
python manage.py collectstatic --noinput
if errorlevel 1 goto erro
python serve.py
pause
exit /b 0
:erro
echo.
echo ERRO ao preparar o sistema. Copie a mensagem acima e envie para quem esta dando suporte.
pause
exit /b 1
