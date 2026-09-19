@echo off
setlocal enabledelayedexpansion
title AI Hiring Intelligence Dashboard
cd /d "%~dp0"

echo ======================================================================
echo   AI Hiring Intelligence and Bias Mitigation System
echo   Qualification-Based Assessment - Faithfulness (EFS) - Gap Analysis (BGI)
echo ======================================================================
echo.

:: 1. Locate Python Environment (Local .venv, Workspace .venv, or System Python)
set PYTHON_EXE=
if exist "%CD%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
    echo [*] Found local virtual environment: .venv
) else if exist "c:\Users\Ashok kumar S\Desktop\project\llm_bias_detection_project_final_with_bat (1)\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=c:\Users\Ashok kumar S\Desktop\project\llm_bias_detection_project_final_with_bat (1)\.venv\Scripts\python.exe"
    echo [*] Found workspace virtual environment
) else if exist "C:\Users\Ashok kumar S\Desktop\project 101\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=C:\Users\Ashok kumar S\Desktop\project 101\.venv\Scripts\python.exe"
    echo [*] Found project 101 virtual environment
) else (
    where python >nul 2>nul
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python"
        echo [*] Using system Python from PATH
    )
)

if "%PYTHON_EXE%"=="" (
    echo [!] ERROR: Python could not be located.
    echo Please install Python 3.10+ or run "python -m venv .venv"
    echo.
    pause
    exit /b 1
)

:: 2. Launch FastAPI Backend and Browser
echo.
echo [*] Starting FastAPI Backend on http://127.0.0.1:8000 ...
echo [*] Opening Dashboard in your default web browser...
echo [i] If browser does not open automatically, visit: http://127.0.0.1:8000
echo [i] Press CTRL+C at any time in this window to stop the server.
echo ======================================================================
echo.

pushd "%~dp0"

start "" "http://127.0.0.1:8000"

"%PYTHON_EXE%" "%~dp0run_app.py"

popd

echo.
echo AI Hiring System server stopped.
pause
