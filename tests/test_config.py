from __future__ import annotations

from datetime import time

import pytest

from routinenotifier.config import AppConfig, ConfigError, Weekday, load_config


def test_valid_config(tmp_path):
    cfg_json = {
        "schedules": [
            {
                "name": "Test",
                "time": "09:30",
                "days": ["mon", "wed"],
                "message": "Hello",
            }
        ]
    }
    p = tmp_path / "cfg.json"
    p.write_text(__import__("json").dumps(cfg_json), encoding="utf-8")
    cfg = load_config(p)
    assert isinstance(cfg, AppConfig)
    s = cfg.schedules[0]
    assert s.time == time(9, 30)
    assert s.days == [Weekday.mon, Weekday.wed]
    assert s.message == "Hello"


def test_invalid_time(tmp_path):
    cfg_json = {
        "schedules": [
            {
                "name": "Bad",
                "time": "25:00",
                "days": ["mon"],
                "message": "Hi",
            }
        ]
    }
    p = tmp_path / "cfg.json"
    p.write_text(__import__("json").dumps(cfg_json), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(p)
