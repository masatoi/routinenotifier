# 家庭内生活習慣改善通知システム MVP要件定義書 (CLI版)

## 1. はじめに

### 1.1. プロジェクトの目的

本プロジェクトは、設定ファイルに基づき、GCPのText-to-Speech (TTS) APIを利用してタスクを音声で通知する、実用最小限のコマンドラインツールを構築することを目的とする。

### 1.2. MVPのスコープ

MVPでは、ユーザーがローカルマシン上で設定ファイル（例：JSON形式）を直接編集し、そのスケジュールに従って常駐プログラムが自動で音声通知を行うというコア機能に絞る。Web UIやデータベースはスコープ外とする。

## 2. システム概要

### 2.1. システム構成図（CLI版）

```

[ユーザー] --(ファイルを編集)--\> [設定ファイル (schedule.json)]
|
| (起動時に読み込み)
V
[常駐CLIツール (ローカルマシン)] --+------\> [GCP TTS API] (音声合成)
|
V
[スピーカー] (音声出力)

````

### 2.2. 利用技術（想定）

* **ツール開発言語**: Python

* **音声合成**: Google Cloud Text-to-Speech API

* **設定**: JSON形式のファイル

* **実行環境**: ローカルマシン (Windows, macOS, Linux)

### 2.3. 開発ツールチェーン

本ツールの開発においては、コードの品質、保守性、開発効率を向上させるため、以下のモダンなPythonツールチェーンを採用する。

| **カテゴリ** | **ツール** | **役割** | 
| ------------ | ---------- | -------- |
| **CLIフレームワーク** | `Typer` | コマンドライン引数の処理、ヘルプ生成を担う。 | 
| **データバリデーション** | `pydantic` | 設定ファイル(JSON)の読み込みと厳密な検証を行う。 | 
| **依存関係/環境管理** | `Poetry` | ライブラリのバージョン管理と仮想環境を統一的に管理する。 | 
| **フォーマッター** | `Ruff` (formatter) | `ruff format` による自動整形。 | 
| **リンター** | `Ruff` | `ruff check` による静的解析。 | 
| **型チェック** | `mypy` | 静的な型チェックを行い、型に起因するエラーを未然に防ぐ。 | 
| **テストフレームワーク** | `pytest` | 機能が正しく動作することを保証するためのテストを記述・実行する。 | 
| **ワークフロー自動化** | `pre-commit` | git commit前にフォーマットやリントを自動実行し、品質を担保する。 | 

補足: GitHub Actions 上で pytest を実行し、README にはバッジを表示する。

## 3. 機能要件

### 3.1. 設定ファイル管理機能【必須】

ユーザーがスケジュールをJSONファイルで直接定義できる機能。

* **3.1.1. JSONによるタスク設定**

  * ユーザーは、以下のような構造のJSONファイルを手動で編集してタスクを設定する。

    ```
    {
      "schedules": [
        {
          "name": "起床",
          "time": "07:00",
          "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
          "message": "おはようございます。起きる時間です。"
        },
        {
          "name": "終業",
          "time": "19:00",
          "days": ["mon", "tue", "wed", "thu", "fri"],
          "message": "業務終了の時間です。お疲れ様でした。"
        }
      ]
    }
    
    ```

* **3.1.2. 音声設定 (voice.json)**

  * 音声合成のパラメータを別JSONで管理できる。

    ```
    {
      "language_code": "ja-JP",
      "voice_name": "ja-JP-Standard-A",
      "speaking_rate": 1.0,
      "pitch": 0.0,
      "audio_encoding": "MP3"
    }
    ```

  * CLIフラグ（--language-code/--voice-name/--speaking-rate/--pitch/--audio-encoding）よりも `--voice-config` で指定されたJSONが優先される。

### 3.2. CLIコマンド【実装済】

* `validate <config.json>`: 設定の検証と概要表示。
* `run --config <schedule.json> [--voice-config <voice.json>]`:
  常駐スケジューラを起動し、指定時刻に音声再生。
* `speak "テキスト" [--voice-config <voice.json>]`: 単発で合成して再生。
* `voices [-l ja-JP] [--json]`: 利用可能なTTS音声の一覧。
* `cache-clear [-y] [--cache-dir <path>]`: 合成済み音声キャッシュを削除。

### 3.3. スケジューラ仕様【実装済】

* 分精度でトリガー（`HH:MM` が一致した際に発火）。
* 同一日・同一エントリは1度のみ実行（翌日0時でリセット）。
* タイムゾーンは実行マシンのローカル時刻に従う。
* ポーリング間隔は既定1秒（`--check-interval`で変更可）。

### 3.4. 音声合成・再生【実装済】

* Google Cloud Text‑to‑Speech を利用。`speaking_rate` と `pitch` を反映。
* OS標準のプレイヤーで再生（macOS: `afplay`、Linux: `aplay/mpg123/ffplay`、Windows: 既定アプリ）。
* プレイヤー未検出時は一時ファイルに保存しパスを通知。

### 3.5. 合成音声キャッシュ【実装済】

* 同一テキスト＋音声パラメータ（言語/声/話速/ピッチ/エンコーディング）でキャッシュをヒットさせ、API呼び出しを省略。
* 既定は XDG キャッシュディレクトリ配下（例: `~/.cache/routinenotifier/`）。
* サイズ上限（既定200MB）でLRU刈り取り。`--no-cache`で無効化、`--cache-dir`/`--cache-max-mb`で制御可能。

## 4. 非機能要件（品質/運用）

* コード品質: `ruff format`/`ruff check`/`mypy` を通過すること。
* テスト: `pytest` によるユニットテストを用意し、CIで自動実行。
* セキュリティ: 認証情報は `GOOGLE_APPLICATION_CREDENTIALS` 等の環境変数/ADCを用い、リポジトリに秘密情報を含めない。
