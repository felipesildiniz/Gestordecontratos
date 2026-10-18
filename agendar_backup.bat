@echo off
rem Cria a tarefa que faz o backup todo dia as 02:00. Execute como Administrador (botao direito > Executar como administrador).
cd /d "%~dp0"
schtasks /Create /TN "Gestor de Contratos - Backup diario" /TR "\"%~dp0fazer_backup.bat\" auto" /SC DAILY /ST 02:00 /RU SYSTEM /RL HIGHEST /F
if errorlevel 1 (
  echo.
  echo Nao foi possivel criar a tarefa. Abra este arquivo como Administrador.
) else (
  echo.
  echo Tarefa criada: backup todos os dias as 02:00. O computador precisa estar ligado nesse horario.
  echo Para conferir ou mudar o horario, abra o "Agendador de Tarefas" do Windows.
)
pause
