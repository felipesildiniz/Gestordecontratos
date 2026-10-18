@echo off
rem Faz o backup do banco, dos PDFs e do codigo. Uso: fazer_backup.bat  (ou "fazer_backup.bat auto", sem pausa)
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo O ambiente ainda nao foi criado. Execute criar_ambiente.bat primeiro.
  if not "%1"=="auto" pause
  exit /b 1
)
call .venv\Scripts\activate
if not exist backups mkdir backups
python fazer_backup.py > backups\ultimo_backup.txt 2>&1
set RESULTADO=%errorlevel%
type backups\ultimo_backup.txt
echo ===== %date% %time% - codigo %RESULTADO% ===== >> backups\backup.log
type backups\ultimo_backup.txt >> backups\backup.log
echo.
if "%RESULTADO%"=="0" echo BACKUP OK.
if "%RESULTADO%"=="2" echo BACKUP FEITO, MAS COM ATENCAO: leia as mensagens acima.
if "%RESULTADO%"=="1" echo BACKUP FALHOU. Copie as mensagens acima e envie para suporte.
if not "%1"=="auto" pause
exit /b %RESULTADO%
