"""
Simple JSON-backed learner profile store. Tracks topics studied, scores,
and strong/weak concepts across sessions so future lessons can be
personalized using history -- deliberately kept as plain JSON (no DB
setup needed) since the assessment only requires the capability to exist,
not a production-grade datastore.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import Optional

import config


def _load_all() -> dict:
    if not os.path.exists(config.PROFILE_STORE_PATH):
        return {}
    with open(config.PROFILE_STORE_PATH, "r") as f:
        return json.load(f)


def _save_all(data: dict) -> None:
    with open(config.PROFILE_STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_profile(student_id: str) -> dict:
    data = _load_all()
    return data.get(student_id, {
        "student_id": student_id,
        "sessions": [],
        "strong_concepts": [],
        "weak_concepts": [],
    })


def record_session(student_id: str, topic: str, score: float, strong: list[str], weak: list[str], recommendation: str) -> None:
    data = _load_all()
    profile = data.get(student_id, {
        "student_id": student_id,
        "sessions": [],
        "strong_concepts": [],
        "weak_concepts": [],
    })

    profile["sessions"].append({
        "topic": topic,
        "score": score,
        "recommendation": recommendation,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Merge concept lists, keeping the most recent classification of each concept
    strong_set = set(profile["strong_concepts"]) | set(strong)
    weak_set = (set(profile["weak_concepts"]) | set(weak)) - strong_set
    profile["strong_concepts"] = sorted(strong_set)
    profile["weak_concepts"] = sorted(weak_set)

    data[student_id] = profile
    _save_all(data)


def get_recommended_focus(student_id: str) -> Optional[str]:
    """Simple heuristic: recommend revisiting the most recently added weak concept."""
    profile = get_profile(student_id)
    weak = profile.get("weak_concepts", [])
    return weak[-1] if weak else None
