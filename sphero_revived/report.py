from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def new_report(mode: str, tool_version: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "tool_version": tool_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "mode": mode,
        "events": [],
    }


def add_event(report: dict[str, Any], event: str, **details: Any) -> None:
    report["events"].append(
        {
            "time": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **details,
        }
    )


def save_report(report: dict[str, Any], directory: Path, stem: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{stem}.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return path
