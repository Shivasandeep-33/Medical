@echo off
title MedLens AI Healthcare Platform Server
cd /d "%~dp0"
echo =========================================================================
echo Starting MedLens AI-Powered Clinical Intelligence & Healthcare Portal
echo =========================================================================
echo Server starting on http://127.0.0.1:8000 ...
start http://127.0.0.1:8000
python app.py
pause
