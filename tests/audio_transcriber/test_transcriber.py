"""Use cases for the transcription core (transcriber.py)."""

from __future__ import annotations

import io

import httpx
import pytest

from audio_transcriber.transcriber import (
    Transcriber,
    TranscriptionError,
    TranscriptionJobResponse,
)


def _job(
    job_id: str = 'job-1',
    *,
    status: str,
    text: str | None = None,
    error_message: str | None = None,
) -> dict:
    return {
        'id': job_id,
        'status': status,
        'original_filename': 'audio.ogg',
        'content_type': 'audio/ogg',
        'file_size_bytes': 10,
        'language': None,
        'error_message': error_message,
        'created_at': None,
        'updated_at': None,
        'started_at': None,
        'finished_at': None,
        'text': text,
    }


def _audio() -> io.BytesIO:
    return io.BytesIO(b'audio-bytes')


# Success after N polls — pending -> processing -> completed
def test_success_after_n_polls(make_transcriber, transcription_api):
    post_route = transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    get_route = transcription_api.get('/api/v1/transcriptions/job-1').mock(
        side_effect=[
            httpx.Response(200, json=_job(status='processing')),
            httpx.Response(
                200, json=_job(status='completed', text='hello world')
            ),
        ]
    )

    transcript = make_transcriber.transcribe(
        _audio(), filename='voice.ogg', content_type='audio/ogg'
    )

    assert transcript == 'hello world'
    assert post_route.call_count == 1
    assert get_route.call_count == 2  # noqa: PLR2004


# Completed job with no text returns an empty string
def test_completed_with_no_text_returns_empty_string(
    make_transcriber, transcription_api
):
    transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(200, json=_job(status='completed'))
    )

    transcript = make_transcriber.transcribe(
        _audio(), filename='voice.ogg', content_type='audio/ogg'
    )
    assert transcript == ''  # noqa: PLC1901


def test_transcribe_returns_stripped_text(make_transcriber, transcription_api):
    transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(
            200, json=_job(status='completed', text='  hello  ')
        )
    )

    transcript = make_transcriber.transcribe(
        _audio(), filename='voice.ogg', content_type='audio/ogg'
    )
    assert transcript == 'hello'


# Failed status raises, with and without an error_message
def test_failed_status_raises_with_message(make_transcriber, transcription_api):
    transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(
            200, json=_job(status='failed', error_message='boom')
        )
    )

    with pytest.raises(TranscriptionError, match='boom'):
        make_transcriber.transcribe(
            _audio(), filename='voice.ogg', content_type='audio/ogg'
        )


def test_failed_status_without_message_uses_default(
    make_transcriber, transcription_api
):
    transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(200, json=_job(status='failed'))
    )

    with pytest.raises(TranscriptionError):
        make_transcriber.transcribe(
            _audio(), filename='voice.ogg', content_type='audio/ogg'
        )


def test_unexpected_status_raises(make_transcriber, transcription_api):
    transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(200, json=_job(status='queued'))
    )

    with pytest.raises(TranscriptionError, match='queued'):
        make_transcriber.transcribe(
            _audio(), filename='voice.ogg', content_type='audio/ogg'
        )


# Poll timeout — every poll keeps returning "processing"
def test_poll_timeout_raises(transcription_api, settings):
    settings = settings.model_copy(update={'transcription_poll_timeout': 0})
    transcriber = Transcriber(settings)
    transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    get_route = transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(200, json=_job(status='processing'))
    )

    with pytest.raises(TranscriptionError, match='timed out'):
        transcriber.transcribe(
            _audio(), filename='voice.ogg', content_type='audio/ogg'
        )
    assert get_route.call_count == 1


# POST HTTP errors raise, with no GET attempted
def test_post_http_error_raises(make_transcriber, transcription_api):
    transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(422, json={'detail': 'bad audio'})
    )
    get_route = transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(200, json=_job(status='completed'))
    )

    with pytest.raises(TranscriptionError):
        make_transcriber.transcribe(
            _audio(), filename='voice.ogg', content_type='audio/ogg'
        )
    assert get_route.call_count == 0


# GET 404 raises, mentioning the job id
def test_get_404_raises(make_transcriber, transcription_api):
    transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(404, json={'detail': 'not found'})
    )

    with pytest.raises(TranscriptionError, match='job-1'):
        make_transcriber.transcribe(
            _audio(), filename='voice.ogg', content_type='audio/ogg'
        )


def test_get_other_http_error_raises(make_transcriber, transcription_api):
    transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(500)
    )

    with pytest.raises(TranscriptionError):
        make_transcriber.transcribe(
            _audio(), filename='voice.ogg', content_type='audio/ogg'
        )


def test_network_error_on_post_raises(make_transcriber, transcription_api):
    transcription_api.post('/api/v1/transcriptions').mock(
        side_effect=httpx.ConnectError('connection refused')
    )

    with pytest.raises(TranscriptionError):
        make_transcriber.transcribe(
            _audio(), filename='voice.ogg', content_type='audio/ogg'
        )


# language is forwarded when set, omitted entirely when None
def test_language_param_forwarded_when_set(make_transcriber, transcription_api):
    post_route = transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(200, json=_job(status='completed'))
    )

    make_transcriber.transcribe(
        _audio(),
        filename='voice.ogg',
        content_type='audio/ogg',
        language='en',
    )

    request = post_route.calls.last.request
    assert b'name="language"' in request.content
    assert b'en' in request.content


def test_language_param_omitted_when_none(make_transcriber, transcription_api):
    post_route = transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(200, json=_job(status='completed'))
    )

    make_transcriber.transcribe(
        _audio(), filename='voice.ogg', content_type='audio/ogg'
    )

    request = post_route.calls.last.request
    assert b'name="language"' not in request.content


def test_multipart_filename_and_content_type_forwarded(
    make_transcriber, transcription_api
):
    post_route = transcription_api.post('/api/v1/transcriptions').mock(
        return_value=httpx.Response(201, json=_job(status='pending'))
    )
    transcription_api.get('/api/v1/transcriptions/job-1').mock(
        return_value=httpx.Response(200, json=_job(status='completed'))
    )

    make_transcriber.transcribe(
        _audio(), filename='audio.mp3', content_type='audio/mpeg'
    )

    request = post_route.calls.last.request
    assert b'filename="audio.mp3"' in request.content
    assert b'audio/mpeg' in request.content


# Singleton: Transcriber(settings) returns the same instance
def test_singleton_returns_same_instance(make_transcriber, settings):
    assert make_transcriber is Transcriber(settings)


def test_response_model_parses_known_fields():
    job = TranscriptionJobResponse.model_validate(
        _job(status='completed', text='hi')
    )
    assert job.id == 'job-1'
    assert job.status == 'completed'
    assert job.text == 'hi'
