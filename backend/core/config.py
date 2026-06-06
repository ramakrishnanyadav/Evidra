from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Any

class Settings(BaseSettings):
    PROJECT_NAME: str = "Evidra API"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/evidra"
    JWT_SECRET: str = "change-this"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8
    FEATHERLESS_API_KEY: str = ""
    GITHUB_TOKEN: str = ""
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSIONS: int = 384

    @model_validator(mode="after")
    def fix_database_url(self) -> 'Settings':
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self

    class Config:
        env_file = ".env"

settings = Settings()
