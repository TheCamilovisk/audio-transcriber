from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings for the bot.

    Values come from environment variables (or a local `.env` file). Field names
    map to upper-case env vars.
    e.g. ``telegram_bot_token`` -> ``TELEGRAM_BOT_TOKEN``.
    """

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    telegram_bot_token: str = Field(
        ..., description='Bot token from @BotFather.'
    )

    transcription_api_base_url: str = Field(
        default='http://localhost:8000',
        description='Base URL of the remote transcription REST API.',
    )
    transcription_request_timeout: float = Field(
        default=30.0,
        description='Per-HTTP-call timeout (seconds) for POST/GET requests.',
    )
    transcription_poll_interval: float = Field(
        default=2.0,
        description='Seconds to sleep between job-status polls.',
    )
    transcription_poll_timeout: float = Field(
        default=300.0,
        description=(
            'Max total seconds to wait for a job to reach a terminal status.'
        ),
    )
