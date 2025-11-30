"""
Al-Madd rule detector implementation.
Demonstrates: Single Responsibility, Open/Closed Principle.
"""
import numpy as np
from typing import List
import logging

from ml.interfaces.base_detector import ITajweedRuleDetector, TajweedDetectionResult
from models.tajweed_rules import get_rule_config
from config import settings

logger = logging.getLogger(__name__)


class MaddDetector(ITajweedRuleDetector):
    """
    Detector for Al-Madd (المد - Stretching/Prolongation) rule.
    
    Rule: Madd letter at end of word + Hamza at start of next word.
    Duration: 4-5 movements.
    
    Single Responsibility: Only detects Al-Madd rule violations.
    """
    
    def __init__(self):
        """Initialize Al-Madd detector with configuration."""
        self._config = get_rule_config("madd")
        self._min_confidence = settings.CONFIDENCE_THRESHOLD
        logger.debug(f"MaddDetector initialized with threshold={self._min_confidence}")
    
    @property
    def rule_name(self) -> str:
        """Get rule name."""
        return "madd"
    
    def detect(
        self,
        audio: np.ndarray,
        features: np.ndarray,
        prediction_scores: dict
    ) -> List[TajweedDetectionResult]:
        """
        Detect Al-Madd rule instances in audio.
        
        Args:
            audio: Original audio waveform
            features: Extracted MFCC/mel-spectrogram features
            prediction_scores: ML model predictions
            
        Returns:
            List[TajweedDetectionResult]: List of detected Al-Madd instances
        """
        detections = []
        
        # Get confidence score for Al-Madd from predictions
        madd_confidence = prediction_scores.get(self.rule_name, 0.0)
        
        if madd_confidence < self._min_confidence:
            logger.debug(f"Al-Madd confidence too low: {madd_confidence}")
            return detections
        
        # Analyze audio for prolongation patterns
        # This is a simplified implementation - actual would use more sophisticated analysis
        duration_check = self._check_duration(audio)
        
        if duration_check["is_valid"]:
            detection = TajweedDetectionResult(
                rule_name=self.rule_name,
                detected=True,
                confidence=madd_confidence,
                timestamp=duration_check["timestamp"],
                description=f"Al-Madd (المد) detected with {duration_check['movements']} movements",
                correction_suggestion=(
                    None if duration_check['movements'] >= 4
                    else f"Extend the prolongation to {self._config.duration_movements} movements"
                )
            )
            
            if self.validate(detection):
                detections.append(detection)
                logger.info(f"Al-Madd detected at {detection.timestamp}s")
        
        return detections
    
    def validate(self, detection: TajweedDetectionResult) -> bool:
        """
        Validate Al-Madd detection.
        
        Args:
            detection: Detection result to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Validation criteria:
        # 1. Confidence above threshold
        # 2. Rule name matches
        # 3. Has timestamp
        
        is_valid = (
            detection.confidence >= self._min_confidence and
            detection.rule_name == self.rule_name and
            detection.timestamp >= 0
        )
        
        return is_valid
    
    def _check_duration(self, audio: np.ndarray) -> dict:
        """
        Check if prolongation duration meets Al-Madd requirements.
        
        This is a simplified heuristic. In production, would use:
        - Mel-frequency energy analysis
        - Temporal pattern matching
        - Comparison with reference Qari recordings
        
        Args:
            audio: Audio waveform
            
        Returns:
            dict: Duration analysis result
        """
        # Simplified implementation
        # In production: analyze energy contours, detect sustained vowels
        
        # Placeholder: estimate from audio length
        sample_rate = settings.AUDIO_SAMPLE_RATE
        estimated_movements = int(len(audio) / sample_rate * 2)  # Rough estimate
        
        return {
            "is_valid": estimated_movements >= 3,  # At least 3 movements detected
            "movements": estimated_movements,
            "timestamp": 0.5  # Placeholder timestamp
        }
