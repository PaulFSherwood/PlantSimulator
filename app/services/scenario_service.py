from __future__ import annotations

from typing import Any

from app.services.db_store import db
from app.sim.engine import plant_sim


SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "normal_shift",
        "name": "Normal Shift",
        "severity": "training",
        "description": "Reset the plant and run a clean normal receiving-to-packaging shift.",
        "actions": ["reset", "resume", "speed:1.0"],
    },
    {
        "id": "dryer_bottleneck",
        "name": "Dryer Bottleneck",
        "severity": "high",
        "description": "Inject a dryer fault so wet bin fills, throughput falls, and profit loss rises.",
        "actions": ["resume", "fault:dryer_line_1:high"],
    },
    {
        "id": "packaging_starved",
        "name": "Packaging Starved",
        "severity": "medium",
        "description": "Stop dryer output and let packaging drain the dry bin.",
        "actions": ["resume", "stop:dryer_line_1"],
    },
    {
        "id": "auger_bearing_failure",
        "name": "Auger Bearing Failure",
        "severity": "critical",
        "description": "Inject a critical fault on Auger 3 for maintenance and alarm workflow testing.",
        "actions": ["resume", "fault:auger_3:critical"],
    },
    {
        "id": "loto_drill",
        "name": "LOTO Drill",
        "severity": "safety",
        "description": "Lock out Conveyor 2 and create a safety drill state.",
        "actions": ["lockout:conveyor_2"],
    },
    {
        "id": "fast_forward",
        "name": "Fast Forward",
        "severity": "utility",
        "description": "Run the engine faster so trends and reports fill with samples quickly.",
        "actions": ["resume", "speed:4.0"],
    },
]


class ScenarioService:
    def list_scenarios(self) -> list[dict[str, Any]]:
        return SCENARIOS

    def get(self, scenario_id: str) -> dict[str, Any] | None:
        return next((s for s in SCENARIOS if s["id"] == scenario_id), None)

    def start_scenario(self, scenario_id: str, actor: str = "demo") -> dict[str, Any]:
        scenario = self.get(scenario_id)
        if not scenario:
            return {"error": f"Unknown scenario: {scenario_id}", "scenarios": self.list_scenarios()}

        state: dict[str, Any] = plant_sim.snapshot()
        for action in scenario.get("actions", []):
            state = self._apply_action(action, scenario)

        db.audit(actor, "scenario.start", scenario_id, {"name": scenario["name"], "actions": scenario.get("actions", [])})
        db.record_snapshot_once(state)
        return {"scenario": scenario, "state": state}

    def _apply_action(self, action: str, scenario: dict[str, Any]) -> dict[str, Any]:
        if action == "reset":
            return plant_sim.reset()
        if action == "resume":
            return plant_sim.resume()
        if action == "pause":
            return plant_sim.pause()
        if action.startswith("speed:"):
            return plant_sim.set_speed(float(action.split(":", 1)[1]))
        if action.startswith("stop:"):
            equipment_id = action.split(":", 1)[1]
            return plant_sim.equipment_action(equipment_id, "stop", f"Scenario: {scenario['name']}")
        if action.startswith("start:"):
            equipment_id = action.split(":", 1)[1]
            return plant_sim.equipment_action(equipment_id, "start", f"Scenario: {scenario['name']}")
        if action.startswith("lockout:"):
            equipment_id = action.split(":", 1)[1]
            return plant_sim.equipment_action(equipment_id, "lockout", f"Scenario: {scenario['name']}")
        if action.startswith("fault:"):
            _, equipment_id, severity = action.split(":", 2)
            return plant_sim.inject_fault(equipment_id, severity)
        return plant_sim.snapshot()


scenario_service = ScenarioService()
