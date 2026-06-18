"""Entrypoint: wire config, transcriber, and the Telegram channel together."""

import logging

from audio_transcriber.channels.manager import ChannelManager
from audio_transcriber.config import Settings


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )

    settings = Settings()  # type: ignore
    manager = ChannelManager(settings)
    manager.run()


if __name__ == '__main__':
    main()
