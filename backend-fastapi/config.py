"""
Configuration settings for Talaqqi Backend.
Uses Pydantic Settings for environment variable management.
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    Demonstrates: Encapsulation, Single Responsibility Principle.
    """
    
    # Application
    APP_NAME: str = "Talaqqi AI Tajweed Analysis"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database
    DATABASE_URL: str = "sqlite:///./talaqqi.db"
    
    # Audio Processing
    AUDIO_SAMPLE_RATE: int = 16000
    MFCC_N_COEFFICIENTS: int = 40
    MEL_N_MELS: int = 128
    MAX_AUDIO_LENGTH_SECONDS: int = 30
    SUPPORTED_AUDIO_FORMATS: List[str] = [".wav", ".mp3", ".ogg", ".webm"]
    
    # ML Model
    MODEL_PATH: Path = Path("./models/tajweed_classifier.h5")
    MODEL_CACHE_SIZE: int = 1  # Singleton - only one model in memory
    CONFIDENCE_THRESHOLD: float = 0.75
    
    # Tajweed Rules
    TAJWEED_RULES: List[str] = ["madd", "ghunnah", "ikhfa"]
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
settings = Settings()
