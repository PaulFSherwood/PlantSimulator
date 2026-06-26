from __future__ import annotations

import asyncio

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response

from app.core.logging_config import configure_logging
from app.core.version import APP_VERSION
from app.services.auth import SESSION_COOKIE, auth_service
from app.services.db_store import db
from app.services.diagnostics import diagnostics_service
from app.services.playback import playback_service
from app.services.scenario_service import scenario_service
from app.services.plant_config import get_plant_context
from app.sim.engine import plant_sim

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
    {"label": "Scenario Builder", "endpoint": "/scenarios", "icon": "training"},
    {"label": "Playback", "endpoint": "/playback", "icon": "trends"},
    {"label": "Reports", "endpoint": "/reports", "icon": "reports"},
    {"label": "I/O Monitor", "endpoint": "/io-monitor", "icon": "io"},
    {"label": "Farmer Display", "endpoint": "/farmer-display", "icon": "farmer"},
    {"label": "Plant Configuration", "endpoint": "/plant-config", "icon": "settings"},
    {"label": "Diagnostics", "endpoint": "/diagnostics", "icon": "help"},
    {"label": "Help", "endpoint": "/help", "icon": "help"},
]

PAGE_DATA = {
    "/dashboard": {"title": "Owner Dashboard", "subtitle": "Daily profit, production, downtime, and risk overview.", "template": "dashboard.html"},
    "/process-flow": {"title": "Process Flow", "subtitle": "Live simulated grain receiving, drying, storage, and packaging flow.", "template": "process_flow.html"},
    "/production": {"title": "Production", "subtitle": "Target vs actual output, bottlenecks, throughput, and shift status.", "template": "production.html"},
    "/equipment": {"title": "Equipment", "subtitle": "Equipment health, sensor values, runtime, and fault status.", "template": "equipment.html"},
    "/alarms": {"title": "Alarms", "subtitle": "Active alarms, acknowledgements, severity, and event age.", "template": "alarms.html"},
    "/trends": {"title": "Trends", "subtitle": "Sensor history, production curves, downtime, and energy trends.", "template": "trends.html"},
    "/maintenance": {"title": "Maintenance", "subtitle": "Work orders, preventive maintenance, and repair history.", "template": "maintenance.html"},
    "/loto": {"title": "Lockout / Tagout", "subtitle": "Track safe isolation, verification, maintenance, and return-to-service workflow.", "template": "loto.html"},
    "/parts": {"title": "Parts & Reliability", "subtitle": "Part life, vendor reliability, cost tradeoffs, and failure history.", "template": "parts.html"},
    "/fault-tuning": {"title": "Fault Tuning", "subtitle": "Senior maintenance tuning for realistic breakage and downtime behavior.", "template": "fault_tuning.html"},
    "/training": {"title": "Training Scenarios", "subtitle": "Operator and maintenance troubleshooting drills.", "template": "training.html"},
    "/scenarios": {"title": "Scenario Builder", "subtitle": "Start realistic operating, fault, and training scenarios.", "template": "scenarios.html"},
    "/playback": {"title": "Historical Playback", "subtitle": "Review recent simulated production and alarm history.", "template": "playback.html"},
    "/reports": {"title": "Reports", "subtitle": "Daily summaries for production, downtime, safety, maintenance, and profit.", "template": "reports.html"},
    "/io-monitor": {"title": "I/O Monitor", "subtitle": "Virtual inputs, outputs, sensor registers, and command states.", "template": "io_monitor.html"},
    "/farmer-display": {"title": "Farmer Intake Display", "subtitle": "Read-only intake board for farmers and truck drivers.", "template": "farmer_display.html", "kiosk": True},
    "/plant-config": {"title": "Plant Configuration", "subtitle": "Plant layout, equipment definitions, thresholds, users, and security settings.", "template": "plant_config.html"},
    "/diagnostics": {"title": "Diagnostics", "subtitle": "Health checks, route checks, database status, and release readiness.", "template": "diagnostics.html"},
    "/help": {"title": "Help", "subtitle": "Project guide, role map, safety notes, and first-use instructions.", "template": "help.html"},
}


class SimSpeedRequest(BaseModel):
    speed: float


class EquipmentActionRequest(BaseModel):
    reason: str | None = None


class FaultRequest(BaseModel):
    equipment_id: str
    severity: str = "high"


