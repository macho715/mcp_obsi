@echo off
setlocal

cd /d "%~dp0"

if not exist "dist\cli.js" (
  echo dist\cli.js not found. Run build.bat first.
  exit /b 1
)

if "%MYAGENT_PROXY_CORS_ORIGINS%"=="" (
  echo MYAGENT_PROXY_CORS_ORIGINS is required.
  exit /b 1
)

if "%MYAGENT_PROXY_AUTH_TOKEN%"=="" (
  echo MYAGENT_PROXY_AUTH_TOKEN is required.
  exit /b 1
)

if "%MYAGENT_PROXY_HOST%"=="" set MYAGENT_PROXY_HOST=0.0.0.0
if "%MYAGENT_PROXY_PORT%"=="" set MYAGENT_PROXY_PORT=3010
if "%MYAGENT_PROXY_OPS_LOGS%"=="" set MYAGENT_PROXY_OPS_LOGS=1
if "%MYAGENT_PROXY_ALLOW_SANITIZED_TO_COPILOT%"=="" set MYAGENT_PROXY_ALLOW_SANITIZED_TO_COPILOT=0
if "%MYAGENT_LOCAL_RAG_TOKEN%"=="" if not "%LOCAL_RAG_SHARED_SECRET%"=="" set MYAGENT_LOCAL_RAG_TOKEN=%LOCAL_RAG_SHARED_SECRET%
if "%MYAGENT_HVDC_PREDICT_ENABLED%"=="" set MYAGENT_HVDC_PREDICT_ENABLED=1
if "%MYAGENT_HVDC_PREDICT_DIR%"=="" if exist "..\..\predict\predict2.py" for %%I in ("%~dp0..\..\predict") do set MYAGENT_HVDC_PREDICT_DIR=%%~fI
if "%MYAGENT_HVDC_PREDICT_PYTHON%"=="" if exist "..\..\predict\.venv\Scripts\python.exe" for %%I in ("%~dp0..\..\predict\.venv\Scripts\python.exe") do set MYAGENT_HVDC_PREDICT_PYTHON=%%~fI

echo Starting standalone on %MYAGENT_PROXY_HOST%:%MYAGENT_PROXY_PORT%
echo Public origin allowlist: %MYAGENT_PROXY_CORS_ORIGINS%
if "%MYAGENT_LOCAL_RAG_TOKEN%"=="" (
  echo local-rag guard: disabled
) else (
  echo local-rag guard: enabled
)
if "%MYAGENT_HVDC_PREDICT_ENABLED%"=="0" (
  echo HVDC predict: disabled
) else (
  echo HVDC predict dir : %MYAGENT_HVDC_PREDICT_DIR%
  echo HVDC predict py  : %MYAGENT_HVDC_PREDICT_PYTHON%
)

node dist\cli.js serve --host %MYAGENT_PROXY_HOST% --port %MYAGENT_PROXY_PORT%
