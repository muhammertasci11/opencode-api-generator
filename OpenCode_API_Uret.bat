@echo off
title OpenCode Otomatik API Key Uretici
echo ========================================================
echo   OpenCode Otomatik Hesap ve API Key Olusturucu
echo ========================================================
echo.
python "%~dp0auto_opencode_apikey.py"
echo.
echo Islem bitti! Terminal 3 saniye sonra otomatik kapanacak...
timeout /t 3 /nobreak >nul
exit
