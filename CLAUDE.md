# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A **Telegram bot that transcribes voice/audio messages** by calling a remote
transcription REST API and replies with the text. A user sends a voice note → the
bot submits it to the API and polls until it's done → it edits its
"Transcribing…" reply into the transcript.

The design separates four concerns so new input/output surfaces are additive:
- **`Transcriber`** (core) — wraps an HTTP client that submits audio to a remote
  transcription API and polls for the result; knows nothing about Telegram.
- **`Channel`** (adapter) — captures incoming audio *and* relays the transcript
  back on the same surface. `Channel` is an ABC; adding Slack/Discord/etc. later
  is a new subclass file, not a refactor.
- **`ChannelManager`** (registry/ownership) — singleton that owns the shared
  `Transcriber` instance and the list of registered channel classes. Adding a
  future channel means appending its class to `ChannelManager.channel_classes`.
- **`Settings`** (config) — typed configuration from env / `.env`.

Both `Transcriber` and `ChannelManager` are singletons (via the `Singleton`
metaclass), ensuring a single shared HTTP-backed transcriber and channel registry
across the process.

## Architecture

Data flow: Telegram voice/audio → download in-memory (`io.BytesIO`, no temp file)
→ `Transcriber.transcribe` (POSTs to the remote API, then polls until done) run off
the event loop via `asyncio.to_thread` → reply.

- [audio_transcriber/config.py](audio_transcriber/config.py) — `Settings`
  (pydantic-settings): the transcription API base URL, request timeout, and
  poll interval/timeout.
- [audio_transcriber/singleton.py](audio_transcriber/singleton.py) — `Singleton`
  metaclass shared by `Transcriber` and `ChannelManager`.
- [audio_transcriber/transcriber.py](audio_transcriber/transcriber.py) —
  `Transcriber` (singleton) POSTs audio (multipart) to
  `{base_url}/api/v1/transcriptions`, then polls
  `GET {base_url}/api/v1/transcriptions/{job_id}` until the job is
  `completed`/`failed` or the poll timeout elapses;
  `transcribe(audio, *, filename, content_type, language=None)` returns the
  transcript text. Synchronous/blocking (uses `httpx.Client`) — always call it off
  the async loop.
- [audio_transcriber/channels/base.py](audio_transcriber/channels/base.py) —
  `Channel` ABC (the extension seam): `run()` blocks while listening + relaying.
- [audio_transcriber/channels/telegram.py](audio_transcriber/channels/telegram.py) —
  `TelegramChannel`: long-polling bot (python-telegram-bot, async) handling
  `filters.VOICE | filters.AUDIO`.
- [audio_transcriber/channels/manager.py](audio_transcriber/channels/manager.py) —
  `ChannelManager` (singleton) registers channel classes, builds the shared
  `Transcriber` once, and fans out `run()` to each channel.
- [main.py](main.py) — entrypoint: loads `Settings`, builds `ChannelManager`,
  calls `.run()`.

## Environment & commands

Uses [uv](https://docs.astral.sh/uv/) (`uv.lock`, `.python-version`); Python ≥3.13.

```bash
uv sync                      # install deps
cp .env.example .env         # then set TELEGRAM_BOT_TOKEN (from @BotFather)
uv run python main.py        # start the bot (long polling)
uv run ruff check .          # lint
uv run ruff format .         # format
```

## Configuration

Env vars (see [.env.example](.env.example)); `.env` is loaded automatically and is
gitignored:
- `TELEGRAM_BOT_TOKEN` (required)
- `TRANSCRIPTION_API_BASE_URL` (default `http://localhost:8000`)
- `TRANSCRIPTION_REQUEST_TIMEOUT` (default `30` seconds, per HTTP call)
- `TRANSCRIPTION_POLL_INTERVAL` (default `2` seconds between job-status polls)
- `TRANSCRIPTION_POLL_TIMEOUT` (default `300` seconds total budget per job)

[main.ipynb](main.ipynb) is kept only as a historical faster-whisper experiment —
the bot no longer runs Whisper locally, so this notebook is fully obsolete and not
the entrypoint.
