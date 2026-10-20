@echo off
chcp 65001 >nul
title SEG_Mackolik - Web Arayuzu
cd /d "C:\Users\egultekin\OneDrive - Borusan\Desktop\Deneme Antigravity"
"C:\Users\egultekin\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
pause
