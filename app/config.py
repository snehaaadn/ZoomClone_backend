from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Zoom Clone API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = "sqlite:///./zoom_clone.db"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "*"
    ]
    DEFAULT_USER_NAME: str = "Sneha Debnath (Host)"
    DEFAULT_USER_EMAIL: str = "sneha.debnath@zoomclone.local"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)



settings = Settings()
