# Slice 002: `Transcriber` becomes a singleton

Part of [001-singleton-transcriber-and-channel-manager](../001-singleton-transcriber-and-channel-manager.md).
Depends on [Slice 001](001-singleton-metaclass.md).

## Context

With the `Singleton` metaclass available, this slice applies it to the heavy
object it exists for: `Transcriber`. The Whisper model now loads at most once no
matter how many times `Transcriber(settings)` is called.

The risk in this slice is the test suite: `make_transcriber`
([tests/conftest.py](../../../tests/conftest.py)) builds a fresh, monkeypatched
`Transcriber` per test, and a leaked singleton would hand later tests a stale
instance. The conftest `_reset_singletons` fixture neutralizes that, keeping
`test_transcriber.py` and `test_telegram.py` valid. This slice ends green.

## Changes

### 1. `audio_transcriber/transcriber.py` — apply the metaclass

Change only the class declaration and add the import. `__init__` (loads
`WhisperModel` + `BatchedInferencePipeline`) is unchanged and now runs at most
once.

```python
from .singleton import Singleton

class Transcriber(metaclass=Singleton):
    ...
```

### 2. `tests/conftest.py` — autouse singleton reset

Add an `autouse` fixture clearing the cache before and after every test so
cached singletons never leak across tests:

```python
@pytest.fixture(autouse=True)
def _reset_singletons():
    from audio_transcriber.singleton import Singleton

    Singleton._instances.clear()
    yield
    Singleton._instances.clear()
```

This is what allows the existing `make_transcriber` fixture (which monkeypatches
`WhisperModel`/`BatchedInferencePipeline` then constructs a `Transcriber`) to
keep returning a fresh, faked instance in each test.

## Tests

- **New assertion (in `tests/audio_transcriber/test_transcriber.py`):**
  `Transcriber(settings) is Transcriber(settings)` returns the same instance,
  exercised through the `make_transcriber` / monkeypatch path so **no real model
  loads**. (Build via the fixture, then assert a second `Transcriber(settings)`
  call returns the same object.)
- **Existing tests unchanged:** `test_transcriber.py` and
  `test_telegram.py` continue to pass because `_reset_singletons` keeps each test
  isolated.

## Verification

```bash
uv run pytest -q                 # full suite incl. the new singleton assertion
uv run ruff check .
uv run ruff format --check .
```

Green state: `Transcriber` is a singleton; existing tests still pass; the model
loads once per process.
