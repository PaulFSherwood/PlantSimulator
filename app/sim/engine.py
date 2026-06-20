from __future__ import annotations

import copy
import math
import random
import threading
import time
from datetime import datetime
from typing import Any


class PlantSimEngine:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = True
        self._tick = 0
        self._started_at = time.time()
        self._state = self._initial_state()

    def _initial_state(self) -> dict[str, Any]:
        return {
            "sim": {
                "running": True,
                "tick": 0,
                "speed": 1.0,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            },
            "plant": {
                "name": "Green Valley Grain & Feed",
                "status": "Receiving Open",
                "shift": "Day Shift",
            },
            "dashboard": {
                "production_tons": 1246,
                "production_target_tons": 1500,
                "revenue_today": 42800,
                "estimated_profit": 8950,
                "downtime_cost": 3400,
                "lost_profit_opportunity": 11700,
                "bottleneck": "Dryer Line 1",
                "bottleneck_loss_percent": 22,
            },
            "process": {
                "receiving_rate_bu_hr": 8450,
                "wet_bin_fill": 68,
                "dry_bin_fill": 42,
                "dryer_temp_f": 285,
                "dryer_outlet_moisture": 12.1,
                "packaging_bag_hr": 280,
                "bins": {
                    "bin_1": 72,
                    "bin_2": 68,
                    "bin_3": 48,
                    "bin_4": 27,
                },
            },
            "alarms": [
                {
                    "severity": "critical",
                    "title": "High Temperature",
                    "message": "Dryer Outlet Temp High",
                    "age": "2 min ago",
                },
                {
                    "severity": "high",
                    "title": "High Vibration",
                    "message": "Auger 3 Bearing",
                    "age": "5 min ago",
                },
                {
                    "severity": "medium",
                    "title": "High Motor Load",
                    "message": "Conveyor 2 Drive",
                    "age": "10 min ago",
                },
                {
                    "severity": "low",
                    "title": "Level Sensor Dirty",
                    "message": "Dry Bin Level Sensor",
                    "age": "15 min ago",
                },
            ],
        }

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

    def pause(self) -> dict[str, Any]:
        with self._lock:
            self._running = False
            self._state["sim"]["running"] = False
            return self.snapshot()

    def resume(self) -> dict[str, Any]:
        with self._lock:
            self._running = True
            self._state["sim"]["running"] = True
            return self.snapshot()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._tick = 0
            self._started_at = time.time()
            self._state = self._initial_state()
            self._running = True
            return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._state)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(1.0)
            with self._lock:
                if self._running:
                    self._tick_once()

    def _tick_once(self) -> None:
        self._tick += 1
        wave = math.sin(self._tick / 12.0)
        small_wave = math.sin(self._tick / 5.0)

        process = self._state["process"]
        dashboard = self._state["dashboard"]

        receiving_rate = int(8450 + (wave * 420) + random.randint(-90, 90))
        dryer_temp = round(285 + (small_wave * 5) + random.uniform(-1.4, 1.4), 1)
        outlet_moisture = round(12.1 + (wave * 0.25) + random.uniform(-0.05, 0.05), 2)
        packaging_rate = int(280 + (wave * 14) + random.randint(-4, 4))

        process["receiving_rate_bu_hr"] = max(0, receiving_rate)
        process["dryer_temp_f"] = dryer_temp
        process["dryer_outlet_moisture"] = outlet_moisture
        process["packaging_bag_hr"] = max(0, packaging_rate)

        # Bin movement: wet bin slowly rises, dry bin slowly falls/rises.
        process["wet_bin_fill"] = self._clamp(
            process["wet_bin_fill"] + random.uniform(-0.15, 0.35),
            0,
            100,
        )
        process["dry_bin_fill"] = self._clamp(
            process["dry_bin_fill"] + random.uniform(-0.25, 0.22),
            0,
            100,
        )

        for key in process["bins"]:
            process["bins"][key] = round(
                self._clamp(process["bins"][key] + random.uniform(-0.2, 0.25), 0, 100),
                1,
            )

        # Production/profit drift upward while running.
        dashboard["production_tons"] = round(dashboard["production_tons"] + random.uniform(0.05, 0.25), 1)
        dashboard["revenue_today"] = int(dashboard["production_tons"] * 34.35)
        dashboard["estimated_profit"] = int(dashboard["revenue_today"] * 0.209)
        dashboard["downtime_cost"] = int(3200 + abs(wave) * 480)
        dashboard["lost_profit_opportunity"] = int(10800 + abs(wave) * 1400)

        if dryer_temp >= 289:
            dashboard["bottleneck"] = "Dryer Line 1"
            dashboard["bottleneck_loss_percent"] = 24
        else:
            dashboard["bottleneck_loss_percent"] = 18

        self._state["sim"]["tick"] = self._tick
        self._state["sim"]["running"] = self._running
        self._state["sim"]["updated_at"] = datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))


plant_sim = PlantSimEngine()