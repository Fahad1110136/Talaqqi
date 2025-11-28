"""
Tajweed rules configuration and metadata.
Demonstrates: Encapsulation, Configuration as data.
"""
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class TajweedRuleConfig:
    """
    Configuration for a Tajweed rule.
    Encapsulates rule metadata for easy extension.
    """
    name: str
    arabic_name: str
    description: str
    color_code: str  # HTML color for UI visualization
    duration_movements: int  # Required duration in movements (if applicable)
    examples: List[str]  # Example words/phrases


# Tajweed Rule Configurations (Open/Closed Principle - easy to extend)
TAJWEED_RULES_CONFIG: Dict[str, TajweedRuleConfig] = {
    "madd": TajweedRuleConfig(
        name="Al-Madd",
        arabic_name="المد",
        description="Stretching/Prolongation - Madd letter at end of word with Hamza at start of next word",
        color_code="#4CAF50",  # Green
        duration_movements=5,  # 4-5 movements
        examples=["يَجۡمَعُ ٱللَّهُ", "مَآ أُجِبۡتُمۡ"]
    ),
    "ghunnah": TajweedRuleConfig(
        name="Ghunnah",
        arabic_name="الغنة",
        description="Nasal Sound - Ghunnah must be shown in aggravated Noon by 2 movements",
        color_code="#2196F3",  # Blue
        duration_movements=2,
        examples=["لَنَآ", "إِنَّكَ"]
    ),
    "ikhfa": TajweedRuleConfig(
        name="Ikhfāʾ",
        arabic_name="الإخفاء",
        description="Hiding/Concealment - Pronouncing consonant Noon or Tanween between showing and fading",
        color_code="#FF9800",  # Orange
        duration_movements=2,
        examples=["لَا عِلۡمَ"]
    )
}


def get_rule_config(rule_name: str) -> TajweedRuleConfig:
    """
    Get configuration for a specific Tajweed rule.
    
    Args:
        rule_name: Name of the Tajweed rule (madd, ghunnah, ikhfa)
        
    Returns:
        TajweedRuleConfig: Configuration object for the rule
        
    Raises:
        ValueError: If rule name is not recognized
    """
    if rule_name.lower() not in TAJWEED_RULES_CONFIG:
        raise ValueError(f"Unknown Tajweed rule: {rule_name}")
    return TAJWEED_RULES_CONFIG[rule_name.lower()]


def get_all_rules() -> List[str]:
    """
    Get list of all supported Tajweed rule names.
    
    Returns:
        List[str]: List of rule names
    """
    return list(TAJWEED_RULES_CONFIG.keys())
