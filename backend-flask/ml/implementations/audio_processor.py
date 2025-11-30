"""
Audio processor implementation using librosa.
Demonstrates: Strategy Pattern, Single Responsibility Principle.
"""
import numpy as np
import librosa
from typing import Optional
import logging

from ml.interfaces.base_processor import IAudioProcessor
from config import settings

logger = logging.getLogger(__name__)


class AudioProcessor(IAudioProcessor):
    """
    Concrete audio processor using librosa library.
    Implements Chain of Responsibility pattern for audio preprocessing pipeline.
    
    Single Responsibility: Only handles audio loading and preprocessing.
    """
    
    def __init__(
        self,
        sample_rate: int = settings.AUDIO_SAMPLE_RATE,
        n_mfcc: int = settings.MFCC_N_COEFFICIENTS,
        n_mels: int = settings.MEL_N_MELS
    ):
        """
        Initialize audio processor with configuration.
        
        Args:
            sample_rate: Target sample rate for audio
            n_mfcc: Number of MFCC coefficients to extract
            n_mels: Number of mel bands for mel-spectrogram
        """
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc
        self.n_mels = n_mels
        logger.info(f"AudioProcessor initialized with sample_rate={sample_rate}, n_mfcc={n_mfcc}")
    
    def load_audio(self, file_path: str) -> np.ndarray:
        """
        Load audio file and resample to target sample rate.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            np.ndarray: Audio waveform
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio file is corrupted or invalid format
        """
        try:
            audio, sr = librosa.load(file_path, sr=self.sample_rate)
            logger.debug(f"Loaded audio from {file_path}: shape={audio.shape}, sr={sr}")
            return audio
        except FileNotFoundError:
            logger.error(f"Audio file not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading audio from {file_path}: {str(e)}")
            raise ValueError(f"Invalid audio file: {str(e)}")
    
    def preprocess(self, audio: np.ndarray) -> np.ndarray:
        """
        Preprocess audio using Chain of Responsibility pattern.
        Pipeline: normalize → trim silence → pad/truncate
        
        Args:
            audio: Raw audio waveform
            
        Returns:
            np.ndarray: Preprocessed audio
        """
        # Step 1: Normalize audio
        audio = self._normalize(audio)
        
        # Step 2: Trim silence from start and end
        audio = self._trim_silence(audio)
        
        # Step 3: Pad or truncate to fixed length
        audio = self._fix_length(audio)
        
        logger.debug(f"Preprocessed audio: shape={audio.shape}")
        return audio
    
    def extract_features(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract MFCC features from audio.
        Uses Strategy Pattern - can be swapped with MelSpectrogramExtractor.
        
        Args:
            audio: Preprocessed audio waveform
            
        Returns:
            np.ndarray: MFCC features (shape: [n_mfcc, time_steps])
        """
        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=self.sample_rate,
            n_mfcc=self.n_mfcc
        )
        logger.debug(f"Extracted MFCC features: shape={mfcc.shape}")
        return mfcc
    
    # Private helper methods (Chain of Responsibility pattern)
    
    def _normalize(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range."""
        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio / max_val
        return audio
    
    def _trim_silence(self, audio: np.ndarray, top_db: int = 20) -> np.ndarray:
        """Trim silence from start and end of audio."""
        audio, _ = librosa.effects.trim(audio, top_db=top_db)
        return audio
    
    def _fix_length(self, audio: np.ndarray, target_length: Optional[int] = None) -> np.ndarray:
        """Pad or truncate audio to fixed length."""
        if target_length is None:
            target_length = self.sample_rate * settings.MAX_AUDIO_LENGTH_SECONDS
        
        if len(audio) > target_length:
            # Truncate
            audio = audio[:target_length]
        elif len(audio) < target_length:
            # Pad with zeros
            audio = np.pad(audio, (0, target_length - len(audio)), mode='constant')
        
        return audio


class MelSpectrogramExtractor(IAudioProcessor):
    """
    Alternative audio processor using mel-spectrogram.
    Demonstrates Strategy Pattern - interchangeable with AudioProcessor.
    """
    
    def __init__(
        self,
        sample_rate: int = settings.AUDIO_SAMPLE_RATE,
        n_mels: int = settings.MEL_N_MELS
    ):
        self.sample_rate = sample_rate
        self.n_mels = n_mels
    
    def load_audio(self, file_path: str) -> np.ndarray:
        """Load audio file."""
        audio, sr = librosa.load(file_path, sr=self.sample_rate)
        return audio
    
    def preprocess(self, audio: np.ndarray) -> np.ndarray:
        """Preprocess audio."""
        # Normalize
        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio / max_val
        return audio
    
    def extract_features(self, audio: np.ndarray) -> np.ndarray:
        """Extract mel-spectrogram features."""
        mel_spec = librosa.feature.melspectrogram(
            y=audio,
            sr=self.sample_rate,
            n_mels=self.n_mels
        )
        # Convert to log scale
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        return mel_spec_db
