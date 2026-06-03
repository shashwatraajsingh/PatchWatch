"""
PatchWatch Configuration
Loads environment variables and provides typed settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # GitHub
    github_webhook_secret: str = ""
    github_token: str = ""

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    # Webhook / External URL
    backend_url: str = ""
    frontend_url: str = "https://patchwatch-frontend.pages.dev"

    # JWT
    jwt_secret: str = "patchwatch-dev-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24 * 7  # 7 days

    # AI Providers
    minimax_api_key: str = ""
    openrouter_api_key: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./patchwatch.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": (".env", "../.env"), "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
