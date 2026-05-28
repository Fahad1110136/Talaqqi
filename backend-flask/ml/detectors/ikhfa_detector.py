"""
Ikhfāʾ rule detector implementation.
Demonstrates: Single Responsibility, Polymorphism.
"""
import numpy as np
from typing import List
import logging

from ml.interfaces.base_detector import ITajweedRuleDetector, TajweedDetectionResult
from models.tajweed_rules import get_rule_config
from config import settings

logger = logging.getLogger(__name__)


class IkhfaDetector(ITajweedRuleDetector):
    """
    Detector for Ikhfāʾ (الإخفاء - Hiding/Concealment) rule.
    
    Rule: Pronouncing consonant Noon or Tanween between showing and fading.
    Detection: Partial concealment of consonant sound.
    
    Single Responsibility: Only detects Ikhfāʾ rule.
    """
    
    def __init__(self):
        """Initialize Ikhfāʾ detector."""
        self._config = get_rule_config("ikhfa")
        self._min_confidence = settings.CONFIDENCE_THRESHOLD
        logger.debug("IkhfaDetector initialized")
    
    @property
    def rule_name(self) -> str:
        """Get rule name."""
        return "ikhfa"
    
    def detect(
        self,
        audio: np.ndarray,
        features: np.ndarray,
        prediction_scores: dict
    ) -> List[TajweedDetectionResult]:
        """
        Detect Ikhfāʾ rule instances in audio.
        
        Args:
            audio: Original audio waveform
            features: Extracted features
            prediction_scores: ML model predictions
            
        Returns:
            List[TajweedDetectionResult]: List of detected Ikhfāʾ instances
        """
        detections = []
        
        # Get confidence score for Ikhfāʾ
        ikhfa_confidence = prediction_scores.get(self.rule_name, 0.0)
        
        if ikhfa_confidence < self._min_confidence:
            logger.debug(f"Ikhfāʾ confidence too low: {ikhfa_confidence}")
            return detections
        
        # Analyze for concealment pattern
        concealment_check = self._detect_concealment(audio, features)
        
        if concealment_check["detected"]:
            detection = TajweedDetectionResult(
                rule_name=self.rule_name,
                detected=True,
                confidence=ikhfa_confidence,
                timestamp=concealment_check["timestamp"],
                description=f"Ikhfāʾ (الإخفاء) detected - consonant concealment",
                correction_suggestion=(
                    None if concealment_check["proper_execution"]
                    else "Ensure proper balance between showing and fading the consonant"
                )
            )
            
            if self.validate(detection):
                detections.append(detection)
                logger.info(f"Ikhfāʾ detected at {detection.timestamp}s")
        
        return detections
    
    def validate(self, detection: TajweedDetectionResult) -> bool:
        """
        Validate Ikhfāʾ detection.
        
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
    
    def _detect_concealment(self, audio: np.ndarray, features: np.ndarray) -> dict:
        """
        Detect consonant concealment pattern in audio.
        
        Ikhfāʾ is characterized by:
        - Gradual reduction in consonant energy
        - Smooth transition (not abrupt)
        - Maintained nasal resonance
        
        This is simplified; production would use:
        - Energy envelope analysis
        - Spectral transition smoothness
        - Formant trajectory analysis
        
        Args:
            audio: Audio waveform
            features: MFCC features
            
        Returns:
            dict: Concealment detection result
        """
        # Simplified heuristic
        # Check for energy transitions in features
        
        # Calculate energy variation across time
        energy_std = np.std(np.sum(features, axis=0))
        
        # Concealment should have moderate variation (not too abrupt, not flat)
        detected = 5 < energy_std < 20  # Thresholds (simplified)
        
        return {
            "detected": detected,
            "timestamp": 0.4,  # Placeholder
            "proper_execution": True  # Placeholder
        }
