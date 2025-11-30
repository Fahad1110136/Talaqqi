"""
Ghunnah rule detector implementation.
Demonstrates: Single Responsibility, Liskov Substitution.
"""
import numpy as np
from typing import List
import logging

from ml.interfaces.base_detector import ITajweedRuleDetector, TajweedDetectionResult
from models.tajweed_rules import get_rule_config
from config import settings

logger = logging.getLogger(__name__)


class GhunnahDetector(ITajweedRuleDetector):
    """
    Detector for Ghunnah (الغنة - Nasal Sound) rule.
    
    Rule: Ghunnah shown in aggravated Noon by 2 movements.
    Detection: Nasal resonance in audio signal.
    
    Single Responsibility: Only detects Ghunnah rule.
    """
    
    def __init__(self):
        """Initialize Ghunnah detector."""
        self._config = get_rule_config("ghunnah")
        self._min_confidence = settings.CONFIDENCE_THRESHOLD
        logger.debug("GhunnahDetector initialized")
    
    @property
    def rule_name(self) -> str:
        """Get rule name."""
        return "ghunnah"
    
    def detect(
        self,
        audio: np.ndarray,
        features: np.ndarray,
        prediction_scores: dict
    ) -> List[TajweedDetectionResult]:
        """
        Detect Ghunnah rule instances in audio.
        
        Args:
            audio: Original audio waveform
            features: Extracted features
            prediction_scores: ML model predictions
            
        Returns:
            List[TajweedDetectionResult]: List of detected Ghunnah instances
        """
        detections = []
        
        # Get confidence score for Ghunnah
        ghunnah_confidence = prediction_scores.get(self.rule_name, 0.0)
        
        if ghunnah_confidence < self._min_confidence:
            logger.debug(f"Ghunnah confidence too low: {ghunnah_confidence}")
            return detections
        
        # Analyze audio for nasal resonance
        nasal_check = self._detect_nasal_resonance(audio, features)
        
        if nasal_check["detected"]:
            detection = TajweedDetectionResult(
                rule_name=self.rule_name,
                detected=True,
                confidence=ghunnah_confidence,
                timestamp=nasal_check["timestamp"],
                description=f"Ghunnah (الغنة) detected - nasal sound for {self._config.duration_movements} movements",
                correction_suggestion=(
                    None if nasal_check["sufficient_duration"]
                    else f"Ensure nasal sound is maintained for {self._config.duration_movements} movements"
                )
            )
            
            if self.validate(detection):
                detections.append(detection)
                logger.info(f"Ghunnah detected at {detection.timestamp}s")
        
        return detections
    
    def validate(self, detection: TajweedDetectionResult) -> bool:
        """
        Validate Ghunnah detection.
        
        Args:
            detection: Detection to validate
            
        Returns:
            bool: True if valid
        """
        return (
            detection.confidence >= self._min_confidence and
            detection.rule_name == self.rule_name and
            detection.timestamp >= 0
        )
    
    def _detect_nasal_resonance(self, audio: np.ndarray, features: np.ndarray) -> dict:
        """
        Detect nasal resonance in audio signal.
        
        Nasal sounds have distinct spectral characteristics:
        - Lower formant frequencies
        - Specific harmonic patterns
        
        This is simplified; production would use:
        - Formant analysis
        - Spectral tilt measurements
        - Comparison with reference nasal sounds
        
        Args:
            audio: Audio waveform
            features: MFCC features
            
        Returns:
            dict: Nasal detection result
        """
        # Simplified heuristic using MFCC features
        # Real implementation would analyze formants and spectral shape
        
        # Check for nasal-like spectral characteristics in MFCC
        # Lower coefficients often indicate nasal resonance
        mean_low_mfcc = np.mean(features[:3, :])  # First 3 MFCC coefficients
        
        detected = mean_low_mfcc > -10  # Threshold (simplified)
        
        return {
            "detected": detected,
            "timestamp": 0.3,  # Placeholder
            "sufficient_duration": True  # Placeholder
        }
