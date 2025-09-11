from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Synthesizer(Protocol):
    def synthesize(
        self,
        text: str,
        *,
        language_code: str = "ja-JP",
        voice_name: str | None = None,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        audio_encoding: str = "MP3",
    ) -> bytes:  # pragma: no cover - protocol
        ...


class GoogleTTS:
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
        try:
            from google.cloud import texttospeech  # type: ignore
        except Exception as e:  # pragma: no cover - import-time path
            raise RuntimeError(
                "google-cloud-texttospeech is required. Install the package "
                "and configure GCP credentials."
            ) from e

        audio_enc_map = {
            "MP3": texttospeech.AudioEncoding.MP3,
            "LINEAR16": texttospeech.AudioEncoding.LINEAR16,
            "OGG_OPUS": texttospeech.AudioEncoding.OGG_OPUS,
        }
        enc = audio_enc_map.get(audio_encoding.upper())
        if enc is None:
            raise ValueError("Unsupported audio encoding. Use MP3, LINEAR16, or OGG_OPUS.")

        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice_params = {
            "language_code": language_code,
        }
        if voice_name:
            voice_params["name"] = voice_name

        voice = texttospeech.VoiceSelectionParams(**voice_params)

        audio_config = texttospeech.AudioConfig(
            audio_encoding=enc,
            speaking_rate=speaking_rate,
            pitch=pitch,
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return bytes(response.audio_content)


class DummyTTS:
    """A dummy synthesizer used for tests; returns silence WAV bytes."""

    def synthesize(
        self,
        text: str,
        *,
        language_code: str = "ja-JP",
        voice_name: str | None = None,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        audio_encoding: str = "LINEAR16",
    ) -> bytes:
        # Produce 0.2s of silence as 16-bit PCM WAV
        import io
        import wave

        framerate = 16000
        duration_sec = 0.2
        nframes = int(framerate * duration_sec)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(framerate)
            wf.writeframes(b"\x00\x00" * nframes)
        return buf.getvalue()


@dataclass(frozen=True)
class VoiceInfo:
    name: str
    language_codes: list[str]
    ssml_gender: str
    natural_sample_rate_hz: int


def list_voices(language_code: str | None = None) -> list[VoiceInfo]:
    """List available Google TTS voices; optionally filter by language code.

    Example language codes: "ja-JP", "en-US".
    """
    try:
        from google.cloud import texttospeech  # type: ignore
    except Exception as e:  # pragma: no cover - import-time path
        raise RuntimeError(
            "google-cloud-texttospeech is required. Install the package "
            "and configure GCP credentials."
        ) from e

    client = texttospeech.TextToSpeechClient()
    lang = language_code or ""
    response = client.list_voices(language_code=lang)
    out: list[VoiceInfo] = []
    for v in response.voices:
        gender = getattr(v.ssml_gender, "name", None) or str(v.ssml_gender)
        out.append(
            VoiceInfo(
                name=v.name,
                language_codes=list(v.language_codes),
                ssml_gender=str(gender),
                natural_sample_rate_hz=int(v.natural_sample_rate_hertz),
            )
        )
    return out
