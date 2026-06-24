"""Use cases for the channel manager (channels/manager.py)."""

from __future__ import annotations

from audio_transcriber.channels.base import Channel
from audio_transcriber.channels.manager import ChannelManager
from audio_transcriber.transcriber import Transcriber


class _RecordingChannel(Channel):
    """Fake channel that records how many times its ``run()`` was called."""

    def __init__(self, transcriber: Transcriber, settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(transcriber, settings)
        self.run_count = 0

    def run(self) -> None:
        self.run_count += 1


# UC — singleton: ChannelManager(settings) is ChannelManager(settings)
def test_singleton_returns_same_instance(settings):
    first = ChannelManager(settings)
    second = ChannelManager(settings)
    assert first is second


# UC — one channel per registered class
def test_one_channel_per_class(settings, monkeypatch):
    monkeypatch.setattr(ChannelManager, 'channel_classes', [_RecordingChannel])
    manager = ChannelManager(settings)
    assert len(manager.channels) == 1
    assert isinstance(manager.channels[0], _RecordingChannel)


# UC — each channel received the shared Transcriber singleton
def test_channels_receive_shared_transcriber(settings, monkeypatch):
    monkeypatch.setattr(ChannelManager, 'channel_classes', [_RecordingChannel])
    manager = ChannelManager(settings)
    for channel in manager.channels:
        assert channel.transcriber is Transcriber(settings)


# UC — run() fans out to each channel
def test_run_fans_out_to_channels(settings, monkeypatch):
    monkeypatch.setattr(ChannelManager, 'channel_classes', [_RecordingChannel])
    manager = ChannelManager(settings)
    manager.run()
    for channel in manager.channels:
        assert channel.run_count == 1
