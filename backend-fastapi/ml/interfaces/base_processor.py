"""
Base processor interface for audio processing.
Demonstrates: Interface Segregation Principle, Abstraction.
"""
from abc import ABC, abstractmethod
from typing import Any
import numpy as np


class IAudioProcessor(ABC):
    """
    Abstract base class for audio processors.
    Defines the contract for all audio processing implementations.
    
    Follows Interface Segregation Principle - clients only depend on methods they use.
    """
    
    @abstractmethod
    def load_audio(self, file_path: str) -> np.ndarray:
        """
        Load audio file from disk.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            np.ndarray: Audio waveform as numpy array
        """
        pass
    
    @abstractmethod
    def preprocess(self, audio: np.ndarray) -> np.ndarray:
        """
        Preprocess audio (normalization, noise reduction, etc.).
        
        Args:
            audio: Raw audio waveform
            
        Returns:
            np.ndarray: Preprocessed audio
        """
        pass
    
    @abstractmethod
    def extract_features(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract features from audio for ML model input.
        
        Args:
            audio: Preprocessed audio waveform
            
        Returns:
            np.ndarray: Extracted features (MFCC, mel-spectrogram, etc.)
        """
        pass
