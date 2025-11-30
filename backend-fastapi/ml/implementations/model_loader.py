"""
Singleton model loader for Tajweed classifier.
Demonstrates: Singleton Pattern, Lazy Initialization.
"""
import tensorflow as tf
from typing import Optional
import logging
import threading

from ml.interfaces.base_classifier import ITajweedClassifier
from config import settings

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Singleton class for loading and caching ML models.
    Ensures only one model instance is loaded in memory (resource optimization).
    
    Thread-safe implementation using double-checked locking.
    Demonstrates: Singleton Pattern, Lazy Initialization.
    """
    
    _instance: Optional['ModelLoader'] = None
    _lock: threading.Lock = threading.Lock()
    _model: Optional[tf.keras.Model] = None
    
    def __new__(cls):
        """
        Create singleton instance with double-checked locking.
        Thread-safe lazy initialization.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    logger.info("ModelLoader singleton instance created")
        return cls._instance
    
    def get_model(self, model_path: Optional[str] = None) -> tf.keras.Model:
        """
        Get the loaded model instance (lazy loading).
        
        Args:
            model_path: Path to model file (optional, uses config default)
            
        Returns:
            tf.keras.Model: Loaded Keras model
            
        Raises:
            FileNotFoundError: If model file doesn't exist
        """
        if self._model is None:
            with self._lock:
                if self._model is None:
                    path = model_path or str(settings.MODEL_PATH)
                    self._model = self._load_model(path)
                    logger.info(f"Model loaded from {path}")
        return self._model
    
    def _load_model(self, model_path: str) -> tf.keras.Model:
        """
        Load TensorFlow/Keras model from disk.
        
        Args:
            model_path: Path to saved model
            
        Returns:
            tf.keras.Model: Loaded model
            
        Raises:
            FileNotFoundError: If model file doesn't exist
        """
        try:
            model = tf.keras.models.load_model(model_path)
            logger.info(f"Successfully loaded model from {model_path}")
            return model
        except FileNotFoundError:
            logger.error(f"Model file not found: {model_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def reload_model(self, model_path: Optional[str] = None) -> None:
        """
        Force reload of the model (useful for model updates).
        
        Args:
            model_path: Path to new model file
        """
        with self._lock:
            path = model_path or str(settings.MODEL_PATH)
            self._model = self._load_model(path)
            logger.info(f"Model reloaded from {path}")
    
    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (primarily for testing)."""
        with cls._lock:
            cls._instance = None
            cls._model = None
            logger.info("ModelLoader singleton reset")
