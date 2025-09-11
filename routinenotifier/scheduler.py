from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import time as time_module

from .audio import play_audio_bytes
from .config import AppConfig, Schedule, Weekday
from .tts import Synthesizer

_WEEKDAY_MAP = {
    0: Weekday.mon,
    1: Weekday.tue,
    2: Weekday.wed,
    3: Weekday.thu,
    4: Weekday.fri,
    5: Weekday.sat,
    6: Weekday.sun,
}


def _today_weekday(now: datetime) -> Weekday:
    return _WEEKDAY_MAP[now.weekday()]


@dataclass(frozen=True)
class _Entry:
    index: int
    schedule: Schedule


def due_indices(cfg: AppConfig, *, now: datetime) -> list[int]:
    wd = _today_weekday(now)
    hh = now.hour
    mm = now.minute
    due: list[int] = []
    for i, s in enumerate(cfg.schedules):
        if wd not in s.days:
            continue
        if s.time.hour == hh and s.time.minute == mm:
            due.append(i)
    return due


def run_forever(
    cfg: AppConfig,
    synthesizer: Synthesizer,
    *,
    language_code: str = "ja-JP",
    voice_name: str | None = None,
    speaking_rate: float = 1.0,
    pitch: float = 0.0,
    audio_encoding: str = "MP3",
    check_interval_sec: float = 1.0,
) -> None:
    """Run the scheduler loop forever.

    Triggers tasks at exact minute matches; avoids re-triggering within the same day.
    """
    triggered: set[tuple[int, date]] = set()
    current_day = datetime.now().date()
    while True:
        now = datetime.now()
        if now.date() != current_day:
            triggered.clear()
            current_day = now.date()

        for idx in due_indices(cfg, now=now):
            key = (idx, now.date())
            if key in triggered:
                continue
            msg = cfg.schedules[idx].message
            audio = synthesizer.synthesize(
                msg,
                language_code=language_code,
                voice_name=voice_name,
                speaking_rate=speaking_rate,
                pitch=pitch,
                audio_encoding=audio_encoding,
            )
            play_audio_bytes(audio, encoding=audio_encoding)
            triggered.add(key)

        time_module.sleep(check_interval_sec)
