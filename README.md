# PlantOps Simulator

FastAPI/Jinja/CSS plant operations simulator for feed mill / grain handling style workflows.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/dashboard
```

## Demo login

```text
owner / plantops
```

## Main features

- Live dashboard and process flow.
- In-memory plant simulation engine.
- Equipment control actions.
- Alarm acknowledgement.
- LOTO workflow.
- Fault injection.
- SQLite database history.
- Reports and CSV export.
- Plant configuration page.
- Demo login, session cookie, TOTP setup support.
- Audit log.
- Diagnostics page.
- Scenario Builder.
- Historical Playback.
- WebSocket `/ws/state` live updates.

## Smoke check

Start the server first, then run:

```bash
python3 scripts/smoke_check.py
```

## Project tree without noisy folders

```bash
bash scripts/project_tree.sh
```

## Docker

```bash
docker compose up --build
```

## Docs

- `docs/OPERATIONS_GUIDE.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/PROJECT_STATUS.md`
