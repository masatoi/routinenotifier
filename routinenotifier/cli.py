from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .config import AppConfig, ConfigError, VoiceConfig, load_config, load_voice_config
from .scheduler import run_forever
from .tts import GoogleTTS, list_voices

app = typer.Typer(help="Routine Notifier: speak scheduled messages via Google TTS")


def _echo_schedules(cfg: AppConfig) -> None:
    for s in cfg.schedules:
        hhmm = f"{s.time.hour:02d}:{s.time.minute:02d}"
        days = ",".join(d.value for d in s.days)
        typer.echo(f"- {s.name} @ {hhmm} on [{days}]")


_CONFIG_ARG = typer.Argument(
    ..., exists=True, readable=True, help="Path to JSON config"
)


@app.command()
def validate(config: Path = _CONFIG_ARG) -> None:
    """Validate and summarize the config file."""
    try:
        cfg = load_config(config)
    except ConfigError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1) from e
    typer.secho("Config is valid. Schedules:", fg=typer.colors.GREEN)
    _echo_schedules(cfg)


_CONFIG_OPT = typer.Option(
    Path("schedule.json"),
    exists=True,
    readable=True,
    help="Path to JSON config",
)
_LANG_OPT = typer.Option("ja-JP", help="Language code for TTS")
_VOICE_OPT = typer.Option(None, help="Specific voice name (optional)")
_RATE_OPT = typer.Option(1.0, help="Speaking rate for TTS (0.25 - 4.0)")
_PITCH_OPT = typer.Option(0.0, help="Pitch in semitones (-20.0..20.0)")
_ENC_OPT = typer.Option("MP3", help="Audio encoding: MP3, LINEAR16, OGG_OPUS")
_INTERVAL_OPT = typer.Option(1.0, help="Polling interval in seconds")


@app.command()
def run(
    config: Path = _CONFIG_OPT,
    language_code: str = _LANG_OPT,
    voice_name: Optional[str] = _VOICE_OPT,
    speaking_rate: float = _RATE_OPT,
    pitch: float = _PITCH_OPT,
    audio_encoding: str = _ENC_OPT,
    check_interval: float = _INTERVAL_OPT,
    voice_config: Optional[Path] = typer.Option(
        None, help="Path to JSON with voice settings (overrides voice flags)"
    ),
) -> None:
    """Run the scheduler to speak messages at scheduled times."""
    try:
        cfg = load_config(config)
    except ConfigError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1) from e

    typer.secho("Loaded schedules:", fg=typer.colors.BLUE)
    _echo_schedules(cfg)
    typer.echo("Starting scheduler. Press Ctrl+C to stop.")

    try:
        tts = GoogleTTS()
    except Exception as e:  # pragma: no cover - import path
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=2) from e

    # Load voice settings from file if provided
    if voice_config is not None:
        try:
            vcfg: VoiceConfig = load_voice_config(voice_config)
        except ConfigError as e:
            typer.secho(str(e), fg=typer.colors.RED)
            raise typer.Exit(code=1) from e
        language_code = vcfg.language_code
        voice_name = vcfg.voice_name
        speaking_rate = vcfg.speaking_rate
        pitch = vcfg.pitch
        audio_encoding = vcfg.audio_encoding

    try:
        run_forever(
            cfg,
            tts,
            language_code=language_code,
            voice_name=voice_name,
            speaking_rate=speaking_rate,
            pitch=pitch,
            audio_encoding=audio_encoding,
            check_interval_sec=check_interval,
        )
    except KeyboardInterrupt:
        typer.echo("Stopped.")


@app.command()
def voices(
    language_code: str = typer.Option(
        "", "--language-code", "-l", help="Optional BCP-47 code (e.g., ja-JP)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List available Google TTS voices."""
    try:
        voices_list = list_voices(language_code or None)
    except Exception as e:  # pragma: no cover - network/credentials
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=2) from e

    if json_output:
        import json as _json
        payload = [
            {
                "name": v.name,
                "language_codes": v.language_codes,
                "ssml_gender": v.ssml_gender,
                "natural_sample_rate_hz": v.natural_sample_rate_hz,
            }
            for v in voices_list
        ]
        typer.echo(_json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if not voices_list:
        typer.echo("No voices found.")
        return

    typer.secho("Available voices:", fg=typer.colors.BLUE)
    for v in voices_list:
        langs = ",".join(v.language_codes)
        rate = f"{v.natural_sample_rate_hz} Hz"
        typer.echo(f"- {v.name} | {langs} | {v.ssml_gender} | {rate}")


@app.command()
def speak(
    text: str = typer.Argument(..., help="Text to speak once"),
    language_code: str = _LANG_OPT,
    voice_name: Optional[str] = _VOICE_OPT,
    speaking_rate: float = _RATE_OPT,
    pitch: float = _PITCH_OPT,
    audio_encoding: str = _ENC_OPT,
    voice_config: Optional[Path] = typer.Option(
        None, help="Path to JSON with voice settings (overrides voice flags)"
    ),
) -> None:
    """Synthesize and play a single line of text."""
    # Apply voice config if provided
    if voice_config is not None:
        try:
            vcfg = load_voice_config(voice_config)
        except ConfigError as e:
            typer.secho(str(e), fg=typer.colors.RED)
            raise typer.Exit(code=1) from e
        language_code = vcfg.language_code
        voice_name = vcfg.voice_name
        speaking_rate = vcfg.speaking_rate
        pitch = vcfg.pitch
        audio_encoding = vcfg.audio_encoding

    try:
        tts = GoogleTTS()
    except Exception as e:  # pragma: no cover - import path
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=2) from e

    from .audio import play_audio_bytes

    audio = tts.synthesize(
        text,
        language_code=language_code,
        voice_name=voice_name,
        speaking_rate=speaking_rate,
        pitch=pitch,
        audio_encoding=audio_encoding,
    )
    play_audio_bytes(audio, encoding=audio_encoding)
