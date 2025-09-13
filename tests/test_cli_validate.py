from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from routinenotifier.cli import app


def test_cli_validate_ok(tmp_path: Path):
    cfg = {
        "schedules": [
            {
                "name": "X",
                "time": "06:00",
                "days": ["mon"],
                "message": "Wake up",
            }
        ]
    }
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["validate", str(cfg_path)])
    assert result.exit_code == 0
    assert "Config is valid" in result.output


def test_cli_validate_fail(tmp_path: Path):
    cfg = {"schedules": [{"name": "X", "time": "25:00", "days": ["mon"], "message": "x"}]}
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["validate", str(cfg_path)])
    assert result.exit_code != 0
    assert "validation" in result.output.lower()
