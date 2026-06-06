from pydantic_settings import BaseSettings, SettingsConfigDict

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

    class Config:
        env_file = ".env"

settings = Settings()
