"""
Base detector interface for Tajweed rule detection.
Demonstrates: Open/Closed Principle, Interface Segregation.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class TajweedDetectionResult:
    """
    Result of Tajweed rule detection.
    Encapsulates detection metadata.
    """
    rule_name: str
    detected: bool
    confidence: float  # 0-1
    timestamp: float  # seconds in audio
    description: str
    correction_suggestion: Optional[str] = None


class ITajweedRuleDetector(ABC):
    """
    Abstract base class for Tajweed rule detectors.
    Each detector is responsible for ONE specific Tajweed rule.
    
    Follows Single Responsibility Principle - one rule per detector.
    Follows Open/Closed Principle - new rules can be added without modifying existing code.
    """
    
    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Get the name of the Tajweed rule this detector handles."""
        pass
    
    @abstractmethod
    def detect(
        self,
        audio: 'np.ndarray',
        features: 'np.ndarray',
        prediction_scores: dict
    ) -> List[TajweedDetectionResult]:
        """
        Detect instances of this Tajweed rule in the audio.
        
        Args:
            audio: Original audio waveform
            features: Extracted features
            prediction_scores: ML model prediction scores
            
        Returns:
            List[TajweedDetectionResult]: List of detected rule violations/applications
        """
        pass
    
    @abstractmethod
    def validate(self, detection: TajweedDetectionResult) -> bool:
        """
        Validate if a detection meets the rule's criteria.
        
        Args:
            detection: Detection result to validate
            
        Returns:
            bool: True if detection is valid, False otherwise
        """
        pass
