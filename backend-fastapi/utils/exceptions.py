"""
Custom exceptions for better error handling.
Demonstrates: Custom Exception Hierarchy, Error Handling best practices.
"""


class TalaqiException(Exception):
    """Base exception for all Talaqqi application errors."""
    pass


class AudioProcessingError(TalaqiException):
    """Raised when audio processing fails."""
    pass


class ModelLoadError(TalaqiException):
    """Raised when ML model loading fails."""
    pass


class ClassificationError(TalaqiException):
    """Raised when Tajweed classification fails."""
    pass


class DetectionError(TalaqiException):
    """Raised when rule detection fails."""
    pass


class DatabaseError(TalaqiException):
    """Raised when database operations fail."""
    pass


class AuthenticationError(TalaqiException):
    """Raised when authentication fails."""
    pass


class ValidationError(TalaqiException):
    """Raised when input validation fails."""
    pass
