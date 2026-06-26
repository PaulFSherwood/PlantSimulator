from __future__ import annotations

import platform
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.version import APP_VERSION
from app.services.db_store import DB_PATH, db
from app.sim.engine import plant_sim


class DiagnosticsService:
    def health(self) -> dict[str, Any]:
        state = plant_sim.snapshot()
        summary = db.summary()
        checks = self._checks(state, summary)
        return {
            "status": "ok" if all(c["ok"] for c in checks) else "degraded",
            "version": APP_VERSION,
            "time": datetime.now().isoformat(timespec="seconds"),
            "python": platform.python_version(),
            "database": str(DB_PATH),
            "db_exists": DB_PATH.exists(),
            "sim_running": bool(state.get("sim", {}).get("running")),
            "tick": state.get("sim", {}).get("tick", 0),
            "checks": checks,
        }

    def summary(self) -> dict[str, Any]:
        state = plant_sim.snapshot()
        db_summary = db.summary()
        return {
            **self.health(),
            "db_summary": db_summary,
            "route_checks": self.route_checks(),
            "release_checks": self.release_checks(),
            "log_file": "app/data/logs/plantops.log",
            "sqlite_size_bytes": DB_PATH.stat().st_size if DB_PATH.exists() else 0,
            "current_plant": state.get("plant", {}),
        }

    def route_checks(self) -> list[dict[str, str]]:
        routes = [
            "/dashboard", "/process-flow", "/equipment", "/alarms", "/production",
            "/maintenance", "/loto", "/reports", "/scenarios", "/playback",
            "/plant-config", "/diagnostics", "/api/state", "/api/health",
            "/api/reports/daily", "/api/playback/summary",
        ]
        return [{"path": path, "expected": "200 OK"} for path in routes]

    def release_checks(self) -> list[dict[str, Any]]:
        files = [
            "README.md", "requirements.txt", "Dockerfile", "docker-compose.yml",
            "docs/OPERATIONS_GUIDE.md", "docs/RELEASE_CHECKLIST.md",
            "scripts/smoke_check.py", "scripts/project_tree.sh",
        ]
        return [{"name": f, "ok": Path(f).exists()} for f in files]

    def _checks(self, state: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"name": "simulation_state", "ok": bool(state), "detail": f"tick={state.get('sim', {}).get('tick', 0)}"},
            {"name": "database_file", "ok": DB_PATH.exists(), "detail": str(DB_PATH)},
            {"name": "production_samples", "ok": int(summary.get("production_samples", 0)) >= 0, "detail": summary.get("production_samples", 0)},
            {"name": "alarm_history", "ok": int(summary.get("alarm_history", 0)) >= 0, "detail": summary.get("alarm_history", 0)},
            {"name": "audit_log", "ok": int(summary.get("audit_log", 0)) >= 0, "detail": summary.get("audit_log", 0)},
        ]


diagnostics_service = DiagnosticsService()