def _current_state_recorded() -> dict:
    state = plant_sim.snapshot()
    db.record_snapshot_once(state)
    return state


def build_template_context(request: Request, endpoint: str, page: dict | None) -> dict:
    state = _current_state_recorded()
    current_user = auth_service.get_user_from_request(request)
    report = db.daily_report()
    return {
        "request": request,
        "nav_items": NAV_ITEMS,
        "active_path": endpoint,
        "page": page,
        "sim_state": state,
        "current_user": current_user,
        "security": {
            "users": db.list_users(),
            "audit": db.recent_audit(12),
            "default_login_hint": "owner / plantops",
        },
        "db_summary": db.summary(),
        "report_summary": report,
        "diagnostics": diagnostics_service.summary(),
        "scenarios": scenario_service.list_scenarios(),
        "playback": playback_service.summary(),
        "plant_config": db.get_active_plant_config(),
        **get_plant_context("feed_mill"),
    }


@app.on_event("startup")
def start_services() -> None:
    configure_logging()
    db.initialize()
    auth_service.ensure_seed_user()
    cfg = db.get_active_plant_config()
    plant_sim.update_plant_profile(
        cfg.get("name", "Demo Feed Mill"),
        cfg.get("operations", {}).get("status", "Receiving Open"),
        cfg.get("operations", {}).get("shift", "Day Shift"),
    )
    db.audit("system", "app.startup", "PlantOps")
    plant_sim.start()


@app.on_event("shutdown")
def stop_services() -> None:
    db.audit("system", "app.shutdown", "PlantOps")
    plant_sim.stop()


@app.get("/api/state")
def api_state():
    return _current_state_recorded()


@app.post("/api/sim/pause")
def api_sim_pause(request: Request):
    state = plant_sim.pause()
    db.audit(auth_service.audit_name(request), "sim.pause")
    db.record_snapshot_once(state)
    return state


@app.post("/api/sim/resume")
def api_sim_resume(request: Request):
    state = plant_sim.resume()
    db.audit(auth_service.audit_name(request), "sim.resume")
    db.record_snapshot_once(state)
    return state


@app.post("/api/sim/reset")
def api_sim_reset(request: Request):
    state = plant_sim.reset()
    db.audit(auth_service.audit_name(request), "sim.reset")
    db.record_snapshot_once(state)
    return state


@app.post("/api/sim/speed")
def api_sim_speed(payload: SimSpeedRequest, request: Request):
    state = plant_sim.set_speed(payload.speed)
    db.audit(auth_service.audit_name(request), "sim.speed", details={"speed": payload.speed})
    db.record_snapshot_once(state)
    return state


@app.post("/api/equipment/{equipment_id}/{action}")
def api_equipment_action(equipment_id: str, action: str, request: Request, payload: EquipmentActionRequest | None = None):
    reason = payload.reason if payload else None
    state = plant_sim.equipment_action(equipment_id, action, reason)
    db.audit(auth_service.audit_name(request), f"equipment.{action}", equipment_id, {"reason": reason})
    db.record_snapshot_once(state)
    return state


@app.post("/api/alarms/{alarm_id}/ack")
def api_alarm_ack(alarm_id: str, request: Request):
    state = plant_sim.acknowledge_alarm(alarm_id)
    db.audit(auth_service.audit_name(request), "alarm.ack", alarm_id)
    db.record_snapshot_once(state)
    return state


@app.post("/api/faults/inject")
def api_inject_fault(payload: FaultRequest, request: Request):
    state = plant_sim.inject_fault(payload.equipment_id, payload.severity)
    db.audit(auth_service.audit_name(request), "fault.inject", payload.equipment_id, {"severity": payload.severity})
    db.record_snapshot_once(state)
    return state


@app.get("/api/db/summary")
def api_db_summary():
    return db.summary()


@app.get("/api/audit")
def api_audit():
    return {"audit": db.recent_audit(100)}


@app.get("/api/reports/daily")
def api_report_daily():
    report = db.daily_report()
    db.save_report_snapshot(report)
    return report


@app.get("/reports/export.csv")
def report_export_csv():
    csv_text = db.report_csv()
    return Response(
        csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=plantops_daily_report.csv"},
    )


@app.get("/login")
def login_page(request: Request):
    context = build_template_context(request, "/login", {"title": "Login", "subtitle": "Demo local authentication.", "template": "login.html"})
    return templates.TemplateResponse("login.html", context)


