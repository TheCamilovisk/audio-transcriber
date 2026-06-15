# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A **Telegram bot that transcribes voice/audio messages** using
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) and replies with the
text. A user sends a voice note → the bot transcribes it → it edits its "Transcribing…"
reply into the transcript.

The design separates three concerns so new input/output surfaces are additive:
- **`Transcriber`** (core) — wraps the Whisper model; knows nothing about Telegram.
- **`Channel`** (adapter) — captures incoming audio *and* relays the transcript
  back on the same surface. `Channel` is an ABC; adding Slack/Discord/etc. later
  is a new subclass file, not a refactor.
- **`Settings`** (config) — typed configuration from env / `.env`.

## Architecture

Data flow: Telegram voice/audio → download in-memory (`io.BytesIO`, no temp file)
→ `Transcriber.transcribe` run off the event loop via `asyncio.to_thread` → reply.

- [audio_transcriber/config.py](audio_transcriber/config.py) — `Settings`
  (pydantic-settings). Resolves `DEVICE=auto` to cuda/cpu and derives `compute_type`.
- [audio_transcriber/transcriber.py](audio_transcriber/transcriber.py) —
  `Transcriber` builds `WhisperModel` + `BatchedInferencePipeline` once; `transcribe`
  accepts a path, a seekable file-like object, or an ndarray and returns the joined
  transcript. Blocking/CPU-bound — always call it off the async loop.
- [audio_transcriber/channels/base.py](audio_transcriber/channels/base.py) —
  `Channel` ABC (the extension seam): `run()` blocks while listening + relaying.
- [audio_transcriber/channels/telegram.py](audio_transcriber/channels/telegram.py) —
  `TelegramChannel`: long-polling bot (python-telegram-bot, async) handling
  `filters.VOICE | filters.AUDIO`.
- [main.py](main.py) — entrypoint: loads `Settings`, builds `Transcriber`, hands it
  to `TelegramChannel`, calls `.run()`.

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
- `WHISPER_MODEL` (default `turbo`)
- `DEVICE` — `cpu` | `cuda` | `auto` (default `cpu`)
- `COMPUTE_TYPE` (optional; defaults: `float16` on cuda, `int8` on cpu)
- `BATCH_SIZE` (default `16`)

**GPU note:** `DEVICE=cuda`/`auto`-on-GPU requires the matching CUDA/cuDNN libs for
ctranslate2 on the host. The `cpu`/`int8` default needs none.

[main.ipynb](main.ipynb) is kept only as the original faster-whisper reference
experiment — it is not the entrypoint.
