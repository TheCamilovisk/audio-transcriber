# Slice 001: `Singleton` metaclass (foundation)

Part of [001-singleton-transcriber-and-channel-manager](../001-singleton-transcriber-and-channel-manager.md).

## Context

The parent plan needs a reusable singleton mechanism shared by both
`Transcriber` and `ChannelManager`. This first slice lands that mechanism in
isolation: a `Singleton` metaclass plus its unit tests. Nothing in the codebase
imports it yet, so this slice is risk-free and leaves the existing suite
untouched and green. Slices 002 and 003 build on it.

## Changes

### 1. New `audio_transcriber/singleton.py`

A metaclass caching one instance per class. Subsequent `Cls(...)` calls return
the cached instance **without** re-running `__init__`. The class-level
`_instances` dict is the cache tests clear between cases.

```python
"""A minimal singleton metaclass shared across the package."""

from __future__ import annotations


class Singleton(type):
    """Metaclass that caches one instance per class.

    Calling ``Cls(...)`` again returns the cached instance and does **not**
    re-run ``__init__``. Tests clear :attr:`_instances` to get fresh instances.
    """

    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):  # noqa: ANN002, ANN003, ANN204
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
```

## Tests

### New `tests/audio_transcriber/test_singleton.py`

Using a small local class defined `metaclass=Singleton`:

- **Same instance:** two instantiations return the *same* object (`is`).
- **`__init__` runs once:** a constructor side-effect (e.g. a class-level
  counter incremented in `__init__`) fires exactly once across multiple
  instantiations.
- **Per-class isolation:** two *different* classes using the metaclass get
  *distinct* instances (no cross-class collision).
- **Cache clear:** after `Singleton._instances.clear()`, the next call builds a
  fresh instance (not identical to the previous one).

These tests are self-contained — no fixtures or monkeypatching required.

## Verification

```bash
uv run pytest tests/audio_transcriber/test_singleton.py -q   # new tests pass
uv run pytest -q                                             # whole suite green
uv run ruff check .
uv run ruff format --check .
```

Green state: new file added, fully tested; no existing behavior changed.
