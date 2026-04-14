@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo .venv is missing. Create it first and install dependencies.
  exit /b 1
)

if "%LOCAL_RAG_MODEL%"=="" set LOCAL_RAG_MODEL=gemma4:e4b
if "%LOCAL_RAG_DOCS_DIR%"=="" set LOCAL_RAG_DOCS_DIR=C:\Users\jichu\Downloads\valut\wiki
if "%LOCAL_RAG_CACHE_PATH%"=="" set LOCAL_RAG_CACHE_PATH=.cache\retrieval-cache.json
if "%LOCAL_RAG_HOST%"=="" set LOCAL_RAG_HOST=127.0.0.1
if "%LOCAL_RAG_PORT%"=="" set LOCAL_RAG_PORT=8010

if /I not "%LOCAL_RAG_HOST%"=="127.0.0.1" if /I not "%LOCAL_RAG_HOST%"=="localhost" if "%LOCAL_RAG_SHARED_SECRET%"=="" (
  echo LOCAL_RAG_SHARED_SECRET is required when binding beyond loopback.
  exit /b 1
)

echo Starting local-rag on %LOCAL_RAG_HOST%:%LOCAL_RAG_PORT%
echo Model   : %LOCAL_RAG_MODEL%
echo Docs dir: %LOCAL_RAG_DOCS_DIR%
echo Cache   : %LOCAL_RAG_CACHE_PATH%
if "%LOCAL_RAG_SHARED_SECRET%"=="" (
  echo Guard   : disabled
) else (
  echo Guard   : enabled
)

".venv\Scripts\python.exe" -m uvicorn app.main:app --host %LOCAL_RAG_HOST% --port %LOCAL_RAG_PORT%