@app.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    username = str(form.get("username", "")).strip()
    password = str(form.get("password", ""))
    totp_code = str(form.get("totp_code", "")).strip() or None
    ok, message, user = auth_service.authenticate(username, password, totp_code)
    if not ok or user is None:
        context = build_template_context(request, "/login", {"title": "Login", "subtitle": "Demo local authentication.", "template": "login.html"})
        context["login_error"] = message
        return templates.TemplateResponse("login.html", context, status_code=401)
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(SESSION_COOKIE, auth_service.login(username), httponly=True, samesite="lax", max_age=7 * 24 * 60 * 60)
    return response


@app.post("/logout")
def logout(request: Request):
    auth_service.logout(request)
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/api/auth/me")
def api_auth_me(request: Request):
    return {"user": auth_service.get_user_from_request(request)}


@app.post("/api/auth/totp/setup")
def api_totp_setup(request: Request):
    user = auth_service.get_user_from_request(request)
    if not user.get("authenticated"):
        return {"error": "Login required."}
    secret = auth_service.generate_totp_secret()
    from app.services.db_store import db as _db
    _db.update_user_totp(user["username"], secret, False)
    uri = auth_service.totp_uri(user["username"], secret)
    _db.audit(user["username"], "auth.totp.setup", user["username"])
    return {"secret": secret, "uri": uri, "message": "Add this secret to your authenticator, then verify a code."}


@app.post("/api/auth/totp/verify")
async def api_totp_verify(request: Request):
    user = auth_service.get_user_from_request(request)
    if not user.get("authenticated"):
        return {"error": "Login required."}
    form = await request.form()
    code = str(form.get("code", "")).strip()
    db_user = db.get_user(user["username"])
    if db_user and auth_service.verify_totp(db_user.get("totp_secret") or "", code):
        db.update_user_totp(user["username"], db_user.get("totp_secret"), True)
        db.audit(user["username"], "auth.totp.enabled", user["username"])
        return RedirectResponse("/plant-config", status_code=303)
    return PlainTextResponse("Invalid TOTP code", status_code=400)


@app.post("/plant-config/save")
async def plant_config_save(request: Request):
    form = await request.form()
    username = auth_service.audit_name(request)
    name = str(form.get("name", "Demo Feed Mill"))
    plant_type = str(form.get("plant_type", "Feed Mill"))
    status = str(form.get("status", "Receiving Open"))
    shift = str(form.get("shift", "Day Shift"))
    cfg = db.update_plant_profile(name, plant_type, status, shift, username=username)
    plant_sim.update_plant_profile(
        cfg.get("name", name),
        cfg.get("operations", {}).get("status", status),
        cfg.get("operations", {}).get("shift", shift),
    )
    return RedirectResponse("/plant-config", status_code=303)




@app.middleware("http")
async def add_reliability_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-PlantOps-Version"] = APP_VERSION
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    db.audit(auth_service.audit_name(request), "app.exception", str(request.url.path), {"error": str(exc)[:500]})
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "path": str(request.url.path),
            "detail": "Check server log for traceback.",
        },
    )


@app.get("/api/version")
def api_version():
    return {"version": APP_VERSION, "app": "PlantOps Simulator"}


@app.get("/api/health")
def api_health():
    return diagnostics_service.health()


@app.get("/api/diagnostics")
def api_diagnostics():
    return diagnostics_service.summary()


@app.get("/api/playback/summary")
def api_playback_summary():
    return playback_service.summary()


@app.get("/api/playback/production")
def api_playback_production(limit: int = 120):
    return {"samples": playback_service.production_samples(limit=limit)}


@app.get("/api/plant-config/export.json")
def api_plant_config_export():
    return db.get_active_plant_config()


@app.get("/api/scenarios")
def api_scenarios():
    return {"scenarios": scenario_service.list_scenarios()}


@app.post("/api/scenarios/{scenario_id}/start")
def api_scenario_start(scenario_id: str, request: Request):
    actor = auth_service.audit_name(request)
    result = scenario_service.start_scenario(scenario_id, actor=actor)
    state = result.get("state", plant_sim.snapshot())
    db.record_snapshot_once(state)
    return result


@app.websocket("/ws/state")
async def websocket_state(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(plant_sim.snapshot())
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        return

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
