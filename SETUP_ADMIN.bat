@echo off
cd /d "%~dp0"
title JA Detailing - Admin setup
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" tools\setup_admin.py
) else (
  python tools\setup_admin.py
)
pause
