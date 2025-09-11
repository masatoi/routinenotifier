Routine Notifier (CLI)

Purpose: Speak scheduled messages using Google Cloud Text-to-Speech, driven by a local JSON config.

Quick start
- Put a JSON config at `schedule.json` (see `examples/schedule.json`).
- Ensure Google Cloud credentials are available via `GOOGLE_APPLICATION_CREDENTIALS` and the Text-to-Speech API is enabled.
- Install deps with Poetry or pip, then run the CLI (see below).

Prerequisites
- Python: `>=3.10`
- GCP: Text-to-Speech API enabled on your project
- Auth: Application Default Credentials (ADC)
  - `gcloud auth application-default login` OR set the env var explicitly:
    - `export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/application_default_credentials.json"`

Install (Poetry)
- Install Poetry and run: `poetry install`

Install (pip)
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e .` (requires `pip>=23` and `setuptools`/`wheel`)

How to run
- As installed console script (recommended):
  - Validate: `routinenotifier validate examples/schedule.json`
  - Run: `routinenotifier run --config examples/schedule.json`
- As a Python module (no install):
  - Validate: `python -m routinenotifier.cli validate examples/schedule.json`
  - Run: `python -m routinenotifier.cli run --config examples/schedule.json`

Note: Do NOT run `python routinenotifier/cli.py …` — relative imports will fail. Use the module form above or the installed console script.

Config schema
- `schedules`: list of tasks with fields:
  - `name`: task label
  - `time`: `HH:MM` (24h)
  - `days`: list of `mon..sun`
  - `message`: text to speak

CLI
- `routinenotifier validate path/to/config.json` — validate config.
- `routinenotifier run --config schedule.json [--language-code ja-JP --voice-name <name> --speaking-rate 1.0 --audio-encoding MP3] [--voice-config examples/voice.json]` — run scheduler. If `--voice-config` is given, it overrides the individual voice flags.
- `routinenotifier voices [-l ja-JP] [--json]` — list available Google TTS voices (optionally filter by language; `--json` for machine-readable output).
- `routinenotifier speak "こんにちは" [--language-code ja-JP --voice-name <name> --speaking-rate 1.0 --audio-encoding MP3] [--voice-config examples/voice.json]` — synthesize and play a single line of text. If `--voice-config` is given, it overrides the individual voice flags.

Voice config JSON
- Example: `examples/voice.json`
  - `language_code`: BCP-47 code (`ja-JP`, `en-US`, ...)
  - `voice_name`: specific voice name (optional)
  - `speaking_rate`: float [0.25, 4.0]
  - `pitch`: float [-20.0, 20.0] (semitones)
  - `audio_encoding`: `MP3` | `LINEAR16` | `OGG_OPUS`

Scheduling behavior
- Timezone: Interprets `time` in your machine’s local timezone (e.g., JST if your OS is set to Asia/Tokyo).
- Trigger: Fires once per task per day when the system clock matches `HH:MM`.
- Interval: Polls every second; adjustable via `--check-interval`.

Audio output
- macOS: uses `afplay` or `open`
- Linux: tries `aplay`/`paplay`/`mpg123`/`ffplay`
- Windows: opens the default audio handler
- If no player is found, the synthesized audio is saved to a temp file and the path is printed.

Dev tools
- Format: `black .`
- Lint: `ruff check .`
- Types: `mypy .`
- Test: `pytest -q`
