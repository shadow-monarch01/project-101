@echo off
title Ollama Model Runner - Qwen 3.5 4B (AI Hiring System)
cd /d "%~dp0"

echo ======================================================================
echo   Ollama Model Runner - Qwen 3.5 (4B) for AI Hiring Intelligence
echo ======================================================================
echo.

:: Check if Ollama is installed
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        set "PATH=%LOCALAPPDATA%\Programs\Ollama;%PATH%"
    ) else (
        echo [!] Ollama was not found in PATH or standard install location.
        echo Please download and install Ollama from: https://ollama.com/download
        echo.
        echo Note: The AI Hiring System web app will continue running in
        echo Demo Simulation Mode even if Ollama is not installed.
        echo.
        pause
        exit /b 1
    )
)

echo [1/3] Checking Ollama Service Status on http://127.0.0.1:11434 ...
curl -s http://127.0.0.1:11434/ >nul 2>nul
if %errorlevel% neq 0 (
    echo [2/3] Starting Ollama Server in background...
    start "Ollama Service" /min ollama serve
    timeout /t 3 /nobreak >nul
) else (
    echo [?] Ollama Server is already running.
)

echo [3/3] Initializing model 'qwen3.5:4b'...
echo (If already downloaded, this will verify and run immediately)
echo.

ollama pull qwen3.5:4b

echo.
echo ======================================================================
echo [?] Model 'qwen3.5:4b' is ready!
echo Ollama API is active at: http://127.0.0.1:11434
echo.
echo You can now use this model in the AI Hiring System web application.
echo ======================================================================
echo.
echo Testing model prompt response...
ollama run qwen3.5:4b "Say 'Qwen 3.5 4B is active and ready for AI Hiring Intelligence bias analysis.'"

echo.
pause
