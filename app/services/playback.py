from __future__ import annotations

import sqlite3
from typing import Any

from app.services.db_store import DB_PATH, db


class PlaybackService:
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def production_samples(self, limit: int = 120) -> list[dict[str, Any]]:
        if not DB_PATH.exists():
            return []
        limit = max(1, min(int(limit), 500))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT tick, ts, production_tons, revenue_today, estimated_profit,
                       downtime_cost, wet_bin_fill, dry_bin_fill, dryer_temp_f, packaging_bag_hr
                FROM production_samples
                ORDER BY tick DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def summary(self) -> dict[str, Any]:
        samples = self.production_samples(limit=80)
        if not samples:
            return {"samples": [], "sample_count": 0, "first_tick": 0, "last_tick": 0}
        return {
            "samples": samples[-20:],
            "sample_count": len(samples),
            "first_tick": samples[0]["tick"],
            "last_tick": samples[-1]["tick"],
            "latest": samples[-1],
            "db_summary": db.summary(),
        }


playback_service = PlaybackService()
