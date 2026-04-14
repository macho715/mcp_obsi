@echo off
setlocal
cd /d "%~dp0.."
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
if defined OBSIDIAN_LOCAL_VAULT_PATH set "VAULT_PATH=%OBSIDIAN_LOCAL_VAULT_PATH%"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
