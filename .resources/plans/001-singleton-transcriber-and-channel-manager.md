# Plan: Singleton Transcriber + Singleton ChannelManager

## Context

Today [main.py](main.py) wires things together by hand: it builds `Settings`,
then a `Transcriber`, then a single `TelegramChannel`, and calls `.run()`. Adding
a second channel (Slack, Discord, …) would mean editing `main.py` to construct
each channel and hand it the transcriber individually, and nothing guarantees a
single shared Whisper model — accidentally building two `Transcriber`s would load
the model twice (expensive on GPU/RAM).

We want:
1. A **singleton `Transcriber`** so the heavy Whisper model is loaded exactly once
   no matter how many channels use it.
2. A **singleton `ChannelManager`** that owns the registry of channel classes,
   instantiates each one, and assigns the shared transcriber to it. Adding a
   channel becomes "add a class to the registry," not "edit the wiring."

Decisions confirmed with the user:
- Singleton mechanism: **one shared `Singleton` metaclass** applied to both
  classes (cleanest; tests clear the instance cache between runs).
- Run semantics: **single active channel for now** — the manager instantiates all
  registered channels and runs them in the main thread (only Telegram exists
  today, and `run_polling` needs the main thread for signal handling). True
  concurrent multi-channel running is left as a documented future step.

## Changes

### 1. New `audio_transcriber/singleton.py` — reusable metaclass

A small `Singleton` metaclass caching one instance per class:

```python
class Singleton(type):
    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
```

Subsequent `Cls(...)` calls return the cached instance **without** re-running
`__init__`. The class-level `_instances` dict is what tests clear between cases.

### 2. `audio_transcriber/transcriber.py` — make `Transcriber` a singleton

Change only the class declaration:
```python
from .singleton import Singleton
class Transcriber(metaclass=Singleton):
```
`__init__` (which loads `WhisperModel` + `BatchedInferencePipeline`) is unchanged
and now runs at most once.

### 3. New `audio_transcriber/channels/manager.py` — `ChannelManager`

```python
class ChannelManager(metaclass=Singleton):
    """Owns the channel registry and the shared transcriber."""

    channel_classes: list[type[Channel]] = [TelegramChannel]

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.transcriber = Transcriber(settings)          # the singleton
        self.channels = [
            cls(self.transcriber, self.settings)
            for cls in self.channel_classes
        ]

    def run(self) -> None:
        # Single active channel for now: run each registered channel in the
        # main thread. Only Telegram exists today and run_polling installs
        # signal handlers that require the main thread. Running >1 blocking
        # channel concurrently (threads/asyncio) is a future step.
        for channel in self.channels:
            channel.run()
```

`channel_classes` is the extension seam: adding a channel = import its class and
append it here, no other wiring. `ChannelManager`, `Channel`, and the existing
`Channel.__init__(transcriber, settings)` contract ([channels/base.py:19](audio_transcriber/channels/base.py#L19)) are reused as-is.

### 4. `main.py` — wire through the manager

Replace the manual `Transcriber` + `TelegramChannel` construction
([main.py:16-19](main.py#L16-L19)) with:
```python
settings = Settings()  # type: ignore
manager = ChannelManager(settings)
manager.run()
```
Drop the now-unused direct `Transcriber` / `TelegramChannel` imports.

### 5. Tests

- **[tests/conftest.py](tests/conftest.py)** — add an `autouse` fixture that
  clears `Singleton._instances` before/after each test so cached singletons don't
  leak across tests (the `make_transcriber` fixture builds a fresh `Transcriber`
  per test and relies on its monkeypatched `WhisperModel` running):
  ```python
  @pytest.fixture(autouse=True)
  def _reset_singletons():
      from audio_transcriber.singleton import Singleton
      Singleton._instances.clear()
      yield
      Singleton._instances.clear()
  ```
- **New `tests/audio_transcriber/test_singleton.py`** — `Singleton` returns the
  same instance and does not re-run `__init__`.
- **New `tests/audio_transcriber/channels/test_manager.py`** — using the existing
  `make_transcriber`/`settings` fixtures and monkeypatching
  `manager.channel_classes` to a fake channel class:
  - `ChannelManager(settings) is ChannelManager(settings)` (singleton).
  - the manager instantiates one channel per registered class.
  - each created channel received the shared `Transcriber` singleton
    (`channel.transcriber is Transcriber(settings)`).
  - `run()` calls each channel's `run()`.
- Existing `test_transcriber.py` and `test_telegram.py` stay valid (the reset
  fixture keeps `make_transcriber` building fresh instances).

### 6. Docs

Update [CLAUDE.md](CLAUDE.md) Architecture/data-flow notes to mention
`ChannelManager` as the new entrypoint owner and that both `Transcriber` and
`ChannelManager` are singletons.

## Verification

```bash
uv run pytest -q            # all tests pass, incl. new singleton/manager tests
uv run ruff check .         # lint clean
uv run ruff format --check .
```
Then a manual smoke test (requires `TELEGRAM_BOT_TOKEN` in `.env`):
```bash
uv run python main.py       # bot starts, logs "Loading Whisper model" exactly once
```
Send a voice note → confirm "Transcribing…" edits into the transcript, proving the
manager-created channel got the shared transcriber.

## Notes / future work

- Per the user's decision, only one channel runs at a time. When a second channel
  is added, `ChannelManager.run()` will need threads (or asyncio) and Telegram's
  `run_polling` will need `stop_signals`/main-thread handling reconsidered.
