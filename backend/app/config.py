from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://flowwatch:password@db:5432/flowwatch"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    N8N_BASE_URL: str = "http://localhost:5678"
    N8N_API_KEY: str = ""
    SLACK_WEBHOOK_URL: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    GROQ_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()