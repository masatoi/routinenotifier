from __future__ import annotations

from collections.abc import Iterable
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile


def _choose_player(candidates: Iterable[str]) -> str | None:
    for c in candidates:
        if shutil.which(c):
            return c
    return None


def _ext_for_encoding(encoding: str) -> str:
    enc = encoding.upper()
    if enc == "MP3":
        return ".mp3"
    if enc == "LINEAR16":
        return ".wav"
    if enc == "OGG_OPUS":
        return ".ogg"
    return ".bin"


def play_audio_bytes(audio: bytes, *, encoding: str = "MP3") -> None:
    ext = _ext_for_encoding(encoding)
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
        f.write(audio)
        tmp_path = Path(f.name)

    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            player = _choose_player(["afplay", "open"])  # open will use default app
            if player == "afplay":
                subprocess.run([player, str(tmp_path)], check=False)
            elif player == "open":
                subprocess.run([player, str(tmp_path)], check=False)
            else:
                print(f"No audio player found. Saved to {tmp_path}")
        elif system == "Linux":
            # Prefer formats: wav->aplay/paplay, mp3->mpg123, ogg->paplay/ffplay
            if ext == ".wav":
                player = _choose_player(["aplay", "paplay", "ffplay"])
            elif ext == ".mp3":
                player = _choose_player(["mpg123", "ffplay", "paplay"])
            else:
                player = _choose_player(["ffplay", "paplay"])
            if player:
                if player == "ffplay":
                    subprocess.run([player, "-nodisp", "-autoexit", str(tmp_path)], check=False)
                else:
                    subprocess.run([player, str(tmp_path)], check=False)
            else:
                print(f"No suitable audio player found. Saved to {tmp_path}")
        elif system == "Windows":
            # Use default handler. This returns immediately.
            os.startfile(str(tmp_path))  # type: ignore[attr-defined]
        else:
            print(f"Unsupported OS {system}. Saved to {tmp_path}")
    finally:
        # Do not remove file immediately to ensure player can read it; leave temp file.
        pass
