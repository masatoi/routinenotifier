from __future__ import annotations

from datetime import datetime

from routinenotifier.config import AppConfig, Schedule, Weekday
from routinenotifier.scheduler import due_indices


def _cfg_at(hh: int, mm: int, days):
    return AppConfig(
        schedules=[
            Schedule(name="A", time=f"{hh:02d}:{mm:02d}", days=days, message="m"),
        ]
    )


def test_due_indices_match_current_minute():
    cfg = _cfg_at(7, 0, [Weekday.mon])
    now = datetime(2024, 1, 1, 7, 0)  # Monday
    assert due_indices(cfg, now=now) == [0]


def test_due_indices_skip_wrong_minute():
    cfg = _cfg_at(7, 1, [Weekday.mon])
    now = datetime(2024, 1, 1, 7, 0)
    assert due_indices(cfg, now=now) == []


def test_due_indices_skip_wrong_day():
    cfg = _cfg_at(7, 0, [Weekday.tue])
    now = datetime(2024, 1, 1, 7, 0)  # Monday
    assert due_indices(cfg, now=now) == []

