@echo off
rem Restaura um backup em um banco NOVO e em pastas separadas, sem tocar no sistema em uso.
setlocal enabledelayedexpansion
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo O ambiente ainda nao foi criado. Execute criar_ambiente.bat primeiro.
  pause
  exit /b 1
)
call .venv\Scripts\activate
set PASTA=%~1
if "%PASTA%"=="" (
  echo Backups disponiveis na pasta backups:
  dir /b /ad backups
  echo.
  set /p NOME=Digite o nome da pasta do backup que quer restaurar: 
  set PASTA=backups\!NOME!
)
python restaurar_backup.py "%PASTA%"
echo.
echo Os PDFs e o codigo foram extraidos na pasta restauracao, dentro do sistema.
echo O banco foi restaurado com o nome NOME_DO_BANCO_restaurado.
echo O sistema em uso NAO foi alterado. Veja INSTALACAO_WINDOWS.md, secao Backup, para colocar a copia em uso.
pause
