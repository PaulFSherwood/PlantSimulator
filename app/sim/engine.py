from __future__ import annotations

import copy
import math
import random
import threading
import time
from datetime import datetime
from typing import Any


class PlantSimEngine:
    """Small in-memory plant simulation engine.

    This is intentionally not a database yet. It gives the UI a live state shape,
    control actions, equipment status changes, alarms, and history samples.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = True
        self._speed = 1.0
        self._tick = 0
        self._state = self._initial_state()

    def _initial_state(self) -> dict[str, Any]:
        return {
            "sim": {
                "running": True,
                "tick": 0,
                "speed": 1.0,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "last_event": "Simulation reset",
            },
            "plant": {
                "name": "Demo Feed Mill",
                "status": "Receiving Open",
                "shift": "Day Shift",
            },
            "dashboard": {
                "production_tons": 1246.0,
                "production_target_tons": 1500.0,
                "production_percent": 83.0,
                "revenue_today": 42800,
                "estimated_profit": 8950,
                "profit_margin_percent": 20.9,
                "downtime_cost": 3400,
                "lost_profit_opportunity": 11700,
                "bottleneck": "Dryer Line 1",
                "bottleneck_loss_percent": 22,
                "end_of_day_profit": 12450,
                "optimized_profit": 20150,
            },
            "process": {
                "receiving_rate_bu_hr": 8450,
                "receiving_rate_ton_hr": 45.0,
                "wet_bin_fill": 68.0,
                "dry_bin_fill": 42.0,
                "hopper_fill": 44.0,
                "dryer_temp_f": 285.0,
                "dryer_outlet_moisture": 12.1,
                "packaging_bag_hr": 280,
                "bins": {
                    "bin_1": 72.0,
                    "bin_2": 68.0,
                    "bin_3": 48.0,
                    "bin_4": 27.0,
                },
                "flow": {
                    "receiving_to_wet": 45.0,
                    "wet_to_dryer": 38.0,
                    "dryer_to_dry": 35.0,
                    "dry_to_packaging": 34.0,
                },
            },
            "equipment": self._initial_equipment(),
            "alarms": self._initial_alarms(),
            "maintenance": {
                "open_work_orders": 7,
                "overdue_work_orders": 2,
                "planned_7_days": 4,
                "mttr_minutes": 46,
                "mtbf_hours": 128,
                "work_orders": [
                    {"id": "WO-1001", "equipment_id": "dryer_line_1", "equipment": "Dryer Line 1", "priority": "High", "status": "Open", "task": "Inspect outlet temperature drift"},
                    {"id": "WO-1002", "equipment_id": "auger_3", "equipment": "Auger 3", "priority": "High", "status": "Overdue", "task": "Bearing vibration inspection"},
                    {"id": "WO-1003", "equipment_id": "dry_bin", "equipment": "Dry Bin", "priority": "Medium", "status": "Open", "task": "Clean level sensor"},
                    {"id": "WO-1004", "equipment_id": "packaging_line_1", "equipment": "Packaging Line 1", "priority": "Low", "status": "Planned", "task": "Scale verification"},
                ],
            },
            "loto": {
                "locked_out": 1,
                "tagged_out": 0,
                "in_progress": 0,
                "verification": 0,
                "records": [
                    {"id": "LOTO-21", "equipment_id": "auger_3", "equipment": "Auger 3", "owner": "Maintenance", "status": "Locked Out", "reason": "Bearing inspection"},
                ],
            },
            "io": {
                "inputs": [
                    {"tag": "DI_DRYER_FLAME", "value": True, "label": "Dryer flame proven"},
                    {"tag": "AI_DRYER_TEMP", "value": 285.0, "label": "Dryer outlet temp"},
                    {"tag": "AI_WET_BIN_LEVEL", "value": 68.0, "label": "Wet bin level"},
                    {"tag": "AI_DRY_BIN_LEVEL", "value": 42.0, "label": "Dry bin level"},
                ],
                "outputs": [
                    {"tag": "DO_DRYER_RUN", "value": True, "label": "Dryer run command"},
                    {"tag": "DO_PACKAGER_RUN", "value": True, "label": "Packaging run command"},
                    {"tag": "DO_AUGER_3_RUN", "value": False, "label": "Auger 3 run command"},
                ],
            },
            "history": {
                "production": [],
                "events": [
                    {"tick": 0, "time": self._time_label(), "message": "Simulation reset"},
                ],
            },
        }

    def _initial_equipment(self) -> dict[str, dict[str, Any]]:
        return {
            "receiving_hopper": self._equipment("receiving_hopper", "Receiving Hopper", "Receiving", "running", 96, 3.2),
            "wet_bin_auger": self._equipment("wet_bin_auger", "Wet Bin Auger", "Conveyor", "running", 94, 3.2),
            "dryer_line_1": self._equipment("dryer_line_1", "Dryer Line 1", "Dryer", "warning", 78, 3.2),
            "dry_bin": self._equipment("dry_bin", "Dry Bin", "Storage", "running", 92, 3.2),
            "packaging_line_1": self._equipment("packaging_line_1", "Packaging Line 1", "Packaging", "running", 91, 3.2),
            "auger_3": self._equipment("auger_3", "Auger 3", "Conveyor", "locked_out", 62, 1.1, locked_out=True),
            "conveyor_2": self._equipment("conveyor_2", "Conveyor 2 Drive", "Conveyor", "warning", 74, 2.8),
            "elevator_1": self._equipment("elevator_1", "Bucket Elevator", "Elevator", "running", 89, 3.2),
            "mixer_1": self._equipment("mixer_1", "Mill / Mixer", "Mixer", "running", 86, 2.4),
        }

    @staticmethod
    def _equipment(eid: str, name: str, kind: str, status: str, health: float, runtime: float, locked_out: bool = False) -> dict[str, Any]:
        return {
            "id": eid,
            "name": name,
            "kind": kind,
            "status": status,
            "locked_out": locked_out,
            "runtime_hours": runtime,
            "health": health,
            "load_percent": 55.0,
            "temperature_f": 95.0,
            "vibration": 0.12,
            "last_action": "Auto",
        }

    def _initial_alarms(self) -> list[dict[str, Any]]:
        return [
            {"id": "ALM-001", "severity": "critical", "equipment_id": "dryer_line_1", "equipment": "Dryer Line 1", "title": "High Temperature", "message": "Dryer Outlet Temp High", "age": "2 min ago", "acknowledged": False},
            {"id": "ALM-002", "severity": "high", "equipment_id": "auger_3", "equipment": "Auger 3", "title": "High Vibration", "message": "Auger 3 Bearing", "age": "5 min ago", "acknowledged": False},
            {"id": "ALM-003", "severity": "medium", "equipment_id": "conveyor_2", "equipment": "Conveyor 2 Drive", "title": "High Motor Load", "message": "Conveyor 2 Drive", "age": "10 min ago", "acknowledged": False},
            {"id": "ALM-004", "severity": "low", "equipment_id": "dry_bin", "equipment": "Dry Bin", "title": "Level Sensor Dirty", "message": "Dry Bin Level Sensor", "age": "15 min ago", "acknowledged": False},
        ]

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._state)

    def pause(self) -> dict[str, Any]:
        with self._lock:
            self._running = False
            self._state["sim"]["running"] = False
            self._event("Simulation paused")
            return self.snapshot()

    def resume(self) -> dict[str, Any]:
        with self._lock:
            self._running = True
            self._state["sim"]["running"] = True
            self._event("Simulation resumed")
            return self.snapshot()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._tick = 0
            self._state = self._initial_state()
            self._running = True
            self._speed = 1.0
            return self.snapshot()

    def set_speed(self, speed: float) -> dict[str, Any]:
        with self._lock:
            self._speed = self._clamp(float(speed), 0.25, 8.0)
            self._state["sim"]["speed"] = self._speed
            self._event(f"Simulation speed set to {self._speed:g}x")
            return self.snapshot()

    def equipment_action(self, equipment_id: str, action: str, reason: str | None = None) -> dict[str, Any]:
        with self._lock:
            eq = self._state["equipment"].get(equipment_id)
            if not eq:
                return {"error": f"Unknown equipment: {equipment_id}", **self.snapshot()}

            reason_text = reason or "Manual action"
            if action == "start":
                if eq["locked_out"]:
                    self._event(f"Start blocked for {eq['name']} because it is locked out")
                else:
                    eq["status"] = "running"
                    eq["last_action"] = reason_text
                    self._event(f"Started {eq['name']}")
            elif action == "stop":
                eq["status"] = "stopped"
                eq["last_action"] = reason_text
                self._event(f"Stopped {eq['name']}")
            elif action == "lockout":
                eq["locked_out"] = True
                eq["status"] = "locked_out"
                eq["last_action"] = reason_text
                self._ensure_loto_record(equipment_id, eq["name"], reason_text)
                self._event(f"Locked out {eq['name']}")
            elif action == "clear_lockout":
                eq["locked_out"] = False
                eq["status"] = "stopped"
                eq["last_action"] = reason_text
                self._state["loto"]["records"] = [r for r in self._state["loto"]["records"] if r.get("equipment_id") != equipment_id]
                self._event(f"Cleared lockout for {eq['name']}")
            elif action == "degrade":
                eq["health"] = max(0, eq["health"] - 10)
                eq["status"] = "warning" if eq["health"] > 45 else "faulted"
                eq["last_action"] = reason_text
                self._event(f"Injected degradation on {eq['name']}")
            self._recalculate_loto()
            self._refresh_alarms()
            return self.snapshot()

    def acknowledge_alarm(self, alarm_id: str) -> dict[str, Any]:
        with self._lock:
            for alarm in self._state["alarms"]:
                if alarm["id"] == alarm_id:
                    alarm["acknowledged"] = True
                    self._event(f"Acknowledged alarm {alarm_id}")
                    break
            return self.snapshot()

    def inject_fault(self, equipment_id: str, severity: str = "high") -> dict[str, Any]:
        with self._lock:
            eq = self._state["equipment"].get(equipment_id)
            if not eq:
                return {"error": f"Unknown equipment: {equipment_id}", **self.snapshot()}
            eq["status"] = "faulted" if severity in {"critical", "high"} else "warning"
            eq["health"] = max(10, eq["health"] - 20)
            new_id = f"ALM-{len(self._state['alarms']) + 1:03d}"
            self._state["alarms"].insert(0, {
                "id": new_id,
                "severity": severity,
                "equipment_id": equipment_id,
                "equipment": eq["name"],
                "title": "Injected Fault",
                "message": f"Training fault on {eq['name']}",
                "age": "just now",
                "acknowledged": False,
            })
            self._event(f"Injected {severity} fault on {eq['name']}")
            return self.snapshot()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(1.0)
            with self._lock:
                if self._running:
                    steps = max(1, int(round(self._speed)))
                    for _ in range(steps):
                        self._tick_once()

    def _tick_once(self) -> None:
        self._tick += 1
        wave = math.sin(self._tick / 12.0)
        fast_wave = math.sin(self._tick / 5.0)
        process = self._state["process"]
        dashboard = self._state["dashboard"]
        equipment = self._state["equipment"]

        dryer_running = equipment["dryer_line_1"]["status"] in {"running", "warning"}
        packaging_running = equipment["packaging_line_1"]["status"] in {"running", "warning"}
        receiving_running = equipment["receiving_hopper"]["status"] in {"running", "warning"}

        receiving_rate = 8450 + wave * 420 + random.randint(-90, 90) if receiving_running else 0
        dryer_flow = 38.0 + fast_wave * 2.8 if dryer_running else 0.0
        packaging_flow = 34.0 + wave * 1.8 if packaging_running and process["dry_bin_fill"] > 3 else 0.0

        process["receiving_rate_bu_hr"] = int(max(0, receiving_rate))
        process["receiving_rate_ton_hr"] = round(process["receiving_rate_bu_hr"] / 187.8, 1)
        process["flow"]["receiving_to_wet"] = process["receiving_rate_ton_hr"]
        process["flow"]["wet_to_dryer"] = round(max(0, dryer_flow), 1)
        process["flow"]["dryer_to_dry"] = round(max(0, dryer_flow * 0.93), 1)
        process["flow"]["dry_to_packaging"] = round(max(0, packaging_flow), 1)

        process["wet_bin_fill"] = self._clamp(process["wet_bin_fill"] + (process["flow"]["receiving_to_wet"] - process["flow"]["wet_to_dryer"]) / 240.0, 0, 100)
        process["dry_bin_fill"] = self._clamp(process["dry_bin_fill"] + (process["flow"]["dryer_to_dry"] - process["flow"]["dry_to_packaging"]) / 250.0, 0, 100)
        process["hopper_fill"] = self._clamp(44.0 + wave * 8.0, 0, 100)

        dryer_temp = 285 + fast_wave * 5 + random.uniform(-1.2, 1.2)
        if not dryer_running:
            dryer_temp -= 28
        process["dryer_temp_f"] = round(dryer_temp, 1)
        process["dryer_outlet_moisture"] = round(12.1 + wave * 0.25 + random.uniform(-0.04, 0.04), 2)
        process["packaging_bag_hr"] = int(max(0, 280 + wave * 14 + random.randint(-4, 4))) if packaging_running else 0

        for key in process["bins"]:
            process["bins"][key] = round(self._clamp(process["bins"][key] + random.uniform(-0.18, 0.22), 0, 100), 1)

        for eq in equipment.values():
            if eq["status"] in {"running", "warning"}:
                eq["runtime_hours"] = round(eq["runtime_hours"] + 1 / 3600, 2)
                eq["load_percent"] = round(self._clamp(55 + wave * 20 + random.uniform(-2, 2), 0, 100), 1)
                eq["temperature_f"] = round(95 + eq["load_percent"] * 0.35 + random.uniform(-2, 2), 1)
                eq["vibration"] = round(self._clamp(eq["vibration"] + random.uniform(-0.01, 0.012), 0.02, 1.2), 3)

        equipment["dryer_line_1"]["temperature_f"] = process["dryer_temp_f"]
        equipment["dryer_line_1"]["load_percent"] = round(self._clamp(72 + abs(fast_wave) * 18, 0, 100), 1)
        equipment["dryer_line_1"]["status"] = "warning" if process["dryer_temp_f"] >= 288 and not equipment["dryer_line_1"]["locked_out"] else equipment["dryer_line_1"]["status"]

        produced = max(0, process["flow"]["dry_to_packaging"] / 3600)
        dashboard["production_tons"] = round(dashboard["production_tons"] + produced * 60, 1)
        dashboard["production_percent"] = round(self._clamp((dashboard["production_tons"] / dashboard["production_target_tons"]) * 100, 0, 999), 1)
        dashboard["revenue_today"] = int(dashboard["production_tons"] * 34.35)
        dashboard["estimated_profit"] = int(dashboard["revenue_today"] * 0.209)
        dashboard["profit_margin_percent"] = 20.9
        dashboard["downtime_cost"] = int(3200 + abs(wave) * 480)
        dashboard["lost_profit_opportunity"] = int(10800 + abs(wave) * 1400 + (0 if dryer_running else 2200))
        dashboard["end_of_day_profit"] = int(dashboard["estimated_profit"] + 3500)
        dashboard["optimized_profit"] = int(dashboard["end_of_day_profit"] + dashboard["lost_profit_opportunity"] * 0.65)
        dashboard["bottleneck"] = "Dryer Line 1" if dryer_running else "Dryer Stopped"
        dashboard["bottleneck_loss_percent"] = 24 if process["dryer_temp_f"] >= 288 else 18

        self._refresh_alarms()
        self._update_io()
        self._append_history()
        self._state["sim"]["tick"] = self._tick
        self._state["sim"]["running"] = self._running
        self._state["sim"]["speed"] = self._speed
        self._state["sim"]["updated_at"] = datetime.now().isoformat(timespec="seconds")

    def _refresh_alarms(self) -> None:
        alarms = self._state["alarms"]
        known = {a["id"]: a for a in alarms}
        dryer_temp = self._state["process"]["dryer_temp_f"]
        if dryer_temp >= 288 and "ALM-AUTO-DRYER-TEMP" not in known:
            alarms.insert(0, {"id": "ALM-AUTO-DRYER-TEMP", "severity": "critical", "equipment_id": "dryer_line_1", "equipment": "Dryer Line 1", "title": "High Temperature", "message": "Dryer outlet temperature above target", "age": "just now", "acknowledged": False})
        if self._state["process"]["wet_bin_fill"] > 92 and "ALM-AUTO-WET-HIGH" not in known:
            alarms.insert(0, {"id": "ALM-AUTO-WET-HIGH", "severity": "high", "equipment_id": "wet_bin_auger", "equipment": "Wet Bin Auger", "title": "Wet Bin High Level", "message": "Wet bin filling faster than dryer draw", "age": "just now", "acknowledged": False})

        # Keep list from growing forever in this fake engine.
        self._state["alarms"] = alarms[:12]

    def _update_io(self) -> None:
        process = self._state["process"]
        equipment = self._state["equipment"]
        self._state["io"]["inputs"] = [
            {"tag": "DI_DRYER_FLAME", "value": equipment["dryer_line_1"]["status"] in {"running", "warning"}, "label": "Dryer flame proven"},
            {"tag": "AI_DRYER_TEMP", "value": process["dryer_temp_f"], "label": "Dryer outlet temp"},
            {"tag": "AI_WET_BIN_LEVEL", "value": round(process["wet_bin_fill"], 1), "label": "Wet bin level"},
            {"tag": "AI_DRY_BIN_LEVEL", "value": round(process["dry_bin_fill"], 1), "label": "Dry bin level"},
        ]
        self._state["io"]["outputs"] = [
            {"tag": "DO_DRYER_RUN", "value": equipment["dryer_line_1"]["status"] in {"running", "warning"}, "label": "Dryer run command"},
            {"tag": "DO_PACKAGER_RUN", "value": equipment["packaging_line_1"]["status"] in {"running", "warning"}, "label": "Packaging run command"},
            {"tag": "DO_AUGER_3_RUN", "value": equipment["auger_3"]["status"] in {"running", "warning"}, "label": "Auger 3 run command"},
        ]

    def _append_history(self) -> None:
        if self._tick % 5 != 0:
            return
        self._state["history"]["production"].append({
            "tick": self._tick,
            "time": self._time_label(),
            "tons": self._state["dashboard"]["production_tons"],
            "rate": self._state["process"]["flow"]["dry_to_packaging"],
        })
        self._state["history"]["production"] = self._state["history"]["production"][-48:]

    def _ensure_loto_record(self, equipment_id: str, name: str, reason: str) -> None:
        if any(r.get("equipment_id") == equipment_id for r in self._state["loto"]["records"]):
            return
        self._state["loto"]["records"].append({
            "id": f"LOTO-{len(self._state['loto']['records']) + 22}",
            "equipment_id": equipment_id,
            "equipment": name,
            "owner": "Maintenance",
            "status": "Locked Out",
            "reason": reason,
        })

    def _recalculate_loto(self) -> None:
        records = self._state["loto"]["records"]
        self._state["loto"]["locked_out"] = len(records)
        self._state["loto"]["tagged_out"] = 0
        self._state["loto"]["in_progress"] = 0
        self._state["loto"]["verification"] = 0

    def _event(self, message: str) -> None:
        self._state["sim"]["last_event"] = message
        self._state["history"]["events"].insert(0, {"tick": self._tick, "time": self._time_label(), "message": message})
        self._state["history"]["events"] = self._state["history"]["events"][:40]

    @staticmethod
    def _time_label() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))


plant_sim = PlantSimEngine()
