"""
Factory for creating Tajweed rule detectors.
Demonstrates: Factory Pattern, Open/Closed Principle.
"""
from typing import Dict, Type
import logging

from ml.interfaces.base_detector import ITajweedRuleDetector
from ml.detectors.madd_detector import MaddDetector
from ml.detectors.ghunnah_detector import GhunnahDetector
from ml.detectors.ikhfa_detector import IkhfaDetector

logger = logging.getLogger(__name__)


class TajweedRuleDetectorFactory:
    """
    Factory for creating Tajweed rule detector instances.
    
    Demonstrates: Factory Pattern, Open/Closed Principle.
    New detectors can be registered without modifying existing code.
    """
    
    # Registry mapping rule names to detector classes
    _detectors: Dict[str, Type[ITajweedRuleDetector]] = {
        "madd": MaddDetector,
        "ghunnah": GhunnahDetector,
        "ikhfa": IkhfaDetector
    }
    
    @classmethod
    def create_detector(cls, rule_name: str) -> ITajweedRuleDetector:
        """
        Create a detector instance for the specified Tajweed rule.
        
        Args:
            rule_name: Name of the Tajweed rule (madd, ghunnah, ikhfa)
            
        Returns:
            ITajweedRuleDetector: Detector instance for the rule
            
        Raises:
            ValueError: If rule name is not recognized
        """
        rule_name_lower = rule_name.lower()
        
        if rule_name_lower not in cls._detectors:
            raise ValueError(
                f"Unknown Tajweed rule: {rule_name}. "
                f"Available rules: {list(cls._detectors.keys())}"
            )
        
        detector_class = cls._detectors[rule_name_lower]
        detector = detector_class()
        
        logger.debug(f"Created detector for rule: {rule_name}")
        return detector
    
    @classmethod
    def create_all_detectors(cls) -> Dict[str, ITajweedRuleDetector]:
        """
        Create instances of all registered detectors.
        
        Returns:
            Dict[str, ITajweedRuleDetector]: Mapping of rule names to detector instances
        """
        detectors = {
            rule_name: cls.create_detector(rule_name)
            for rule_name in cls._detectors.keys()
        }
        logger.info(f"Created {len(detectors)} Tajweed rule detectors")
        return detectors
    
    @classmethod
    def register_detector(
        cls,
        rule_name: str,
        detector_class: Type[ITajweedRuleDetector]
    ) -> None:
        """
        Register a new detector class (extensibility).
        Demonstrates Open/Closed Principle - extend without modification.
        
        Args:
            rule_name: Name of the Tajweed rule
            detector_class: Detector class implementing ITajweedRuleDetector
            
        Raises:
            TypeError: If detector_class doesn't implement ITajweedRuleDetector
        """
        if not issubclass(detector_class, ITajweedRuleDetector):
            raise TypeError(
                f"{detector_class.__name__} must implement ITajweedRuleDetector"
            )
        
        cls._detectors[rule_name.lower()] = detector_class
        logger.info(f"Registered new detector: {rule_name} -> {detector_class.__name__}")
    
    @classmethod
    def get_available_rules(cls) -> list:
        """
        Get list of all available Tajweed rule names.
        
        Returns:
            list: List of rule names
        """
        return list(cls._detectors.keys())
