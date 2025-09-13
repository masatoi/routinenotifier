# Repository Guidelines

## Project Structure & Module Organization
- `routinenotifier/`: Source package
  - `cli.py` (Typer CLI), `config.py` (pydantic models), `scheduler.py` (loop), `tts.py` (Google TTS), `audio.py` (playback), `__init__.py`.
- `tests/`: Pytest suites (`test_*.py`).
- `examples/`: Sample configs (`schedule.json`, `voice.json`).
- `instructions/`, `prd/`: Task directions and product requirements.
- Root: `pyproject.toml`, `.pre-commit-config.yaml`, `README.md`.

## Build, Test, and Development Commands
- Create venv + install (editable):
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -e .`
- Run CLI (installed):
  - `routinenotifier validate examples/schedule.json`
  - `routinenotifier run --config examples/schedule.json`
  - `routinenotifier speak "こんにちは" --voice-config examples/voice.json`
  - `routinenotifier voices -l ja-JP`
- Run CLI (module form): `python -m routinenotifier.cli …`
- Tests: `PYTHONPATH=. pytest -q`
- Format: `python -m ruff format .`
- Lint: `python -m ruff check .` (autofix: `--fix`)
- Types: `python -m mypy .`
- Pre-commit: `pre-commit install` then commit normally.

## Coding Style & Naming Conventions
- Language: Python 3.10+; use type annotations in `routinenotifier/*` (mypy-enforced).
- Formatting: Ruff formatter (`ruff format`), line length 100.
- Linting: `ruff` with pycodestyle/pyflakes/isort/bugbear/pyupgrade rules.
- Names: modules/files `snake_case.py`; functions/vars `snake_case`; classes `CamelCase`.

## Testing Guidelines
- Framework: `pytest`.
- Location/names: tests in `tests/`, files `test_*.py`.
- Scope: Prefer fast, unit-level tests; avoid networked GCP calls (use `DummyTTS`).
- Run locally before PR: `pytest -q` and ensure green.

## Commit & Pull Request Guidelines
- Commits: small, focused, imperative style (e.g., "Add CLI speak command").
- Reference issues in messages/PRs when applicable.
- PR checklist:
  - Describe change, rationale, and how to validate (commands/examples).
  - Ensure: `ruff format`, `ruff check`, `mypy`, and `pytest` all pass.
  - Include docs updates (README/examples) for user-facing changes.
  - Update design docs under `design/` when behavior, interfaces, or architecture changes.

## Design Docs Updates
- Keep `design/` in sync with code changes (especially `design/implementation.md`).
- Document:
  - What changed (modules/functions, CLI flags, config schema).
  - Why it changed (trade-offs, alternatives considered briefly).
  - How to use it (short commands or JSON snippets).
- Example: after adding `--pitch` and `voice.json` schema, update sections describing `VoiceConfig`, CLI flags, and examples.

## Security & Configuration Tips
- Do not commit secrets. Use ADC for GCP:
  - `export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/application_default_credentials.json"`
- Enable the GCP Text-to-Speech API in your project before running.
