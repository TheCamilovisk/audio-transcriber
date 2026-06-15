"""The channel adapter seam.

A channel is the surface that both *captures* incoming audio and *relays* the
resulting transcript back. Each concrete channel (Telegram today, others later)
subclasses :class:`Channel` and implements :meth:`run`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import Settings
from ..transcriber import Transcriber


class Channel(ABC):
    """Base class for a transcription channel."""

    def __init__(self, transcriber: Transcriber, settings: Settings) -> None:
        self.transcriber = transcriber
        self.settings = settings

    @abstractmethod
    def run(self) -> None:
        """Start listening for audio and relaying transcripts. Blocks."""
