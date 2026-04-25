@echo off
echo ==============================================
echo    VELLI PROSPECT V3 - Iniciando...
echo    Aguarde! O aplicativo vai abrir em instantes.
echo ==============================================

cd /d "%~dp0"

:: Corrige SSL para Python da Microsoft Store
for /f "delims=" %%i in ('python -c "import certifi; print(certifi.where())"') do set SSL_CERT_FILE=%%i

echo [1/2] Verificando dependencias...
pip install -r requirements.txt -q 2>nul

echo [2/2] Abrindo Velli Prospect V3...
python main.py
pause
