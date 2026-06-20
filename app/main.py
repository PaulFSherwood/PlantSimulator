from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

from app.services.plant_config import get_plant_context

app = FastAPI(title="PlantOps Simulator")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

NAV_ITEMS = [
    {"label": "Owner Dashboard", "endpoint": "/dashboard", "icon": "dashboard"},
    {"label": "Process Flow", "endpoint": "/process-flow", "icon": "process"},
    {"label": "Production", "endpoint": "/production", "icon": "production"},
    {"label": "Equipment", "endpoint": "/equipment", "icon": "equipment"},
    {"label": "Alarms", "endpoint": "/alarms", "icon": "alarms"},
    {"label": "Trends", "endpoint": "/trends", "icon": "trends"},
    {"label": "Maintenance", "endpoint": "/maintenance", "icon": "maintenance"},
    {"label": "Lockout / Tagout", "endpoint": "/loto", "icon": "loto"},
    {"label": "Parts & Reliability", "endpoint": "/parts", "icon": "parts"},
    {"label": "Fault Tuning", "endpoint": "/fault-tuning", "icon": "fault"},
    {"label": "Training Scenarios", "endpoint": "/training", "icon": "training"},
    {"label": "Reports", "endpoint": "/reports", "icon": "reports"},
    {"label": "I/O Monitor", "endpoint": "/io-monitor", "icon": "io"},
    {"label": "Farmer Display", "endpoint": "/farmer-display", "icon": "farmer"},
    {"label": "Plant Configuration", "endpoint": "/plant-config", "icon": "settings"},
    {"label": "Help", "endpoint": "/help", "icon": "help"},
]

PAGE_DATA = {
    "/dashboard": {
        "title": "Owner Dashboard",
        "subtitle": "Daily profit, production, downtime, and risk overview.",
        "template": "dashboard.html",
    },
    "/process-flow": {
        "title": "Process Flow",
        "subtitle": "Live simulated grain receiving, drying, storage, and packaging flow.",
        "template": "process_flow.html",
    },
    "/production": {
        "title": "Production",
        "subtitle": "Target vs actual output, bottlenecks, throughput, and shift status.",
        "template": "production.html",
    },
    "/equipment": {
        "title": "Equipment",
        "subtitle": "Equipment health, sensor values, runtime, and fault status.",
        "template": "equipment.html",
    },
    "/alarms": {
        "title": "Alarms",
        "subtitle": "Active alarms, acknowledgements, severity, and event age.",
        "template": "alarms.html",
    },
    "/trends": {
        "title": "Trends",
        "subtitle": "Sensor history, production curves, downtime, and energy trends.",
        "template": "trends.html",
    },
    "/maintenance": {
        "title": "Maintenance",
        "subtitle": "Work orders, preventive maintenance, and repair history.",
        "template": "maintenance.html",
    },
    "/loto": {
        "title": "Lockout / Tagout",
        "subtitle": "Track safe isolation, verification, maintenance, and return-to-service workflow.",
        "template": "loto.html",
    },
    "/parts": {
        "title": "Parts & Reliability",
        "subtitle": "Part life, vendor reliability, cost tradeoffs, and failure history.",
        "template": "parts.html",
    },
    "/fault-tuning": {
        "title": "Fault Tuning",
        "subtitle": "Senior maintenance tuning for realistic breakage and downtime behavior.",
        "template": "fault_tuning.html",
    },
    "/training": {
        "title": "Training Scenarios",
        "subtitle": "Operator and maintenance troubleshooting drills.",
        "template": "training.html",
    },
    "/reports": {
        "title": "Reports",
        "subtitle": "Daily summaries for production, downtime, safety, maintenance, and profit.",
        "template": "reports.html",
    },
    "/io-monitor": {
        "title": "I/O Monitor",
        "subtitle": "Virtual inputs, outputs, sensor registers, and command states.",
        "template": "io_monitor.html",
    },
    "/farmer-display": {
        "title": "Farmer Intake Display",
        "subtitle": "Read-only intake board for farmers and truck drivers.",
        "template": "farmer_display.html",
        "kiosk": True,
    },
    "/plant-config": {
        "title": "Plant Configuration",
        "subtitle": "Plant layout, equipment definitions, thresholds, users, and security settings.",
        "template": "plant_config.html",
    },
    "/help": {
        "title": "Help",
        "subtitle": "Project guide, role map, safety notes, and first-use instructions.",
        "template": "help.html",
    },
}


def build_template_context(request: Request, endpoint: str, page: dict | None) -> dict:
    return {
        "request": request,
        "nav_items": NAV_ITEMS,
        "active_path": endpoint,
        "page": page,
        **get_plant_context("feed_mill"),
    }


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/dashboard")


@app.get("/{page_path:path}")
def render_page(request: Request, page_path: str):
    endpoint = f"/{page_path}" if page_path else "/dashboard"
    page = PAGE_DATA.get(endpoint)

    if page is None:
        context = build_template_context(request, endpoint, None)
        context["title"] = "Not Found"
        return templates.TemplateResponse("not_found.html", context, status_code=404)

    return templates.TemplateResponse(
        page["template"],
        build_template_context(request, endpoint, page),
    )
