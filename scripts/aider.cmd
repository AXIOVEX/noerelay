@echo off
REM Start Aider against the local OpenAI-compatible endpoint.
REM Usage: scripts\aider.cmd [extra aider args...]
setlocal

set "AIDER_MODEL=openai/axiovex-agni"
set "AIDER_API_BASE=http://localhost:8080/v1"
set "AIDER_API_KEY=noerelay-local-development-key-0001"

where python >nul 2>nul
if errorlevel 1 (
    echo Python is not on PATH.
    exit /b 1
)

python "%~dp0aider_noerelay.py" --model "%AIDER_MODEL%" --openai-api-base "%AIDER_API_BASE%" --openai-api-key "%AIDER_API_KEY%" --no-show-model-warnings %*

endlocal & exit /b %ERRORLEVEL%
