from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "GamePulse"
    VERSION: str = "1.0.0"

    # Database settings
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/gamepulse"

    # Telegram settings (will be loaded from .env automatically)
    TELEGRAM_BOT_TOKEN: str = ""

    # Pydantic will read variables from the .env file
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
