"""
Configuration settings for the MCP-UI-Terminology Checker.
"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Security
    API_TOKEN: str = "TEST_TOKEN"
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/terms.db"
    
    # Terminology checking
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: List[str] = ["en", "jp"]
    
    # LLM Integration
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: str = "openai"  # "openai" or "anthropic"
    LLM_MODEL: str = "gpt-3.5-turbo"  # or "claude-3-haiku-20240307"
    LLM_TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 500
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 