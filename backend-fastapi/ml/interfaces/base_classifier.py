"""
Base classifier interface for Tajweed classification.
Demonstrates: Interface Segregation Principle, Dependency Inversion.
"""
from abc import ABC, abstractmethod
from typing import Dict, List
import numpy as np


class ITajweedClassifier(ABC):
    """
    Abstract base class for Tajweed classifiers.
    Defines the contract for all ML classification implementations.
    
    Allows for different model architectures to be swapped (Liskov Substitution).
    """
    
    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """
        Load trained model from disk.
        
        Args:
            model_path: Path to saved model file
        """
        pass
    
    @abstractmethod
    def predict(self, features: np.ndarray) -> Dict[str, float]:
        """
        Predict Tajweed rule probabilities from audio features.
        
        Args:
            features: Extracted audio features
            
        Returns:
            Dict[str, float]: Dictionary mapping rule names to probability scores
                Example: {"madd": 0.92, "ghunnah": 0.15, "ikhfa": 0.05}
        """
        pass
    
    @abstractmethod
    def predict_batch(self, features_batch: List[np.ndarray]) -> List[Dict[str, float]]:
        """
        Predict Tajweed rules for multiple audio samples (batch processing).
        
        Args:
            features_batch: List of feature arrays
            
        Returns:
            List[Dict[str, float]]: List of prediction dictionaries
        """
        pass
