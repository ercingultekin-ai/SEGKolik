@echo off
chcp 65001 >nul
title Türkiye Spor Sonuçları - Demo Raporu
echo [INFO] Örnek maç verileri ile demo e-posta raporu oluşturuluyor...

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYCMD=python
) else (
    set PYCMD="C:\Users\egultekin\AppData\Local\Programs\Python\Python312\python.exe"
)

%PYCMD% main.py --demo
echo.
echo [INFO] preview_report.html dosyasını herhangi bir web tarayıcısında açarak sonucu görebilirsiniz.
pause
