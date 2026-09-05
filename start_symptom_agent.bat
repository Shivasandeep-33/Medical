@echo off
title MediCure AI Symptom & Disease Diagnostic Agent
cd /d "%~dp0\symptom_agent"
echo ====================================================================
echo Starting MediCure AI - Clinical Disease Diagnostic & Triage Agent
echo ====================================================================
set PORT=8001
echo Launching browser at http://127.0.0.1:8001 ...
start http://127.0.0.1:8001
python agent_app.py
pause
