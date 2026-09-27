@echo off
cd /d "%~dp0"
title JA Detailing London

if not exist "streamlit_app.py" (
  echo ERROR: START.bat must be inside the JA Detail folder next to streamlit_app.py
  pause
  exit /b
)

if not exist ".venv\Scripts\python.exe" (
  echo ============================================
  echo  First run - setting up. This takes 1-3 minutes.
  echo ============================================
  python -m venv .venv
  if errorlevel 1 (
    echo.
    echo Python was not found. Install it from https://www.python.org/downloads/
    echo and TICK "Add python.exe to PATH" during installation, then try again.
    pause
    exit /b
  )
)

".venv\Scripts\python.exe" -c "import streamlit, reportlab, pandas, altair" >nul 2>&1
if errorlevel 1 (
  echo Installing required packages...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Installing packages failed - check your internet connection and try again.
    pause
    exit /b
  )
)

echo.
echo ==========================================================
echo  JA Detailing London is starting...
echo  On THIS computer:  http://localhost:8501
echo  On your PHONE (same Wi-Fi): use the "Network URL" shown below
echo  Admin:             http://localhost:8501/admin
echo  Keep this window open. Close it to stop the website.
echo ==========================================================
echo.
".venv\Scripts\python.exe" -m streamlit run streamlit_app.py
pause
