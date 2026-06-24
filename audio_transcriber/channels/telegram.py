"""Telegram channel: receives audio messages and replies with transcripts."""

from __future__ import annotations

import asyncio
import io
import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .base import Channel

logger = logging.getLogger(__name__)

_DEFAULT_VOICE_FILENAME = 'voice.ogg'
_DEFAULT_CONTENT_TYPE = 'audio/ogg'


class TelegramChannel(Channel):
    """A long-polling Telegram bot backed by the shared :class:`Transcriber`."""  # noqa: E501

    def _build_application(self) -> Application:
        app = (
            ApplicationBuilder().token(self.settings.telegram_bot_token).build()
        )
        app.add_handler(CommandHandler('start', self._on_start))
        app.add_handler(
            MessageHandler(filters.VOICE | filters.AUDIO, self._on_audio)
        )
        return app

    async def _on_start(  # noqa: PLR6301
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.message:
            await update.message.reply_text(
                "Send me a voice message or audio file and I'll transcribe it."
            )

    async def _on_audio(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message = update.message
        if message is None:
            return

        media = message.voice or message.audio
        if media is None:
            return

        filename, content_type = self._media_metadata(media)

        ack = await message.reply_text('Transcribing…')
        try:
            tg_file = await media.get_file()
            data = await tg_file.download_as_bytearray()
            buf = io.BytesIO(bytes(data))
            transcript = await asyncio.to_thread(
                self.transcriber.transcribe,
                buf,
                filename=filename,
                content_type=content_type,
            )
        except Exception:
            logger.exception('Failed to transcribe audio')
            await ack.edit_text("Sorry, I couldn't transcribe that audio.")
            return

        await ack.edit_text(transcript or '(no speech detected)')

    @staticmethod
    def _media_metadata(media) -> tuple[str, str]:  # noqa: ANN001
        """Derive ``(filename, content_type)`` for ``voice`` or ``audio``.

        ``Voice`` has no filename and is always Ogg/Opus; ``Audio`` carries
        its own ``file_name``/``mime_type``, falling back to the same
        defaults when Telegram omits them.
        """
        filename = getattr(media, 'file_name', None) or _DEFAULT_VOICE_FILENAME
        content_type = (
            getattr(media, 'mime_type', None) or _DEFAULT_CONTENT_TYPE
        )
        return filename, content_type

    def run(self) -> None:
        app = self._build_application()
        logger.info('Telegram bot started (long polling)')
        app.run_polling()
