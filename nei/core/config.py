"""Configuration and settings."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="NEI_",
    )

    # Runtime
    environment: str = "dev"  # dev | prod | local

    # Database
    database_url: str = "sqlite+aiosqlite:///data/nei.db"
    
    # Frontend
    vite_dev_url: str = "http://localhost:5173"
    static_build_path: Path = Path("frontend/dist")
    
    # LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    
    # Security
    session_secret: str = "insecure-change-me"
    session_timeout_minutes: int = 120
    
    # Artifacts
    artifacts_path: Path = Path("data/artifacts")
    
    # Rhino 6
    rhino_exe_path: str = r"D:\Rhino 6\System\Rhino.exe"


settings = Settings()