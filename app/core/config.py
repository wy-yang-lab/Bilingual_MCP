"""
Configuration settings for the MCP-UI-Terminology Checker.
"""
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Security
    API_TOKEN: str = os.getenv("API_TOKEN", "TEST_TOKEN")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8501",
        "https://*.streamlit.app",
        "https://*.streamlitapp.com", 
        "http://127.0.0.1:8501",
        "*"  # Allow all for now - will tighten after deployment
    ]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/terms.db")
    
    # Terminology checking
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: List[str] = ["en", "jp"]
    
    # LLM Integration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DEFAULT_LLM_PROVIDER: str = "openai"  # "openai" or "anthropic"
    LLM_MODEL: str = "gpt-4o"  # Use GPT-4o as chosen
    LLM_TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 