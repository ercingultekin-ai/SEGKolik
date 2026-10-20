@echo off
chcp 65001 >nul
title Türkiye Spor Sonuçları - Hemen Çalıştır
echo [INFO] Türkiye Spor Sonuçları Raporu Başlatılıyor...

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYCMD=python
) else (
    set PYCMD="C:\Users\egultekin\AppData\Local\Programs\Python\Python312\python.exe"
)

%PYCMD% main.py --now
echo.
pause
