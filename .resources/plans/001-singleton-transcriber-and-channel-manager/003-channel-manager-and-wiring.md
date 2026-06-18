# Slice 003: `ChannelManager` + `main.py` wiring + docs

Part of [001-singleton-transcriber-and-channel-manager](../001-singleton-transcriber-and-channel-manager.md).
Depends on [Slice 001](001-singleton-metaclass.md) and [Slice 002](002-singleton-transcriber.md).

## Context

This final slice introduces the singleton `ChannelManager` **and immediately
wires `main.py` through it**, so the manager lands already in use — no dead-code
interim. The manager owns the registry of channel classes, builds the shared
`Transcriber` singleton once, and assigns it to each channel. Adding a future
channel becomes "append a class to `channel_classes`," not "edit the wiring."

Reuses the existing seams as-is: the `Channel.__init__(transcriber, settings)`
contract ([channels/base.py:19](../../../audio_transcriber/channels/base.py#L19))
and the `Singleton` metaclass from Slice 001.

## Changes

### 1. New `audio_transcriber/channels/manager.py`

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

`channel_classes` is the extension seam.

### 2. `main.py` — wire through the manager

Replace the manual `Transcriber` + `TelegramChannel` construction
([main.py:16-19](../../../main.py#L16-L19)) with:

```python
settings = Settings()  # type: ignore
manager = ChannelManager(settings)
manager.run()
```

Drop the now-unused direct `Transcriber` / `TelegramChannel` imports.

### 3. `CLAUDE.md` — docs

Update the Architecture / data-flow notes: `ChannelManager` is the new
entrypoint owner, and both `Transcriber` and `ChannelManager` are singletons.

## Tests

### New `tests/audio_transcriber/channels/test_manager.py`

Using the existing `make_transcriber` / `settings` fixtures and monkeypatching
`ChannelManager.channel_classes` to a fake `Channel` subclass (whose `run()` is a
recorder/mock):

- **Singleton:** `ChannelManager(settings) is ChannelManager(settings)`.
- **One channel per registered class:** the manager instantiates exactly one
  channel for each entry in `channel_classes`.
- **Shared transcriber:** each created channel received the shared `Transcriber`
  singleton — `channel.transcriber is Transcriber(settings)`.
- **`run()` fan-out:** `manager.run()` calls each channel's `run()` once.

The `_reset_singletons` autouse fixture (added in Slice 002) keeps each case
isolated.

## Verification

```bash
uv run pytest -q                 # full suite incl. new manager tests
uv run ruff check .
uv run ruff format --check .
```

Manual smoke test (requires `TELEGRAM_BOT_TOKEN` in `.env`):

```bash
uv run python main.py            # bot starts; logs "Loading Whisper model" once
```

Send a voice note → confirm "Transcribing…" edits into the transcript, proving
the manager-created channel got the shared transcriber.

Green state: feature complete — the union of slices 001–003 equals parent plan
001's scope.

## Notes / future work

Per the parent plan's decision, only one channel runs at a time. When a second
channel is added, `ChannelManager.run()` will need threads (or asyncio) and
Telegram's `run_polling` will need `stop_signals` / main-thread handling
reconsidered.
