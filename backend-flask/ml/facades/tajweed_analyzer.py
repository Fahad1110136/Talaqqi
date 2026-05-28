"""
Facade for Tajweed analysis pipeline.
Demonstrates: Facade Pattern, Single Responsibility.
"""
from typing import List, Dict
import numpy as np
import logging

from ml.interfaces.base_processor import IAudioProcessor
from ml.interfaces.base_classifier import ITajweedClassifier
from ml.interfaces.base_detector import TajweedDetectionResult
from ml.implementations.audio_processor import AudioProcessor
from ml.implementations.tajweed_classifier import TajweedClassifier
from ml.factories.detector_factory import TajweedRuleDetectorFactory

logger = logging.getLogger(__name__)


class TajweedAnalyzer:
    """
    Facade for the complete Tajweed analysis pipeline.
    Simplifies the complex ML workflow into a single, easy-to-use interface.
    
    Demonstrates: Facade Pattern - hides complexity behind simple API.
    Single Responsibility: Orchestrates the analysis workflow.
    
    Internal pipeline:
    1. Load and preprocess audio (AudioProcessor)
    2. Extract features (AudioProcessor)
    3. Classify Tajweed rules (TajweedClassifier)
    4. Detect specific violations (RuleDetectors)
    5. Generate feedback
    """
    
    def __init__(
        self,
        audio_processor: IAudioProcessor = None,
        classifier: ITajweedClassifier = None
    ):
        """
        Initialize Tajweed analyzer with dependencies.
        Uses Dependency Injection for flexibility.
        
        Args:
            audio_processor: Audio processor implementation (default: AudioProcessor)
            classifier: Tajweed classifier implementation (default: TajweedClassifier)
        """
        # Dependency Injection - allows for testing with mocks
        self._audio_processor = audio_processor or AudioProcessor()
        self._classifier = classifier or TajweedClassifier()
        self._detectors = TajweedRuleDetectorFactory.create_all_detectors()
        
        # Load model on initialization
        self._classifier.load_model()
        
        logger.info("TajweedAnalyzer initialized")
    
    def analyze_audio_file(self, file_path: str) -> Dict:
        """
        Analyze audio file for Tajweed rules (Facade method).
        Single entry point that handles the entire pipeline.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dict: Complete analysis results
                {
                    "overall_score": float,
                    "predictions": Dict[str, float],
                    "detections": List[TajweedDetectionResult],
                    "feedback": List[str]
                }
        """
        logger.info(f"Analyzing audio file: {file_path}")
        
        try:
            # Step 1: Load audio
            audio = self._audio_processor.load_audio(file_path)
            
            # Step 2: Preprocess
            audio_processed = self._audio_processor.preprocess(audio)
            
            # Step 3: Extract features
            features = self._audio_processor.extract_features(audio_processed)
            
            # Step 4: Classify Tajweed rules
            predictions = self._classifier.predict(features)
            
            # Step 5: Run rule detectors
            detections = self._run_detectors(audio_processed, features, predictions)
            
            # Step 6: Calculate overall score
            overall_score = self._calculate_score(predictions, detections)
            
            # Step 7: Generate feedback
            feedback = self._generate_feedback(detections)
            
            logger.info(f"Analysis complete: score={overall_score}, detections={len(detections)}")
            
            return {
                "overall_score": overall_score,
                "predictions": predictions,
                "detections": [self._format_detection(d) for d in detections],
                "feedback": feedback
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audio: {str(e)}")
            raise
    
    def analyze_audio_stream(self, audio_data: np.ndarray) -> Dict:
        """
        Analyze audio from streaming data (for real-time WebSocket analysis).
        
        Args:
            audio_data: Raw audio array
            
        Returns:
            Dict: Analysis results
        """
        logger.debug("Analyzing audio stream")
        
        try:
            # Preprocess
            audio_processed = self._audio_processor.preprocess(audio_data)
            
            # Extract features
            features = self._audio_processor.extract_features(audio_processed)
            
            # Classify
            predictions = self._classifier.predict(features)
            
            # Detect
            detections = self._run_detectors(audio_processed, features, predictions)
            
            # Score and feedback
            overall_score = self._calculate_score(predictions, detections)
            feedback = self._generate_feedback(detections)
            
            return {
                "overall_score": overall_score,
                "predictions": predictions,
                "detections": [self._format_detection(d) for d in detections],
                "feedback": feedback
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audio stream: {str(e)}")
            raise
    
    def _run_detectors(
        self,
        audio: np.ndarray,
        features: np.ndarray,
        predictions: Dict[str, float]
    ) -> List[TajweedDetectionResult]:
        """
        Run all registered Tajweed rule detectors.
        
        Args:
            audio: Preprocessed audio
            features: Extracted features
            predictions: Classifier predictions
            
        Returns:
            List[TajweedDetectionResult]: All detections
        """
        all_detections = []
        
        for rule_name, detector in self._detectors.items():
            detections = detector.detect(audio, features, predictions)
            all_detections.extend(detections)
            logger.debug(f"{rule_name} detector found {len(detections)} instances")
        
        return all_detections
    
    def _calculate_score(
        self,
        predictions: Dict[str, float],
        detections: List[TajweedDetectionResult]
    ) -> float:
        """
        Calculate overall score based on predictions and detections.
        
        Args:
            predictions: ML model predictions
            detections: Detected rule instances
            
        Returns:
            float: Overall score (0-100)
        """
        # Simple scoring: average of top predictions
        # Penalize if correction suggestions exist
        
        avg_confidence = sum(predictions.values()) / len(predictions) if predictions else 0
        
        # Penalty for errors (detections with correction suggestions)
        error_count = sum(1 for d in detections if d.correction_suggestion)
        penalty = error_count * 0.1
        
        score = max(0, min(100, (avg_confidence - penalty) * 100))
        
        return round(score, 2)
    
    def _generate_feedback(self, detections: List[TajweedDetectionResult]) -> List[str]:
        """
        Generate user-friendly feedback messages.
        
        Args:
            detections: Detected Tajweed rule instances
            
        Returns:
            List[str]: Feedback messages
        """
        feedback = []
        
        for detection in detections:
            message = f"✓ {detection.description}"
            if detection.correction_suggestion:
                message += f"\n  💡 Suggestion: {detection.correction_suggestion}"
            feedback.append(message)
        
        if not detections:
            feedback.append("No Tajweed rules detected in this recitation.")
        
        return feedback
    
    def _format_detection(self, detection: TajweedDetectionResult) -> Dict:
        """
        Format detection result as dictionary for JSON serialization.
        
        Args:
            detection: Detection result
            
        Returns:
            Dict: Serializable detection data
        """
        return {
            "rule_name": detection.rule_name,
            "detected": detection.detected,
            "confidence": detection.confidence,
            "timestamp": detection.timestamp,
            "description": detection.description,
            "correction_suggestion": detection.correction_suggestion
        }
