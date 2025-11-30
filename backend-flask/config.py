"""
Configuration for Flask application.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG  # Log SQL queries in debug mode
    
    # File Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'audio_files')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_AUDIO_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.webm'}
    
    # Audio Processing
    AUDIO_SAMPLE_RATE = 16000
    MFCC_N_COEFFICIENTS = 40
    
    # ML Model
    MODEL_PATH = os.getenv('MODEL_PATH', './models/tajweed_classifier.h5')
    CONFIDENCE_THRESHOLD = 0.75
    
    # SocketIO
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
