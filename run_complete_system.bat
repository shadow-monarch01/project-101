@echo off
setlocal enabledelayedexpansion
title AI Hiring System - Complete Stack
cd /d "%~dp0"

echo ======================================================================
echo   AI Hiring System - Complete Stack Launcher
echo   Model: Qwen 3.5 (4B) via Ollama -- Backend: FastAPI -- Frontend: Web UI
echo ======================================================================
echo.

:: 1. Check/Start Ollama in Background
where ollama >nul 2>nul
if !errorlevel! equ 0 (
    echo [1/3] Checking Ollama Model Service...
    curl -s http://127.0.0.1:11434/ >nul 2>nul
    if !errorlevel! neq 0 (
        echo Starting Ollama background server...
        start "Ollama Service" /min ollama serve
        timeout /t 2 /nobreak >nul
    ) else (
        echo [*] Ollama server is active on http://127.0.0.1:11434
    )
) else (
    echo [i] Ollama not found in PATH. App will run in Demo Simulation Mode.
)

:: 2. Locate Python Environment
echo.
echo [2/3] Locating Python environment...
set PYTHON_EXE=
if exist "%CD%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
    echo [*] Using local .venv
) else if exist "c:\Users\Ashok kumar S\Desktop\project\llm_bias_detection_project_final_with_bat (1)\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=c:\Users\Ashok kumar S\Desktop\project\llm_bias_detection_project_final_with_bat (1)\.venv\Scripts\python.exe"
    echo [*] Using workspace virtual environment
) else if exist "C:\Users\Ashok kumar S\Desktop\project 101\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=C:\Users\Ashok kumar S\Desktop\project 101\.venv\Scripts\python.exe"
    echo [*] Using project 101 virtual environment
) else (
    where python >nul 2>nul
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python"
        echo [*] Using system Python from PATH
    )
)

if "%PYTHON_EXE%"=="" (
    echo [!] ERROR: Python could not be located.
    echo Please install Python 3.10+ or run 'python -m venv .venv'
    echo.
    pause
    exit /b 1
)

pushd "%~dp0"

start "" "http://127.0.0.1:8000"

echo [i] Press CTRL+C at any time in this window to stop the server.
echo ======================================================================
echo.

"%PYTHON_EXE%" "%~dp0run_app.py"

popd

echo.
echo AI Hiring System stopped.
pause
