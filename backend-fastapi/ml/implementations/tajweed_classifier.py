"""
TensorFlow/Keras Tajweed classifier implementation.
Demonstrates: Dependency Inversion, Single Responsibility.
"""
import numpy as np
import tensorflow as tf
from typing import Dict, List
import logging

from ml.interfaces.base_classifier import ITajweedClassifier
from ml.implementations.model_loader import ModelLoader
from models.tajweed_rules import get_all_rules
from config import settings

logger = logging.getLogger(__name__)


class TajweedClassifier(ITajweedClassifier):
    """
    Concrete implementation of Tajweed classifier using TensorFlow/Keras.
    
    Single Responsibility: Only performs ML inference.
    Dependency Inversion: Depends on ITajweedClassifier abstraction.
    """
    
    def __init__(self):
        """Initialize classifier with ModelLoader singleton."""
        self._model_loader = ModelLoader()
        self._model: tf.keras.Model = None
        self._rule_names = get_all_rules()
        logger.info(f"TajweedClassifier initialized for rules: {self._rule_names}")
    
    def load_model(self, model_path: str = None) -> None:
        """
        Load trained model using Singleton ModelLoader.
        
        Args:
            model_path: Optional path to model file
        """
        self._model = self._model_loader.get_model(model_path)
        logger.info("Model loaded successfully")
    
    def predict(self, features: np.ndarray) -> Dict[str, float]:
        """
        Predict Tajweed rule probabilities from audio features.
        
        Args:
            features: Extracted audio features (MFCC or mel-spectrogram)
                     Shape: [n_features, time_steps]
            
        Returns:
            Dict[str, float]: Rule name to probability mapping
                Example: {"madd": 0.92, "ghunnah": 0.15, "ikhfa": 0.05}
        
        Raises:
            RuntimeError: If model not loaded
        """
        if self._model is None:
            self.load_model()
        
        # Reshape features for model input: [1, n_features, time_steps]
        features_input = self._prepare_input(features)
        
        # Get predictions
        predictions = self._model.predict(features_input, verbose=0)
        
        # Convert to dictionary
        result = self._format_predictions(predictions[0])
        
        logger.debug(f"Predictions: {result}")
        return result
    
    def predict_batch(self, features_batch: List[np.ndarray]) -> List[Dict[str, float]]:
        """
        Predict Tajweed rules for multiple audio samples.
        
        Args:
            features_batch: List of feature arrays
            
        Returns:
            List[Dict[str, float]]: List of prediction dictionaries
        """
        if self._model is None:
            self.load_model()
        
        # Prepare batch input
        batch_input = np.array([self._prepare_input(f)[0] for f in features_batch])
        
        # Get batch predictions
        predictions = self._model.predict(batch_input, verbose=0)
        
        # Format results
        results = [self._format_predictions(pred) for pred in predictions]
        
        logger.debug(f"Batch predictions completed for {len(results)} samples")
        return results
    
    def _prepare_input(self, features: np.ndarray) -> np.ndarray:
        """
        Prepare features for model input.
        
        Args:
            features: Raw features array
            
        Returns:
            np.ndarray: Formatted input for model
        """
        # Add batch dimension if needed
        if len(features.shape) == 2:
            features = np.expand_dims(features, axis=0)
        
        # Ensure correct shape: [batch, n_features, time_steps]
        return features
    
    def _format_predictions(self, predictions: np.ndarray) -> Dict[str, float]:
        """
        Format model output as dictionary.
        
        Args:
            predictions: Raw model output (probabilities for each class)
            
        Returns:
            Dict[str, float]: Rule name to probability mapping
        """
        return {
            rule_name: float(predictions[i])
            for i, rule_name in enumerate(self._rule_names)
        }
    
    def get_top_prediction(self, predictions: Dict[str, float]) -> tuple:
        """
        Get the most likely Tajweed rule from predictions.
        
        Args:
            predictions: Dictionary of rule probabilities
            
        Returns:
            tuple: (rule_name, confidence_score)
        """
        top_rule = max(predictions.items(), key=lambda x: x[1])
        return top_rule
    
    def filter_by_threshold(
        self,
        predictions: Dict[str, float],
        threshold: float = None
    ) -> Dict[str, float]:
        """
        Filter predictions above confidence threshold.
        
        Args:
            predictions: Dictionary of rule probabilities
            threshold: Minimum confidence (default from settings)
            
        Returns:
            Dict[str, float]: Filtered predictions
        """
        threshold = threshold or settings.CONFIDENCE_THRESHOLD
        return {
            rule: score
            for rule, score in predictions.items()
            if score >= threshold
        }
