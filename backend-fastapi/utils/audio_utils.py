"""
Utility functions for audio file handling.
Demonstrates: Utility Pattern, Single Responsibility.
"""
import os
from pathlib import Path
from typing import List
import logging

from config import settings
from utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_audio_file(file_path: str) -> bool:
    """
    Validate if file is a supported audio format.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValidationError: If file doesn't exist or invalid format
    """
    path = Path(file_path)
    
    # Check existence
    if not path.exists():
        raise ValidationError(f"Audio file not found: {file_path}")
    
    # Check extension
    ext = path.suffix.lower()
    if ext not in settings.SUPPORTED_AUDIO_FORMATS:
        raise ValidationError(
            f"Unsupported audio format: {ext}. "
            f"Supported: {settings.SUPPORTED_AUDIO_FORMATS}"
        )
    
    # Check file size (max 50 MB for POC)
    max_size = 50 * 1024 * 1024  # 50 MB
    if path.stat().st_size > max_size:
        raise ValidationError(f"Audio file too large (max 50 MB)")
    
    logger.debug(f"Audio file validated: {file_path}")
    return True


def get_audio_duration(file_path: str) -> float:
    """
    Get duration of audio file in seconds.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        float: Duration in seconds
    """
    import librosa
    
    try:
        duration = librosa.get_duration(path=file_path)
        return duration
    except Exception as e:
        logger.error(f"Error getting audio duration: {str(e)}")
        return 0.0


def ensure_audio_directory(directory: str) -> Path:
    """
    Ensure audio storage directory exists.
    
    Args:
        directory: Directory path
        
    Returns:
        Path: Created directory path
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Audio directory ensured: {path}")
    return path


def generate_audio_filename(student_id: int, session_id: int) -> str:
    """
    Generate unique filename for audio recording.
    
    Args:
        student_id: Student ID
        session_id: Session ID
        
    Returns:
        str: Generated filename
    """
    from datetime import datetime
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"recitation_s{student_id}_sess{session_id}_{timestamp}.wav"
    
    return filename
