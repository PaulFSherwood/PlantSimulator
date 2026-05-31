# PlantOps Simulator

A no-npm FastAPI/Jinja2 first draft for a web-based plant operations simulator.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

## Design decisions

- No npm / React / frontend build chain.
- Shared external CSS in `app/static/css/plantops.css`.
- Shared JavaScript in `app/static/js/plantops.js`.
- Shared SVG icons in `app/static/icons/`.
- All pages inherit from `templates/base.html`.
- This draft uses placeholder demo data. PostgreSQL models come next.

## Included pages

- Owner Dashboard
- Process Flow
- Production
- Equipment
- Alarms
- Trends
- Maintenance
- Lockout / Tagout
- Parts & Reliability
- Fault Tuning
- Training Scenarios
- Reports
- I/O Monitor
- Farmer Display
- Plant Configuration
- Help
