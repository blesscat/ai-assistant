import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/ai_assistant"
    )

    # Google
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_api_key: str = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY", "")

    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")

    # Encryption
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
