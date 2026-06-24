"""Core transcription, delegating to a remote transcription REST API."""

from __future__ import annotations

import logging
import time
from typing import BinaryIO

import httpx
from pydantic import BaseModel

from .config import Settings
from .singleton import Singleton

logger = logging.getLogger(__name__)

_PENDING_STATUSES = {'pending', 'processing'}


class TranscriptionJobResponse(BaseModel):
    """Mirrors the remote API's ``TranscriptionJobResponse`` schema."""

    id: str
    status: str
    original_filename: str | None = None
    content_type: str | None = None
    file_size_bytes: int | None = None
    language: str | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    text: str | None = None


class TranscriptionError(RuntimeError):
    """Raised when the remote transcription API cannot produce a transcript."""


class Transcriber(metaclass=Singleton):
    """Submits audio to a remote transcription REST API and polls for the
    result.
    """

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.transcription_api_base_url
        self._request_timeout = settings.transcription_request_timeout
        self._poll_interval = settings.transcription_poll_interval
        self._poll_timeout = settings.transcription_poll_timeout

    def transcribe(
        self,
        audio: BinaryIO,
        *,
        filename: str,
        content_type: str,
        language: str | None = None,
    ) -> str:
        """Submit ``audio`` to the remote API and poll until it finishes.

        Blocking — call it off the event loop (e.g. via ``asyncio.to_thread``).
        Raises :class:`TranscriptionError` if the job fails, times out, or the
        API returns an unexpected response.
        """
        job = self._submit(
            audio,
            filename=filename,
            content_type=content_type,
            language=language,
        )
        job = self._await_completion(job.id)
        return (job.text or '').strip()

    def _submit(
        self,
        audio: BinaryIO,
        *,
        filename: str,
        content_type: str,
        language: str | None,
    ) -> TranscriptionJobResponse:
        data = {'language': language} if language else None
        with httpx.Client(timeout=self._request_timeout) as client:
            try:
                response = client.post(
                    f'{self._base_url}/api/v1/transcriptions',
                    files={'audio': (filename, audio, content_type)},
                    data=data,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise TranscriptionError(
                    'Transcription API rejected the upload: '
                    f'{exc.response.status_code}'
                ) from exc
            except httpx.HTTPError as exc:
                raise TranscriptionError(
                    'Could not reach the transcription API'
                ) from exc
        return TranscriptionJobResponse.model_validate(response.json())

    def _await_completion(self, job_id: str) -> TranscriptionJobResponse:
        deadline = time.monotonic() + self._poll_timeout
        with httpx.Client(timeout=self._request_timeout) as client:
            while True:
                job = self._fetch(client, job_id)
                if job.status == 'completed':
                    return job
                if job.status == 'failed':
                    raise TranscriptionError(
                        job.error_message or 'Transcription job failed'
                    )
                if job.status not in _PENDING_STATUSES:
                    raise TranscriptionError(
                        f'Unexpected job status: {job.status!r}'
                    )
                if time.monotonic() >= deadline:
                    raise TranscriptionError(
                        f'Transcription job {job_id} timed out after '
                        f'{self._poll_timeout:.0f}s'
                    )
                time.sleep(self._poll_interval)

    def _fetch(
        self, client: httpx.Client, job_id: str
    ) -> TranscriptionJobResponse:
        try:
            response = client.get(
                f'{self._base_url}/api/v1/transcriptions/{job_id}'
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == httpx.codes.NOT_FOUND:
                raise TranscriptionError(
                    f'Transcription job {job_id} not found'
                ) from exc
            raise TranscriptionError(
                'Transcription API error while polling: '
                f'{exc.response.status_code}'
            ) from exc
        except httpx.HTTPError as exc:
            raise TranscriptionError(
                'Could not reach the transcription API'
            ) from exc
        return TranscriptionJobResponse.model_validate(response.json())
