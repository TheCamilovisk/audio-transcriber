"""Use cases for Settings (config.py)."""

from __future__ import annotations

import ctranslate2
import pytest
from pydantic import ValidationError

from audio_transcriber.config import Settings


def _settings(**overrides) -> Settings:
    """Build Settings isolated from the real .env / host env."""
    overrides.setdefault('telegram_bot_token', 'test-token')
    overrides.setdefault('device', 'cpu')
    return Settings(_env_file=None, **overrides)  # type: ignore


# UC1 — token is required
def test_missing_token_fails_clearly(monkeypatch):
    monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore


# UC2 — defaults hold when unset
def test_defaults():
    settings = _settings()
    assert settings.whisper_model == 'turbo'
    assert settings.device == 'cpu'
    assert settings.batch_size == 16  # noqa: PLR2004
    assert settings.compute_type is None


# UC3 — unknown env vars are ignored
def test_unknown_env_vars_ignored(monkeypatch):
    monkeypatch.setenv('SOME_UNRELATED_VAR', 'whatever')
    settings = _settings()
    assert not hasattr(settings, 'some_unrelated_var')


# UC4 — device resolution
@pytest.mark.parametrize('device', ['cpu', 'cuda'])
def test_explicit_device_passes_through(device):
    assert _settings(device=device).resolved_device == device


def test_auto_resolves_to_cuda_when_gpu_present(monkeypatch):
    monkeypatch.setattr(ctranslate2, 'get_cuda_device_count', lambda: 1)
    assert _settings(device='auto').resolved_device == 'cuda'


def test_auto_resolves_to_cpu_when_no_gpu(monkeypatch):
    monkeypatch.setattr(ctranslate2, 'get_cuda_device_count', lambda: 0)
    assert _settings(device='auto').resolved_device == 'cpu'


def test_auto_falls_back_to_cpu_on_detection_failure(monkeypatch):
    def _boom():
        raise RuntimeError('cuda libs missing')

    monkeypatch.setattr(ctranslate2, 'get_cuda_device_count', _boom)
    assert _settings(device='auto').resolved_device == 'cpu'


# UC5 — compute-type resolution
def test_explicit_compute_type_wins():
    settings = _settings(device='cpu', compute_type='float32')
    assert settings.resolved_compute_type == 'float32'


def test_compute_type_defaults_to_float16_on_cuda(monkeypatch):
    monkeypatch.setattr(ctranslate2, 'get_cuda_device_count', lambda: 1)
    assert _settings(device='auto').resolved_compute_type == 'float16'


def test_compute_type_defaults_to_int8_on_cpu():
    assert _settings(device='cpu').resolved_compute_type == 'int8'
