from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import datetime as dt
from enum import Enum
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


class Weekday(str, Enum):
    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"


def _parse_time(value: str) -> dt.time:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("time must be in HH:MM format")
    hour, minute = parts
    h = int(hour)
    m = int(minute)
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("time must be a valid 24h time")
    return dt.time(hour=h, minute=m)


class Schedule(BaseModel):
    name: str = Field(..., description="Task name")
    time: dt.time = Field(..., description="Time in HH:MM (24h)")
    days: list[Weekday] = Field(..., description="Days to run: mon..sun")
    message: str = Field(..., description="Message to speak")

    @field_validator("time", mode="before")
    @classmethod
    def validate_time(cls, v: Any) -> dt.time:
        if isinstance(v, dt.time):
            return v
        if isinstance(v, str):
            return _parse_time(v.strip())
        raise TypeError("time must be a string in HH:MM format")

    @field_validator("days", mode="before")
    @classmethod
    def normalize_days(cls, v: Any) -> Iterable[Weekday]:
        if isinstance(v, list | tuple):
            norm: list[Weekday] = []
            for d in v:
                if isinstance(d, Weekday):
                    norm.append(d)
                else:
                    s = str(d).lower()
                    if "." in s:
                        s = s.split(".")[-1]
                    norm.append(Weekday(s))
            return norm
        raise TypeError("days must be a list of weekdays (mon..sun)")


class AppConfig(BaseModel):
    schedules: list[Schedule]


class ConfigError(Exception):
    pass


def load_config(path: Path) -> AppConfig:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ConfigError(f"Config file not found: {path}") from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON: {e}") from e
    try:
        return AppConfig.model_validate(data)
    except ValidationError as e:
        raise ConfigError(f"Config validation error: {e}") from e


class VoiceConfig(BaseModel):
    language_code: str = Field(
        default="ja-JP", description="BCP-47 language code like ja-JP or en-US"
    )
    voice_name: str | None = Field(default=None, description="Specific TTS voice name")
    speaking_rate: float = Field(default=1.0, ge=0.25, le=4.0, description="Speaking rate")
    pitch: float = Field(
        default=0.0, ge=-20.0, le=20.0, description="Pitch in semitones (-20.0..20.0)"
    )
    audio_encoding: str = Field(
        default="MP3", description="MP3, LINEAR16, or OGG_OPUS"
    )

    @field_validator("audio_encoding")
    @classmethod
    def _enc_upper(cls, v: str) -> str:
        v2 = v.upper()
        if v2 not in {"MP3", "LINEAR16", "OGG_OPUS"}:
            raise ValueError("audio_encoding must be MP3, LINEAR16, or OGG_OPUS")
        return v2


def load_voice_config(path: Path) -> VoiceConfig:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ConfigError(f"Voice config file not found: {path}") from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON: {e}") from e
    try:
        return VoiceConfig.model_validate(data)
    except ValidationError as e:
        raise ConfigError(f"Voice config validation error: {e}") from e


@dataclass(frozen=True)
class ScheduleKey:
    index: int
    name: str
    hhmm: str

    @staticmethod
    def from_schedule(index: int, s: Schedule) -> ScheduleKey:
        hhmm = f"{s.time.hour:02d}:{s.time.minute:02d}"
        return ScheduleKey(index=index, name=s.name, hhmm=hhmm)
