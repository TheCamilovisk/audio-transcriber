"""Use cases for the Telegram channel (channels/telegram.py)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import audio_transcriber.channels.telegram as telegram_mod
from audio_transcriber.channels.telegram import TelegramChannel


@pytest.fixture
def channel(fake_transcriber, settings) -> TelegramChannel:
    return TelegramChannel(fake_transcriber, settings)


@pytest.fixture
def context() -> MagicMock:
    return MagicMock()


# UC10 — /start replies with usage instructions
async def test_start_replies_with_usage(channel, context, make_update):
    update = make_update()
    await channel._on_start(update, context)
    update.message.reply_text.assert_awaited_once_with(
        "Send me a voice message or audio file and I'll transcribe it."
    )


# UC10 — /start is a no-op without a message
async def test_start_ignores_missing_message(channel, context, make_update):
    update = make_update(has_message=False)
    await channel._on_start(update, context)  # must not raise


# UC11 — a voice message is acked then edited into the transcript
async def test_voice_message_transcribed(channel, context, make_update):
    update = make_update(voice=True)
    await channel._on_audio(update, context)
    update.message.reply_text.assert_awaited_once_with('Transcribing…')
    ack = update.message.reply_text.return_value
    ack.edit_text.assert_awaited_once_with('hello world')


# UC11 — an audio file works the same way
async def test_audio_message_transcribed(channel, context, make_update):
    update = make_update(audio=True)
    await channel._on_audio(update, context)
    ack = update.message.reply_text.return_value
    ack.edit_text.assert_awaited_once_with('hello world')


# UC11 — the downloaded bytes reach the transcriber as a seekable buffer
async def test_downloaded_bytes_reach_transcriber(
    channel, context, make_update, fake_transcriber
):
    update = make_update(voice=True, download=b'the-audio')
    await channel._on_audio(update, context)
    buf = fake_transcriber.transcribe.call_args.args[0]
    assert buf.getvalue() == b'the-audio'


# UC12 — voice is preferred over audio when both are present
async def test_prefers_voice_over_audio(channel, context, make_update):
    update = make_update(voice=True, audio=True)
    await channel._on_audio(update, context)
    update.message.voice.get_file.assert_awaited_once()
    update.message.audio.get_file.assert_not_awaited()


# UC13 — empty transcript becomes the "no speech" notice
async def test_empty_transcript_shows_notice(
    channel, context, make_update, fake_transcriber
):
    fake_transcriber.transcribe.return_value = ''
    update = make_update(voice=True)
    await channel._on_audio(update, context)
    ack = update.message.reply_text.return_value
    ack.edit_text.assert_awaited_once_with('(no speech detected)')


# UC14 — a download failure becomes an apology, no crash
async def test_download_failure_apologizes(channel, context, make_update):
    update = make_update(voice=True, get_file_error=RuntimeError('network'))
    await channel._on_audio(update, context)
    ack = update.message.reply_text.return_value
    ack.edit_text.assert_awaited_once_with(
        "Sorry, I couldn't transcribe that audio."
    )


# UC14 — a transcription failure also becomes an apology
async def test_transcription_failure_apologizes(
    channel, context, make_update, fake_transcriber
):
    fake_transcriber.transcribe.side_effect = RuntimeError('boom')
    update = make_update(voice=True)
    await channel._on_audio(update, context)
    ack = update.message.reply_text.return_value
    ack.edit_text.assert_awaited_once_with(
        "Sorry, I couldn't transcribe that audio."
    )


# UC15 — no message is ignored silently
async def test_missing_message_ignored(channel, context, make_update):
    update = make_update(has_message=False)
    await channel._on_audio(update, context)  # must not raise


# UC15 — a message with neither voice nor audio is ignored silently
async def test_message_without_media_ignored(channel, context, make_update):
    update = make_update(voice=False, audio=False)
    await channel._on_audio(update, context)
    update.message.reply_text.assert_not_awaited()


# UC16 — transcription is dispatched off the event loop via asyncio.to_thread
async def test_transcription_runs_off_event_loop(
    channel, context, make_update, fake_transcriber, monkeypatch
):
    calls = []

    async def fake_to_thread(func, *args):
        calls.append((func, args))
        return func(*args)

    monkeypatch.setattr(telegram_mod.asyncio, 'to_thread', fake_to_thread)
    update = make_update(voice=True)
    await channel._on_audio(update, context)

    assert len(calls) == 1
    func, args = calls[0]
    assert func is fake_transcriber.transcribe
    assert args[0].getvalue() == b'audio-bytes'
