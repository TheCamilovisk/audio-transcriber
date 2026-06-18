"""Tests for the ``Singleton`` metaclass."""

from __future__ import annotations

import pytest

from audio_transcriber.singleton import Singleton


class _Counter(metaclass=Singleton):
    """Counts how many times ``__init__`` has run."""

    init_count: int = 0

    def __init__(self) -> None:
        _Counter.init_count += 1


class _Other(metaclass=Singleton):
    """A second singleton class — different cache key than ``_Counter``."""

    def __init__(self) -> None:
        self.value = 42


@pytest.fixture(autouse=True)
def _clear_singleton_cache():
    """Clear the shared cache before and after every test."""
    Singleton._instances.clear()
    yield
    Singleton._instances.clear()


def test_same_instance() -> None:
    """Two instantiations return the *same* object (``is``)."""
    a = _Counter()
    b = _Counter()
    assert a is b


def test_init_runs_once() -> None:
    """``__init__`` fires exactly once across multiple instantiations."""
    _Counter.init_count = 0
    _Counter()
    _Counter()
    _Counter()
    assert _Counter.init_count == 1


def test_per_class_isolation() -> None:
    """Two different singleton classes get *distinct* instances."""
    a = _Counter()
    b = _Other()
    assert a is not b
    assert type(a) is _Counter
    assert type(b) is _Other


def test_cache_clear() -> None:
    """After ``_instances.clear()``, the next call builds a new instance."""
    a = _Counter()
    Singleton._instances.clear()
    b = _Counter()
    assert a is not b
