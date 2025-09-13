# 実装方針とアーキテクチャ概要

本ドキュメントは、現在のCLI版MVPの実装方針・設計判断・拡張点をまとめたものです。

## 目的とスコープ
- 目的: ローカルのJSON設定に従い、Google Cloud Text‑to‑Speech (TTS) で音声通知を行う。
- スコープ: CLI常駐・音声合成・再生に限定。DB/GUIは対象外。

## 全体構成
```
ユーザー ─(JSON編集)→ schedule.json / voice.json
     │
     └─(起動時読込)→ routinenotifier (CLI)
                       ├─ config: JSON検証
                       ├─ scheduler: 時刻判定・起動
                       ├─ tts: Google TTS合成
                       └─ audio: OS別再生
```

## モジュール設計
- `routinenotifier/config.py`
  - `Schedule`, `AppConfig`: スケジュール定義。`HH:MM` の厳密検証、`Weekday` 正規化。
  - `VoiceConfig`: 音声設定（`language_code`, `voice_name`, `speaking_rate`, `pitch`, `audio_encoding`）。`pitch` は semitone（-20.0..20.0）。
  - `load_config`, `load_voice_config`: JSON読み込み＋`pydantic`で検証。エラーは `ConfigError` に正規化。
- `routinenotifier/tts.py`
  - `Synthesizer` Protocol: 切替可能なTTS実装の抽象。
  - `GoogleTTS`: `TextToSpeechClient` を遅延importで使用。`AudioConfig` に `speaking_rate` と `pitch` を反映。
  - `list_voices(language_code)`: 利用可能な音声の列挙。
  - `DummyTTS`: テスト用の無音WAV出力（ネットワーク不要）。
  - `CachingSynthesizer`（新規）: 合成前にキャッシュを確認し、未命中時のみ合成→保存→再生。
    - キー: `text + language_code + voice_name + speaking_rate + pitch + audio_encoding + CACHE_VERSION` をSHA-256でハッシュ化。
    - 保存先: 既定は XDG Cache (`~/.cache/routinenotifier/`)。`--cache-dir` で上書き可。
    - 容量制御: `--cache-max-mb`（既定200MB）。LRU（mtime）で刈り取り。
    - 迂回: `--no-cache` で無効化可能。
- `routinenotifier/audio.py`
  - 合成バイト列を一時ファイルへ書き出し、OS標準プレイヤー（macOS: `afplay` など、Linux: `aplay/mpg123/ffplay` など、Windows: 既定アプリ）で再生。
  - プレイヤーが無い場合はパスを表示（手動再生可能）。
- `routinenotifier/scheduler.py`
  - `due_indices(cfg, now)`: 現在の分と曜日に一致するエントリを算出。
  - `run_forever(...)`: 1秒ポーリングで分単位の一致を検出。1日1回の再通知抑止（midnightでリセット）。
- `routinenotifier/cli.py`（Typer）
  - `validate`: 設定検証。
  - `run`: スケジューラ起動。フラグ（`--language-code`, `--voice-name`, `--speaking-rate`, `--pitch`, `--audio-encoding`）と `--voice-config`（JSON優先）をサポート。
  - `speak`: 指定テキストを単発合成・再生。
  - `voices`: 利用可能な音声の一覧表示（`--language-code`, `--json`）。

## 時刻・タイムゾーン
- 現状: 実行マシンのローカル時刻を使用（例: OSがJSTならJST）。
- 将来: `--timezone` や設定ファイルでのTZ指定を拡張候補。

## 設定ファイル仕様
- `examples/schedule.json`
  - `schedules[]`: `{ name, time:"HH:MM", days:[mon..sun], message }`
- `examples/voice.json`
  - `{ language_code, voice_name?, speaking_rate, pitch, audio_encoding }`

## エラーハンドリング
- 設定不正: `ConfigError` をCLIで整形出力して非0終了。
- 依存未設定: `google-cloud-texttospeech` 未導入・ADC未設定時は実行時に明瞭なエラー文言。

## 品質管理と開発フロー
- フォーマット: `black`（行長100）
- Lint: `ruff`（pycodestyle/pyflakes/isort/bugbear/pyupgrade）
- 型: `mypy`（`routinenotifier` 配下で厳格チェック）
- テスト: `pytest`。ネットワーク不要の単体テストを重視（`DummyTTS`利用）。

## セキュリティ/設定
- 資格情報は環境変数経由で指定: `GOOGLE_APPLICATION_CREDENTIALS`。
- GCPプロジェクトで TTS API を有効化。

## 拡張方針（今後）
- タイムゾーン明示サポート、休日/例外日設定、繰り返し間隔の柔軟化。
- 合成音声キャッシュ、出力デバイス選択、音量制御。
- 他TTSプロバイダ実装（`Synthesizer`差し替え）。
- ログ整備・メトリクス、軽量UIの追加。
