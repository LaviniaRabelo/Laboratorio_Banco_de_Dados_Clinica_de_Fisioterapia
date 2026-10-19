@echo off
cd /d "%~dp0"
py -3 --version
if errorlevel 1 goto erro
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
if errorlevel 1 goto erro
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto erro
.venv\Scripts\python.exe configurar.py
if errorlevel 1 goto erro
echo.
echo Depois da configuracao, abra iniciar.bat.
pause
exit /b 0
:erro
echo.
echo A configuracao nao terminou. Confira a mensagem acima.
echo Se o comando py nao existir, instale Python 3.11 ou superior.
pause
exit /b 1
