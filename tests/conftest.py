"""Centralized fixtures for the test suite.

Everything heavy (the Whisper model, the Telegram network surface) is faked
here so tests run offline, deterministically, and in milliseconds.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

import audio_transcriber.transcriber as transcriber_mod
from audio_transcriber.config import Settings
from audio_transcriber.transcriber import Transcriber


@pytest.fixture
def settings() -> Settings:
    """A valid Settings instance isolated from the real .env / host env."""
    return Settings(telegram_bot_token='test-token', _env_file=None)


# --- Transcriber (faster-whisper) fakes -------------------------------------


@dataclass
class _Segment:
    """Stand-in for a faster-whisper segment (only ``.text`` is read)."""

    text: str


@dataclass
class _Info:
    """Stand-in for the detection info returned alongside segments."""

    language: str = 'en'
    language_probability: float = 0.99


class _RecordingModel:
    """Captures how :class:`Transcriber` builds the Whisper model."""

    def __init__(
        self, model_size: str, *, device: str, compute_type: str
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type


class _FakePipeline:
    """Returns canned segments and records the ``transcribe`` call."""

    def __init__(self, segments: list[_Segment], info: _Info) -> None:
        self._segments = segments
        self._info = info
        self.model: _RecordingModel | None = None
        self.last_audio: object = None
        self.last_batch_size: int | None = None

    def transcribe(self, audio, batch_size):  # noqa: ANN001
        self.last_audio = audio
        self.last_batch_size = batch_size
        return self._segments, self._info


@pytest.fixture
def make_transcriber(settings: Settings, monkeypatch):
    """Factory building a :class:`Transcriber` with a faked pipeline.

    Pass the segment texts each test wants back; the resulting transcriber's
    ``_pipeline`` (a :class:`_FakePipeline`) and ``_pipeline.model`` are
    reachable for call assertions.
    """

    def _make(
        *,
        texts: tuple[str, ...] = (),
        language: str = 'en',
        language_probability: float = 0.99,
    ) -> Transcriber:
        pipeline = _FakePipeline(
            [_Segment(text) for text in texts],
            _Info(language, language_probability),
        )

        def _build_pipeline(*, model):  # noqa: ANN001
            pipeline.model = model
            return pipeline

        monkeypatch.setattr(transcriber_mod, 'WhisperModel', _RecordingModel)
        monkeypatch.setattr(
            transcriber_mod, 'BatchedInferencePipeline', _build_pipeline
        )
        return Transcriber(settings)

    return _make


# --- Telegram fakes ---------------------------------------------------------


@pytest.fixture
def fake_transcriber() -> MagicMock:
    """A transcriber the channel can call: only ``.transcribe`` matters."""
    transcriber = MagicMock()
    transcriber.transcribe = MagicMock(return_value='hello world')
    return transcriber


def _build_media(*, download: bytes, get_file_error: Exception | None):
    """A fake Telegram media object (voice/audio) with an async download."""
    media = MagicMock()
    if get_file_error is not None:
        media.get_file = AsyncMock(side_effect=get_file_error)
        return media
    tg_file = MagicMock()
    tg_file.download_as_bytearray = AsyncMock(return_value=bytearray(download))
    media.get_file = AsyncMock(return_value=tg_file)
    return media


@pytest.fixture
def make_update():
    """Factory building a fake Telegram ``Update``.

    The reply ack is reachable via ``update.message.reply_text.return_value``
    and its ``edit_text`` is an ``AsyncMock``.
    """

    def _make(
        *,
        has_message: bool = True,
        voice: bool = False,
        audio: bool = False,
        download: bytes = b'audio-bytes',
        get_file_error: Exception | None = None,
    ) -> MagicMock:
        update = MagicMock()
        if not has_message:
            update.message = None
            return update

        message = MagicMock()
        ack = MagicMock()
        ack.edit_text = AsyncMock()
        message.reply_text = AsyncMock(return_value=ack)
        message.voice = (
            _build_media(download=download, get_file_error=get_file_error)
            if voice
            else None
        )
        message.audio = (
            _build_media(download=download, get_file_error=get_file_error)
            if audio
            else None
        )
        update.message = message
        return update

    return _make
