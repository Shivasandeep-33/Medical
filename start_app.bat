@echo off
title MediSync AI Server
cd /d "%~dp0"
echo ===================================================
echo Starting MediSync AI Clinical Medical Record Server
echo ===================================================
echo Opening browser at http://127.0.0.1:8000 ...
start http://127.0.0.1:8000
python app.py
pause
