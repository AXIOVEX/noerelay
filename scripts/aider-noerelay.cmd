@echo off
REM ============================================================
REM NoeRelay Aider Launcher
REM Opens Aider connected to the NoeRelay gateway
REM ============================================================

REM --- Configuration (edit these) ---
set NOERELAY_BASE_URL=http://localhost:8080/v1
set NOERELAY_API_KEY=noerelay-local-development-key-0001
set NOERELAY_MODEL=openai/axiovex-agni
REM --- End Configuration ---

echo Starting Aider with NoeRelay...
echo   Model: %NOERELAY_MODEL%
echo   Base URL: %NOERELAY_BASE_URL%
echo.

set OPENAI_API_BASE=%NOERELAY_BASE_URL%
set OPENAI_API_KEY=%NOERELAY_API_KEY%

aider --model %NOERELAY_MODEL% %*
