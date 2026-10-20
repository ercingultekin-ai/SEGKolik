@echo off
chcp 65001 >nul
title Türkiye Spor Sonuçları - Test Modu
echo [INFO] Test Raporu Çalıştırılıyor (E-posta gönderilmez, HTML üretilir)...

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYCMD=python
) else (
    set PYCMD="C:\Users\egultekin\AppData\Local\Programs\Python\Python312\python.exe"
)

%PYCMD% main.py --test
echo.
echo [INFO] Sonuç HTML dosyası 'preview_report.html' olarak kaydedildi.
pause
