"""Channel registry and shared-transcriber ownership.

:class:`ChannelManager` is the singleton that owns the shared
:class:`Transcriber` instance and the list of registered channel classes.
Adding a future channel means appending its class to
:attr:`ChannelManager.channel_classes`, not editing wiring code.
"""

from __future__ import annotations

from ..config import Settings
from ..singleton import Singleton
from ..transcriber import Transcriber
from .base import Channel
from .telegram import TelegramChannel


class ChannelManager(metaclass=Singleton):
    """Owns the channel registry and the shared transcriber.

    Instantiated once with :class:`Settings` — subsequent calls return the
    same cached instance and do **not** re-run ``__init__``.

    Use :func:`run` to start all registered channels.
    """

    channel_classes: list[type[Channel]] = [TelegramChannel]

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.transcriber = Transcriber(settings)
        self.channels = [
            cls(self.transcriber, self.settings) for cls in self.channel_classes
        ]

    def run(self) -> None:
        """Start each registered channel in order.

        Only one channel exists today (:class:`TelegramChannel`).
        ``run_polling`` installs signal handlers that require the main thread,
        so channels are run sequentially. When a second channel is added this
        method will need to use threads or asyncio.
        """
        for channel in self.channels:
            channel.run()
