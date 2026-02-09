from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Marketing Automation"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/marketing_db"

    # OpenAI / LLM
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    # BotConversa
    BOTCONVERSA_API_KEY: str = ""
    BOTCONVERSA_WEBHOOK_SECRET: str = ""

    # CRM - RD Station
    RD_STATION_API_KEY: str = ""
    RD_STATION_CLIENT_ID: str = ""
    RD_STATION_CLIENT_SECRET: str = ""

    # Payments
    STRIPE_SECRET_KEY: str = ""
    MERCADOPAGO_ACCESS_TOKEN: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
