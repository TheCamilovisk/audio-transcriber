"""Use cases for the transcription core (transcriber.py)."""

from __future__ import annotations

from audio_transcriber.transcriber import Transcriber


# UC6 — segment texts joined by single spaces, each stripped, whole stripped
def test_joins_and_strips_segments(make_transcriber):
    transcriber = make_transcriber(texts=('  Hello ', ' world  ', '  there'))
    assert transcriber.transcribe('audio.wav') == 'Hello world there'


# UC7 — no speech yields an empty string
def test_no_speech_returns_empty_string(make_transcriber):
    transcriber = make_transcriber(texts=())
    assert transcriber.transcribe('audio.wav') == ''  # noqa: PLC1901


# UC8 — the configured batch size is forwarded to the pipeline
def test_batch_size_forwarded(make_transcriber, settings):
    transcriber = make_transcriber(texts=('hi',))
    transcriber.transcribe('audio.wav')
    assert transcriber._pipeline.last_batch_size == settings.batch_size


# UC8 — the audio argument is passed through untouched
def test_audio_passed_through(make_transcriber):
    transcriber = make_transcriber(texts=('hi',))
    sentinel = object()
    transcriber.transcribe(sentinel)
    assert transcriber._pipeline.last_audio is sentinel


# UC9 — singleton: Transcriber(settings) returns the same instance
# (exercised through the monkeypatched ``make_transcriber`` path)
def test_singleton_returns_same_instance(make_transcriber, settings):
    first = make_transcriber(texts=('hello',))
    second = Transcriber(settings)
    assert first is second


# UC10 — the model is built on the resolved device / compute type
def test_model_built_with_resolved_device_and_compute_type(make_transcriber):
    transcriber = make_transcriber(texts=('hi',))
    model = transcriber._pipeline.model
    assert model.device == 'cpu'
    assert model.compute_type == 'int8'
