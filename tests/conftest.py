"""Centralized fixtures for the test suite.

Everything heavy (the remote transcription API, the Telegram network
surface) is faked here so tests run offline, deterministically, and in
milliseconds.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import respx

from audio_transcriber.config import Settings
from audio_transcriber.singleton import Singleton
from audio_transcriber.transcriber import Transcriber


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Clear singleton cache before and after every test.

    Keeps :class:`Transcriber` (and any future singleton) isolated between
    tests so each test gets a fresh instance.
    """
    Singleton._instances.clear()
    yield
    Singleton._instances.clear()


@pytest.fixture
def settings() -> Settings:
    """A valid Settings instance isolated from the real .env / host env."""
    return Settings(
        telegram_bot_token='test-token',
        transcription_poll_interval=0,
        _env_file=None,
    )


# --- Transcriber (remote transcription API) fakes ---------------------------


@pytest.fixture
def transcription_api(settings: Settings):
    """A respx mock router scoped to the configured API base URL.

    Tests register ``transcription_api.post(...)``/``.get(...)`` routes and
    can inspect ``transcription_api.calls`` afterwards.
    """
    with respx.mock(
        base_url=settings.transcription_api_base_url, assert_all_called=False
    ) as router:
        yield router


@pytest.fixture
def make_transcriber(settings: Settings) -> Transcriber:
    """Build a :class:`Transcriber` wired to ``settings``.

    Construction does no I/O — tests script the HTTP behavior via the
    ``transcription_api`` respx router.
    """
    return Transcriber(settings)


# --- Telegram fakes ---------------------------------------------------------


@pytest.fixture
def fake_transcriber() -> MagicMock:
    """A transcriber the channel can call: only ``.transcribe`` matters."""
    transcriber = MagicMock()
    transcriber.transcribe = MagicMock(return_value='hello world')
    return transcriber


def _build_media(
    *,
    download: bytes,
    get_file_error: Exception | None,
    file_name: str | None = None,
    mime_type: str | None = None,
):
    """A fake Telegram media object (voice/audio) with an async download."""
    media = MagicMock()
    media.file_name = file_name
    media.mime_type = mime_type
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

    def _make(  # noqa: PLR0913
        *,
        has_message: bool = True,
        voice: bool = False,
        audio: bool = False,
        download: bytes = b'audio-bytes',
        get_file_error: Exception | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
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
            _build_media(
                download=download,
                get_file_error=get_file_error,
                file_name=file_name,
                mime_type=mime_type,
            )
            if voice
            else None
        )
        message.audio = (
            _build_media(
                download=download,
                get_file_error=get_file_error,
                file_name=file_name,
                mime_type=mime_type,
            )
            if audio
            else None
        )
        update.message = message
        return update

    return _make
