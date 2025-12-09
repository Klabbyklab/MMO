# MMO – Material & Moisture Observer

Web app + Google Sheets logger for analyzing building/structure photos.

## Local dev

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

export APPS_SCRIPT_WEBHOOK_URL="https://script.google.com/macros/s/AKfycbxXrQBud-llIMQPLgDqSq882kZ8DXLvDjAFFXMp7bl-JDEgdEs2jdW0RuB-9jNm8NSnPQ/exec"
uvicorn app.main:app --reload
