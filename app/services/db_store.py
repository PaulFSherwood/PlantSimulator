from __future__ import annotations

import json
import sqlite3
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "plantops.sqlite3"
TEMPLATE_PATH = DATA_DIR / "plant_templates" / "feed_mill.json"


class PlantOpsDb:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._lock = threading.RLock()
        self._last_recorded_tick: int | None = None

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def initialize(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    totp_secret TEXT,
                    totp_enabled INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(username) REFERENCES users(username)
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT,
                    details TEXT
                );

                CREATE TABLE IF NOT EXISTS plant_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    plant_type TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS production_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tick INTEGER NOT NULL,
                    ts TEXT NOT NULL,
                    production_tons REAL NOT NULL,
                    revenue_today INTEGER NOT NULL,
                    estimated_profit INTEGER NOT NULL,
                    downtime_cost INTEGER NOT NULL,
                    wet_bin_fill REAL NOT NULL,
                    dry_bin_fill REAL NOT NULL,
                    dryer_temp_f REAL NOT NULL,
                    packaging_bag_hr INTEGER NOT NULL,
                    UNIQUE(tick)
                );

                CREATE TABLE IF NOT EXISTS alarm_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alarm_id TEXT UNIQUE NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    equipment TEXT,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    acknowledged INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS report_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    data_json TEXT NOT NULL
                );
                """
            )
            self._seed_plant_config(conn)
            conn.commit()

    def _seed_plant_config(self, conn: sqlite3.Connection) -> None:
        existing = conn.execute("SELECT COUNT(*) AS count FROM plant_configs WHERE active = 1").fetchone()["count"]
        if existing:
            return
        if TEMPLATE_PATH.exists():
            config = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        else:
            config = {"name": "Demo Feed Mill", "plant_type": "Feed Mill", "operations": {"status": "Receiving Open", "shift": "Day Shift"}}
        now = self._now()
        conn.execute(
            "INSERT INTO plant_configs(name, plant_type, config_json, active, updated_at) VALUES (?, ?, ?, 1, ?)",
            (config.get("name", "Demo Feed Mill"), config.get("plant_type", "Feed Mill"), json.dumps(config), now),
        )

    def user_exists(self, username: str) -> bool:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
            return row is not None

    def create_user(self, username: str, display_name: str, role: str, password_hash: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users(username, display_name, role, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (username, display_name, role, password_hash, self._now()),
            )
            conn.commit()

    def get_user(self, username: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            return dict(row) if row else None

    def list_users(self) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT username, display_name, role, totp_enabled, created_at FROM users ORDER BY username").fetchall()
            return [dict(r) for r in rows]

    def update_user_totp(self, username: str, secret: str | None, enabled: bool) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE users SET totp_secret = ?, totp_enabled = ? WHERE username = ?",
                (secret, 1 if enabled else 0, username),
            )
            conn.commit()

    def create_session(self, token: str, username: str, expires_at: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions(token, username, expires_at, created_at) VALUES (?, ?, ?, ?)",
                (token, username, expires_at, self._now()),
            )
            conn.commit()

    def get_session_user(self, token: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT users.* FROM sessions
                JOIN users ON users.username = sessions.username
                WHERE sessions.token = ? AND sessions.expires_at > ?
                """,
                (token, self._now()),
            ).fetchone()
            return dict(row) if row else None

    def delete_session(self, token: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()

    def audit(self, username: str, action: str, target: str | None = None, details: Any = None) -> None:
        if not isinstance(details, str):
            details = json.dumps(details or {}, default=str)
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_log(ts, username, action, target, details) VALUES (?, ?, ?, ?, ?)",
                (self._now(), username, action, target, details),
            )
            conn.commit()

    def recent_audit(self, limit: int = 40) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_active_plant_config(self) -> dict[str, Any]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT config_json FROM plant_configs WHERE active = 1 ORDER BY id DESC LIMIT 1").fetchone()
            if not row:
                self.initialize()
                row = conn.execute("SELECT config_json FROM plant_configs WHERE active = 1 ORDER BY id DESC LIMIT 1").fetchone()
            return json.loads(row["config_json"])

    def update_plant_config(self, config: dict[str, Any], username: str = "system") -> dict[str, Any]:
        name = config.get("name", "Demo Feed Mill")
        plant_type = config.get("plant_type", "Feed Mill")
        with self._lock, self._connect() as conn:
            conn.execute("UPDATE plant_configs SET active = 0 WHERE active = 1")
            conn.execute(
                "INSERT INTO plant_configs(name, plant_type, config_json, active, updated_at) VALUES (?, ?, ?, 1, ?)",
                (name, plant_type, json.dumps(config), self._now()),
            )
            conn.commit()
        self.audit(username, "plant_config.update", name, {"plant_type": plant_type})
        return config

    def update_plant_profile(self, name: str, plant_type: str, status: str, shift: str, username: str = "system") -> dict[str, Any]:
        config = self.get_active_plant_config()
        config["name"] = name.strip() or config.get("name", "Demo Feed Mill")
        config["plant_type"] = plant_type.strip() or config.get("plant_type", "Feed Mill")
        operations = config.setdefault("operations", {})
        operations["status"] = status.strip() or operations.get("status", "Receiving Open")
        operations["shift"] = shift.strip() or operations.get("shift", "Day Shift")
        return self.update_plant_config(config, username)

    def record_snapshot_once(self, state: dict[str, Any]) -> None:
        tick = int(state.get("sim", {}).get("tick", 0))
        if self._last_recorded_tick == tick:
            return
        self._last_recorded_tick = tick
        dashboard = state.get("dashboard", {})
        process = state.get("process", {})
        sim = state.get("sim", {})
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO production_samples(
                    tick, ts, production_tons, revenue_today, estimated_profit, downtime_cost,
                    wet_bin_fill, dry_bin_fill, dryer_temp_f, packaging_bag_hr
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tick,
                    sim.get("updated_at") or self._now(),
                    float(dashboard.get("production_tons", 0)),
                    int(dashboard.get("revenue_today", 0)),
                    int(dashboard.get("estimated_profit", 0)),
                    int(dashboard.get("downtime_cost", 0)),
                    float(process.get("wet_bin_fill", 0)),
                    float(process.get("dry_bin_fill", 0)),
                    float(process.get("dryer_temp_f", 0)),
                    int(process.get("packaging_bag_hr", 0)),
                ),
            )
            for alarm in state.get("alarms", []):
                conn.execute(
                    """
                    INSERT INTO alarm_history(alarm_id, first_seen, last_seen, severity, equipment, title, message, acknowledged)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(alarm_id) DO UPDATE SET
                        last_seen = excluded.last_seen,
                        severity = excluded.severity,
                        equipment = excluded.equipment,
                        title = excluded.title,
                        message = excluded.message,
                        acknowledged = excluded.acknowledged
                    """,
                    (
                        alarm.get("id", "unknown"),
                        self._now(),
                        self._now(),
                        alarm.get("severity", "low"),
                        alarm.get("equipment", ""),
                        alarm.get("title", "Alarm"),
                        alarm.get("message", ""),
                        1 if alarm.get("acknowledged") else 0,
                    ),
                )
            conn.commit()

    def daily_report(self) -> dict[str, Any]:
        today = date.today().isoformat()
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM production_samples WHERE substr(ts, 1, 10) = ? ORDER BY id ASC",
                (today,),
            ).fetchall()
            alarms = conn.execute("SELECT * FROM alarm_history ORDER BY id DESC LIMIT 25").fetchall()
            audit = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 20").fetchall()
        first = dict(rows[0]) if rows else None
        last = dict(rows[-1]) if rows else None
        production_delta = 0.0 if not first or not last else round(last["production_tons"] - first["production_tons"], 2)
        report = {
            "report_date": today,
            "sample_count": len(rows),
            "production_delta_tons": production_delta,
            "latest": last or {},
            "alarms": [dict(r) for r in alarms],
            "audit": [dict(r) for r in audit],
            "generated_at": self._now(),
        }
        return report

    def save_report_snapshot(self, report: dict[str, Any]) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO report_snapshots(report_date, created_at, data_json) VALUES (?, ?, ?)",
                (report.get("report_date", date.today().isoformat()), self._now(), json.dumps(report, default=str)),
            )
            conn.commit()

    def report_csv(self) -> str:
        report = self.daily_report()
        lines = ["metric,value"]
        lines.append(f"report_date,{report['report_date']}")
        lines.append(f"sample_count,{report['sample_count']}")
        lines.append(f"production_delta_tons,{report['production_delta_tons']}")
        latest = report.get("latest", {})
        for key in ["production_tons", "revenue_today", "estimated_profit", "downtime_cost", "wet_bin_fill", "dry_bin_fill", "dryer_temp_f", "packaging_bag_hr"]:
            lines.append(f"latest_{key},{latest.get(key, '')}")
        return "\n".join(lines) + "\n"

    def summary(self) -> dict[str, Any]:
        with self._lock, self._connect() as conn:
            prod_count = conn.execute("SELECT COUNT(*) AS count FROM production_samples").fetchone()["count"]
            alarm_count = conn.execute("SELECT COUNT(*) AS count FROM alarm_history").fetchone()["count"]
            audit_count = conn.execute("SELECT COUNT(*) AS count FROM audit_log").fetchone()["count"]
            user_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
            cfg = conn.execute("SELECT name, plant_type, updated_at FROM plant_configs WHERE active = 1 ORDER BY id DESC LIMIT 1").fetchone()
        return {
            "database_path": str(self.db_path),
            "production_samples": prod_count,
            "alarm_history": alarm_count,
            "audit_events": audit_count,
            "users": user_count,
            "active_config": dict(cfg) if cfg else {},
        }

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")


db = PlantOpsDb()
