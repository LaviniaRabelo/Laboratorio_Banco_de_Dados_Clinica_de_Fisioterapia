@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe goto configurar
if not exist .env goto configurar
echo Abra http://127.0.0.1:5000 no navegador quando o servidor iniciar.
echo Mantenha esta janela aberta. Para encerrar, pressione Ctrl+C.
.venv\Scripts\python.exe app.py
pause
exit /b
:configurar
echo Execute configurar.bat primeiro.
pause
