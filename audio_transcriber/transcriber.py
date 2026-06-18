"""Core transcription, wrapping faster-whisper. Framework-agnostic."""

from __future__ import annotations

import logging
from typing import BinaryIO

from faster_whisper import BatchedInferencePipeline, WhisperModel
from numpy import ndarray

from .config import Settings
from .singleton import Singleton

logger = logging.getLogger(__name__)

AudioInput = str | BinaryIO | ndarray


class Transcriber(metaclass=Singleton):
    """Loads a Whisper model once and turns audio into a transcript string."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        device = settings.resolved_device
        compute_type = settings.resolved_compute_type
        logger.info(
            'Loading Whisper model %r on %s (%s)',
            settings.whisper_model,
            device,
            compute_type,
        )
        model = WhisperModel(
            settings.whisper_model, device=device, compute_type=compute_type
        )
        self._pipeline = BatchedInferencePipeline(model=model)

    def transcribe(self, audio: AudioInput) -> str:
        """Transcribe ``audio`` (a path, seekable file-like object,
        or ndarray).

        Returns the concatenated transcript. Blocking and CPU/GPU-bound — call
        it off the event loop (e.g. via ``asyncio.to_thread``).
        """
        segments, info = self._pipeline.transcribe(
            audio, batch_size=self._settings.batch_size
        )
        logger.debug(
            'Detected language '
            f'{info.language} (p={info.language_probability:.2f})'
        )
        return ' '.join(segment.text.strip() for segment in segments).strip()
