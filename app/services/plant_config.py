import json
from functools import lru_cache
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = APP_DIR / "data" / "plant_templates"


@lru_cache(maxsize=16)
def load_plant_config(template_name: str = "feed_mill") -> dict[str, Any]:
    """Load a plant template JSON file from app/data/plant_templates."""
    template_path = TEMPLATE_DIR / f"{template_name}.json"
    with template_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def get_plant_context(template_name: str = "feed_mill") -> dict[str, Any]:
    """Return template context plus old shortcut variables used by early pages."""
    plant = load_plant_config(template_name)
    operations = plant.get("operations", {})
    dashboard = plant.get("dashboard", {})

    profit_metric = next(
        (metric for metric in dashboard.get("metrics", []) if metric.get("label") == "Estimated Profit"),
        {},
    )
    lost_profit_metric = next(
        (metric for metric in dashboard.get("metrics", []) if metric.get("label") == "Lost Profit Opportunity"),
        {},
    )

    return {
        "plant": plant,
        "plant_name": plant.get("name", "Demo Feed Mill"),
        "app_version": plant.get("app_version", "1.0.0"),
        "status": operations.get("status", "Unknown"),
        "shift": operations.get("shift", "Unknown"),
        "profit_today": profit_metric.get("value", "$0"),
        "lost_profit": lost_profit_metric.get("value", "$0"),
        "throughput": operations.get("throughput", "0 tons/hr"),
        "uptime": operations.get("uptime", "0%"),
        "active_faults": operations.get("active_faults", "0"),
        "bottleneck": operations.get("bottleneck", "None"),
    }
