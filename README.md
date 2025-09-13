# Routine Notifier (CLI)

[![Tests](https://github.com/masatoi/routinenotifier/actions/workflows/tests.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/tests.yml)

Speak scheduled messages using Google Cloud Text‑to‑Speech, driven by local JSON files.

## Quick Start
1) Create a schedule JSON (see examples below).
2) Ensure GCP credentials and TTS API are set up.
3) Install dependencies and run the CLI.

## Prerequisites
- Python: >= 3.10
- GCP: Enable the Text‑to‑Speech API on your project
- Auth: Application Default Credentials (ADC)

Set ADC via gcloud or env var:

```bash
gcloud auth application-default login
# or
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/application_default_credentials.json"
```

## Installation

Using Poetry:

```bash
poetry install
```

Using pip (editable):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## How to Run

Installed console script (recommended):

```bash
routinenotifier validate examples/schedule.json
routinenotifier run --config examples/schedule.json
```

Module form (no install):

```bash
python -m routinenotifier.cli validate examples/schedule.json
python -m routinenotifier.cli run --config examples/schedule.json
```

Note: Do NOT run `python routinenotifier/cli.py …` — use the module form above or the installed script.

## Configuration

### Schedule (schedule.json)
```json
{
  "schedules": [
    {
      "name": "Wake",
      "time": "07:00",
      "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
      "message": "Good morning"
    }
  ]
}
```

### Voice (voice.json)
```json
{
  "language_code": "ja-JP",
  "voice_name": "ja-JP-Wavenet-A",
  "speaking_rate": 1.0,
  "pitch": 0.0,
  "audio_encoding": "MP3"
}
```

## CLI Commands

Validate config:

```bash
routinenotifier validate path/to/config.json
```

Run scheduler (voice flags can be overridden by --voice-config):

```bash
routinenotifier run --config schedule.json \
  --language-code ja-JP --voice-name ja-JP-Standard-A \
  --speaking-rate 1.0 --pitch 0.0 --audio-encoding MP3 \
  --voice-config examples/voice.json \
  --no-cache --cache-dir ./cache --cache-max-mb 200
```

Speak once:

```bash
routinenotifier speak "こんにちは" --voice-config examples/voice.json
```

List voices:

```bash
routinenotifier voices -l ja-JP --json
```

Clear cache:

```bash
routinenotifier cache-clear -y --cache-dir ./cache
```

## Scheduling Behavior
- Timezone: Uses your system local time (e.g., JST if OS is Asia/Tokyo).
- Trigger: Once per task per day at exact `HH:MM`.
- Polling: Checks every second; adjustable via `--check-interval`.

## Audio Output
- macOS: `afplay` (fallback `open`)
- Linux: `aplay`/`paplay`/`mpg123`/`ffplay`
- Windows: default audio handler
- If no player is found, the synthesized audio is saved to a temp file and its path is printed.

## Caching
- Default: On‑disk cache under XDG cache (e.g., `~/.cache/routinenotifier/`).
- Key: Text + voice parameters (language/voice/rate/pitch/encoding).
- Control: `--no-cache`, `--cache-dir`, `--cache-max-mb` (0 = unlimited).
- Maintenance: `routinenotifier cache-clear -y` to purge.

## Development
```bash
# Format
black .
# Lint
python -m ruff check .
# Types
python -m mypy .
# Tests
PYTHONPATH=. pytest -q
```
