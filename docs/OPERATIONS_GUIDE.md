# PlantOps Operations Guide

## Run locally

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/dashboard`.

## Demo login

Username: `owner`  
Password: `plantops`

## Daily workflow

1. Dashboard: watch profit, production, alarms, and bottleneck.
2. Process Flow: watch material movement through receiving, dryer, bins, mixer, and packaging.
3. Equipment: start/stop/lockout equipment.
4. Alarms: acknowledge active alarms.
5. Scenarios: start training/fault scenarios.
6. Reports and Playback: review database-backed history.
7. Diagnostics: run readiness checks.

## Useful APIs

- `/api/state`
- `/ws/state`
- `/api/health`
- `/api/scenarios`
- `/api/playback/summary`
- `/api/reports/daily`
- `/reports/export.csv`
