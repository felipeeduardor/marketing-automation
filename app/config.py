from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Marketing Automation"
    DEBUG: bool = False

    # Security
    ADMIN_API_TOKEN: str = ""  # bearer token for the internal API, shared with the dashboard
    CORS_ORIGINS: str = ""  # comma-separated origins allowed to call the API from a browser
    META_VERIFY_TOKEN: str = ""  # token configured in the Meta webhook settings

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/marketing_db"

    # CRM - RD Station
    RD_STATION_API_KEY: str = ""
    RD_STATION_CLIENT_ID: str = ""
    RD_STATION_CLIENT_SECRET: str = ""

    # Payments
    STRIPE_SECRET_KEY: str = ""
    MERCADOPAGO_ACCESS_TOKEN: str = ""

    # VSL sales funnel
    VSL_VIDEO_URL: str = ""  # .mp4/.webm file or YouTube link
    VSL_CTA_DELAY_SECONDS: int = 0  # seconds of video watched before the offer button appears
    VSL_SIGNUP_URL: str = "https://vitaclini.com.br/login?aba=cadastro"  # where "Criar conta grátis" leads
    VSL_WHATSAPP_NUMBER: str = ""  # e.g. 5511999999999; shows a "Falar com especialista" button
    VSL_HEADLINE: str = "Sua recepção responde as mesmas perguntas no WhatsApp o dia inteiro?"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
