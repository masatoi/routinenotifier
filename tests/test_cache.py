from __future__ import annotations

from pathlib import Path

from routinenotifier.cache import CachingSynthesizer, CacheKey, cache_path_for, prune_cache
from routinenotifier.tts import Synthesizer


class FakeSynth(Synthesizer):  # type: ignore[misc]
    def __init__(self, payload_size: int = 16) -> None:
        self.calls: int = 0
        self.payload_size = payload_size

    def synthesize(
        self,
        text: str,
        *,
        language_code: str = "ja-JP",
        voice_name: str | None = None,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        audio_encoding: str = "MP3",
    ) -> bytes:
        self.calls += 1
        base = (
            f"{text}|{language_code}|{voice_name}|{speaking_rate}|{pitch}|{audio_encoding}".encode(
                "utf-8"
            )
        )
        if len(base) >= self.payload_size:
            return base
        return base + b"-" * (self.payload_size - len(base))


def test_caching_hit_and_miss(tmp_path: Path) -> None:
    inner = FakeSynth()
    cache = CachingSynthesizer(inner, cache_dir=tmp_path, enabled=True)
    # First call: miss
    b1 = cache.synthesize("hello", language_code="ja-JP", audio_encoding="MP3")
    assert inner.calls == 1
    # Second call same params: hit
    b2 = cache.synthesize("hello", language_code="ja-JP", audio_encoding="MP3")
    assert inner.calls == 1
    assert b1 == b2


def test_caching_key_changes_with_pitch(tmp_path: Path) -> None:
    inner = FakeSynth()
    cache = CachingSynthesizer(inner, cache_dir=tmp_path, enabled=True)
    cache.synthesize("hello", language_code="ja-JP", pitch=0.0)
    cache.synthesize("hello", language_code="ja-JP", pitch=2.0)
    # Two different keys should cause two inner calls
    assert inner.calls == 2


def test_prune_cache_respects_size(tmp_path: Path) -> None:
    inner = FakeSynth(payload_size=50_000)
    cache = CachingSynthesizer(inner, cache_dir=tmp_path, enabled=True, max_size_bytes=100_000)
    # Create three entries (~150KB total)
    cache.synthesize("a")
    cache.synthesize("b")
    cache.synthesize("c")
    # Prune executed internally; total directory size should be <= 100KB
    total = sum(p.stat().st_size for p in tmp_path.glob("*") if p.is_file())
    assert total <= 100_000
