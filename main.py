"""Entrypoint: wire config, transcriber, and the Telegram channel together."""

import logging

from audio_transcriber.channels.telegram import TelegramChannel
from audio_transcriber.config import Settings
from audio_transcriber.transcriber import Transcriber


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )

    settings = Settings()  # type: ignore
    transcriber = Transcriber(settings)
    channel = TelegramChannel(transcriber, settings)
    channel.run()


if __name__ == '__main__':
    main()
