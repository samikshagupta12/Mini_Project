@echo off
title AI Interview Preparation System
cls
echo ============================================================
echo   LAUNCHING AI-POWERED INTERVIEW PREPARATION SYSTEM
echo ============================================================
echo.
echo   Storage Mode: In-Memory Demo Mode (mongomock Active)
echo   Local MongoDB is NOT required.
echo.
echo   Opening Streamlit Application at http://localhost:8501...
echo   Press Ctrl + C in this terminal to stop the application.
echo.
echo ============================================================
echo.

python -m streamlit run app.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application terminated unexpectedly.
    echo Please ensure setup.bat has been executed first.
    pause
)
