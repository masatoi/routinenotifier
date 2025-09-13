from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .tts import Synthesizer


CACHE_VERSION = "v1"


def _default_cache_root() -> Path:
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or str(Path.home())
        return Path(base) / "routinenotifier" / "cache"
    # POSIX/XDG
    base = os.environ.get("XDG_CACHE_HOME")
    if base:
        return Path(base) / "routinenotifier"
    return Path.home() / ".cache" / "routinenotifier"


def _ext_for_encoding(encoding: str) -> str:
    enc = encoding.upper()
    if enc == "MP3":
        return ".mp3"
    if enc == "LINEAR16":
        return ".wav"
    if enc == "OGG_OPUS":
        return ".ogg"
    return ".bin"


@dataclass(frozen=True)
class CacheKey:
    text: str
    language_code: str
    voice_name: Optional[str]
    speaking_rate: float
    pitch: float
    audio_encoding: str
    version: str = CACHE_VERSION

    def digest(self) -> str:
        payload = {
            "t": self.text,
            "lc": self.language_code,
            "vn": self.voice_name or "",
            "sr": round(self.speaking_rate, 6),
            "pi": round(self.pitch, 6),
            "ae": self.audio_encoding.upper(),
            "v": self.version,
        }
        b = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(b).hexdigest()


def cache_path_for(key: CacheKey, cache_dir: Optional[Path] = None) -> Path:
    root = cache_dir or _default_cache_root()
    root.mkdir(parents=True, exist_ok=True)
    ext = _ext_for_encoding(key.audio_encoding)
    return root / f"{key.digest()}{ext}"


def _dir_size_bytes(path: Path) -> int:
    total = 0
    for p in path.glob("*"):
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            continue
    return total


def prune_cache(cache_dir: Path, max_bytes: int) -> None:
    if max_bytes <= 0:
        return
    try:
        files = [p for p in cache_dir.glob("*") if p.is_file()]
    except FileNotFoundError:
        return
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    total = 0
    keep: list[Path] = []
    for p in files:
        size = p.stat().st_size
        if total + size <= max_bytes:
            total += size
            keep.append(p)
        else:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass


class CachingSynthesizer:
    """Wraps a Synthesizer and caches audio bytes to disk.

    If disabled, passes through directly.
    """

    def __init__(
        self,
        inner: Synthesizer,
        *,
        cache_dir: Optional[Path] = None,
        enabled: bool = True,
        max_size_bytes: Optional[int] = None,
    ) -> None:
        self.inner = inner
        self.cache_dir = cache_dir or _default_cache_root()
        self.enabled = enabled
        self.max_size_bytes = max_size_bytes
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(
        self,
        text: str,
        *,
        language_code: str = "ja-JP",
        voice_name: Optional[str] = None,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        audio_encoding: str = "MP3",
    ) -> bytes:
        if not self.enabled:
            return self.inner.synthesize(
                text,
                language_code=language_code,
                voice_name=voice_name,
                speaking_rate=speaking_rate,
                pitch=pitch,
                audio_encoding=audio_encoding,
            )

        key = CacheKey(
            text=text,
            language_code=language_code,
            voice_name=voice_name,
            speaking_rate=speaking_rate,
            pitch=pitch,
            audio_encoding=audio_encoding,
        )
        path = cache_path_for(key, self.cache_dir)
        if path.exists():
            try:
                data = path.read_bytes()
                # touch to update atime/mtime for LRU
                try:
                    path.touch()
                except OSError:
                    pass
                return data
            except OSError:
                # Fall through to regenerate
                pass

        data = self.inner.synthesize(
            text,
            language_code=language_code,
            voice_name=voice_name,
            speaking_rate=speaking_rate,
            pitch=pitch,
            audio_encoding=audio_encoding,
        )

        tmp = None
        try:
            tmp = Path(
                tempfile.mkstemp(prefix="rn-", suffix=path.suffix, dir=str(self.cache_dir))[1]
            )
            Path(tmp).write_bytes(data)
            Path(tmp).replace(path)
        finally:
            if tmp is not None:
                try:
                    Path(tmp).unlink(missing_ok=True)
                except OSError:
                    pass

        if self.max_size_bytes and self.max_size_bytes > 0:
            try:
                prune_cache(self.cache_dir, self.max_size_bytes)
            except Exception:
                pass
        return data
