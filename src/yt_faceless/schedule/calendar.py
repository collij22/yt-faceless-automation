"""Minimal calendar module for content scheduling."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import AppConfig

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CalendarStore:
    path: Path

    def load(self) -> List[Dict[str, Any]]:
        return json.loads(self.path.read_text()) if self.path.exists() else []

    def save(self, items: List[Dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(items, indent=2))


def add_item(cfg: AppConfig, item: Dict[str, Any]) -> None:
    store = CalendarStore(cfg.directories.data_dir / "calendar" / "items.json")
    items = store.load()
    items.append(item)
    store.save(items)


def list_items(cfg: AppConfig, slug: Optional[str] = None) -> List[Dict[str, Any]]:
    store = CalendarStore(cfg.directories.data_dir / "calendar" / "items.json")
    items = store.load()
    return [i for i in items if not slug or i.get("slug") == slug]


async def schedule_content(
    cfg: AppConfig,
    slug: str,
    publish_date: Optional[datetime] = None,
    template: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Schedule a content slug for publishing."""
    when = publish_date or (datetime.now(timezone.utc) + timedelta(hours=24))
    item = {
        "slug": slug,
        "platform": "youtube",
        "scheduled_time": when.isoformat(),
        "status": "scheduled",
        "priority": 5,
        "template": template,
    }
    if dry_run:
        return {"would_schedule": item}
    add_item(cfg, item)
    return {"scheduled_time": item["scheduled_time"], "status": "scheduled"}


def get_publishing_schedule(
    cfg: AppConfig,
    days_ahead: int = 7,
    analyze: bool = False,
) -> Dict[str, Any]:
    """Return upcoming schedule (optionally with simple analytics)."""
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=days_ahead)
    items = list_items(cfg)
    upcoming = [
        i
        for i in items
        if "scheduled_time" in i
        and now <= datetime.fromisoformat(i["scheduled_time"].replace("Z", "+00:00")) <= horizon
    ]
    out: Dict[str, Any] = {"upcoming": upcoming}
    if analyze:
        out["analytics"] = {"status": "no_data"}  # TODO: integrate n8n analytics if desired
    return out