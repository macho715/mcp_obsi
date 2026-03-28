#!/usr/bin/env bash
set -euo pipefail

if [ ! -f ".venv/bin/activate" ]; then
  echo "가상환경이 없습니다. 먼저 python -m venv .venv 를 실행하세요."
  exit 1
fi

source .venv/bin/activate
export PYTHONPATH="$(pwd)"

python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
