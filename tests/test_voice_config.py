from __future__ import annotations

from pathlib import Path

import json
import pytest

from routinenotifier.config import ConfigError, VoiceConfig, load_voice_config


def test_load_voice_config_ok(tmp_path: Path) -> None:
    data = {
        "language_code": "ja-JP",
        "voice_name": "ja-JP-Standard-A",
        "speaking_rate": 1.2,
        "pitch": -3.5,
        "audio_encoding": "mp3",
    }
    p = tmp_path / "voice.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    cfg = load_voice_config(p)
    assert isinstance(cfg, VoiceConfig)
    assert cfg.language_code == "ja-JP"
    assert cfg.voice_name == "ja-JP-Standard-A"
    assert cfg.speaking_rate == 1.2
    assert cfg.pitch == -3.5
    assert cfg.audio_encoding == "MP3"


def test_load_voice_config_bad_encoding(tmp_path: Path) -> None:
    data = {
        "language_code": "ja-JP",
        "audio_encoding": "FLAC",
    }
    p = tmp_path / "voice.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_voice_config(p)


def test_load_voice_config_bad_pitch(tmp_path: Path) -> None:
    data = {
        "language_code": "ja-JP",
        "pitch": 30.0
    }
    p = tmp_path / "voice.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_voice_config(p)
