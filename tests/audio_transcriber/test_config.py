"""Use cases for Settings (config.py)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from audio_transcriber.config import Settings


def _settings(**overrides) -> Settings:
    """Build Settings isolated from the real .env / host env."""
    overrides.setdefault('telegram_bot_token', 'test-token')
    return Settings(_env_file=None, **overrides)  # type: ignore


# UC1 — token is required
def test_missing_token_fails_clearly(monkeypatch):
    monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore


# UC2 — defaults hold when unset
def test_defaults():
    settings = _settings()
    assert settings.transcription_api_base_url == 'http://localhost:8000'
    assert settings.transcription_request_timeout == 30.0  # noqa: PLR2004
    assert settings.transcription_poll_interval == 2.0  # noqa: PLR2004
    assert settings.transcription_poll_timeout == 300.0  # noqa: PLR2004


# UC3 — unknown env vars are ignored
def test_unknown_env_vars_ignored(monkeypatch):
    monkeypatch.setenv('SOME_UNRELATED_VAR', 'whatever')
    settings = _settings()
    assert not hasattr(settings, 'some_unrelated_var')


# UC4 — base URL is overridable from env
def test_base_url_overridable_from_env(monkeypatch):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test-token')
    monkeypatch.setenv(
        'TRANSCRIPTION_API_BASE_URL', 'https://transcribe.example.com'
    )
    settings = Settings(_env_file=None)  # type: ignore
    assert settings.transcription_api_base_url == (
        'https://transcribe.example.com'
    )


# UC5 — timeouts/poll interval are overridable from env (string -> float)
def test_timeouts_overridable_from_env(monkeypatch):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'test-token')
    monkeypatch.setenv('TRANSCRIPTION_REQUEST_TIMEOUT', '10')
    monkeypatch.setenv('TRANSCRIPTION_POLL_INTERVAL', '1.5')
    monkeypatch.setenv('TRANSCRIPTION_POLL_TIMEOUT', '60')
    settings = Settings(_env_file=None)  # type: ignore
    assert settings.transcription_request_timeout == 10.0  # noqa: PLR2004
    assert settings.transcription_poll_interval == 1.5  # noqa: PLR2004
    assert settings.transcription_poll_timeout == 60.0  # noqa: PLR2004
