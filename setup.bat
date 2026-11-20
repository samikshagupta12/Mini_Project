@echo off
title AI Interview Preparation System - Windows Setup
cls
echo ============================================================
echo   AI-POWERED TECHNICAL INTERVIEW PREPARATION SYSTEM
echo   Automated Environment Setup & Dependency Installation
echo ============================================================
echo.

:: 1. Verify Python Installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not detected in your system PATH.
    echo Please install Python 3.10 or higher from https://www.python.org
    echo Make sure to check the box: "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [1/4] Python interpreter detected:
python --version
echo.

:: 2. Initialize Environment Configuration (.env)
echo [2/4] Initializing environment configuration (.env)...
if not exist .env (
    copy .env.example .env >nul
    echo       Created .env from .env.example (Demo Mode enabled by default).
) else (
    echo       Existing .env configuration preserved.
)
echo.

:: 3. Install Locked Dependencies
echo [3/4] Installing third-party Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies encountered an issue during installation.
    echo Retrying with relaxed flags...
    python -m pip install -r requirements.txt --no-warn-script-location
)
echo.

:: 4. Verify & Train Decision Tree Model Artifacts
echo [4/4] Verifying Machine Learning Model artifacts (CART Decision Tree)...
python -m ml.train_model
echo.

echo ============================================================
echo   SETUP COMPLETE!
echo ============================================================
echo   The system is configured in Demo Mode (In-Memory Database).
echo   You do NOT need to install or configure MongoDB!
echo.
echo   To launch the application:
echo   Double-click: run.bat
echo   Or in terminal run: python -m streamlit run app.py
echo ============================================================
echo.
pause
