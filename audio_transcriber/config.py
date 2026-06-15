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

    whisper_model: str = 'turbo'
    device: str = 'cpu'  # "cpu" | "cuda" | "auto"
    compute_type: str | None = None  # derived from device when unset
    batch_size: int = 16

    @property
    def resolved_device(self) -> str:
        """Concrete device to load the model on, resolving ``"auto"``."""
        if self.device != 'auto':
            return self.device
        try:
            from ctranslate2 import get_cuda_device_count  # noqa: PLC0415

            return 'cuda' if get_cuda_device_count() > 0 else 'cpu'
        except Exception:
            return 'cpu'

    @property
    def resolved_compute_type(self) -> str:
        """Compute type for the model, derived from the device when unset."""
        if self.compute_type:
            return self.compute_type
        return 'float16' if self.resolved_device == 'cuda' else 'int8'
