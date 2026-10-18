@echo off
cd /d "%~dp0"
echo Criando o ambiente do sistema (pode demorar alguns minutos)...
python -m venv .venv
if errorlevel 1 goto erro
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto erro
echo.
echo Ambiente criado com sucesso.
echo Proximo passo: copie .env.example para .env e preencha (veja INSTALACAO_WINDOWS.md).
pause
exit /b 0
:erro
echo.
echo ERRO ao criar o ambiente. Copie a mensagem acima e envie para quem esta dando suporte.
pause
exit /b 1
