"""
Key detection and melody extraction services.

This module provides:
- Key signature detection using harmonic analysis
- Melody scanner for melody-only extraction
"""
import librosa
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class KeyDetector:
    """Detects musical key signatures using harmonic analysis."""
    
    # Krumhansl-Schmuckler key profiles
    MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    
    KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    
    def __init__(self, sample_rate: int = 22050):
        """
        Initialize key detector.
        
        Args:
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate
    
    def detect_key(self, y: np.ndarray) -> Dict[str, any]:
        """
        Detect the key signature of audio using Krumhansl-Schmuckler algorithm.
        
        Args:
            y: Audio time series
            
        Returns:
            Dictionary with detected key, mode, and confidence
        """
        # Compute chromagram
        chroma = librosa.feature.chroma_cqt(y=y, sr=self.sample_rate)
        
        # Average chroma over time to get pitch class distribution
        pitch_class_distribution = np.mean(chroma, axis=1)
        
        # Normalize
        if np.sum(pitch_class_distribution) > 0:
            pitch_class_distribution = pitch_class_distribution / np.sum(pitch_class_distribution)
        
        # Correlate with key profiles
        best_key, best_mode, best_correlation = self._find_best_key(pitch_class_distribution)
        
        # Format key name
        key_name = f"{self.KEY_NAMES[best_key]} {best_mode}"
        
        logger.info(f"Detected key: {key_name} (confidence: {best_correlation:.3f})")
        
        return {
            "key": self.KEY_NAMES[best_key],
            "mode": best_mode,
            "key_signature": key_name,
            "confidence": float(best_correlation),
            "pitch_class_distribution": pitch_class_distribution.tolist()
        }
    
    def _find_best_key(
        self,
        pitch_class_distribution: np.ndarray
    ) -> Tuple[int, str, float]:
        """
        Find the best matching key using correlation with key profiles.
        
        Args:
            pitch_class_distribution: 12-element array of pitch class strengths
            
        Returns:
            Tuple of (key_index, mode, correlation)
        """
        best_correlation = -1
        best_key = 0
        best_mode = "major"
        
        # Try all 24 keys (12 major + 12 minor)
        for key_idx in range(12):
            # Rotate profiles to match this key
            major_profile = np.roll(self.MAJOR_PROFILE, key_idx)
            minor_profile = np.roll(self.MINOR_PROFILE, key_idx)
            
            # Normalize profiles
            major_profile = major_profile / np.sum(major_profile)
            minor_profile = minor_profile / np.sum(minor_profile)
            
            # Calculate correlation
            major_corr = np.corrcoef(pitch_class_distribution, major_profile)[0, 1]
            minor_corr = np.corrcoef(pitch_class_distribution, minor_profile)[0, 1]
            
            # Check if this is the best match
            if major_corr > best_correlation:
                best_correlation = major_corr
                best_key = key_idx
                best_mode = "major"
            
            if minor_corr > best_correlation:
                best_correlation = minor_corr
                best_key = key_idx
                best_mode = "minor"
        
        return best_key, best_mode, best_correlation
    
    def transpose_key(self, current_key: str, semitones: int) -> str:
        """
        Transpose a key by a number of semitones.
        
        Args:
            current_key: Current key signature (e.g., "C major")
            semitones: Number of semitones to transpose (positive or negative)
            
        Returns:
            New key signature
        """
        # Parse current key
        parts = current_key.split()
        if len(parts) != 2:
            raise ValueError(f"Invalid key format: {current_key}")
        
        key_name, mode = parts
        
        # Find current key index
        try:
            key_idx = self.KEY_NAMES.index(key_name)
        except ValueError:
            raise ValueError(f"Unknown key: {key_name}")
        
        # Transpose
        new_key_idx = (key_idx + semitones) % 12
        new_key_name = self.KEY_NAMES[new_key_idx]
        
        return f"{new_key_name} {mode}"


class MelodyScanner:
    """Extracts melody-only transcription from audio."""
    
    def __init__(self, sample_rate: int = 22050):
        """
        Initialize melody scanner.
        
        Args:
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate
    
    def extract_melody(self, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract the dominant melodic line from audio.
        
        Uses harmonic-percussive source separation and pitch tracking
        to isolate the main melody.
        
        Args:
            y: Audio time series
            
        Returns:
            Tuple of (melody_frequencies, times)
        """
        # Separate harmonic and percussive components
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        
        # Track pitch on harmonic component
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y_harmonic,
            fmin=librosa.note_to_hz('C3'),
            fmax=librosa.note_to_hz('C6'),
            sr=self.sample_rate
        )
        
        # Get time array
        times = librosa.times_like(f0, sr=self.sample_rate)
        
        # Filter by voicing probability (keep only confident melody notes)
        melody_threshold = 0.5
        f0_melody = np.where(voiced_probs > melody_threshold, f0, np.nan)
        
        # Smooth melody line (remove rapid fluctuations)
        f0_melody = self._smooth_melody(f0_melody)
        
        logger.info(f"Extracted melody: {np.sum(~np.isnan(f0_melody))} voiced frames")
        
        return f0_melody, times
    
    def _smooth_melody(self, f0: np.ndarray, window_size: int = 5) -> np.ndarray:
        """
        Smooth melody line using median filtering.
        
        Args:
            f0: Frequency array (may contain NaN)
            window_size: Size of smoothing window
            
        Returns:
            Smoothed frequency array
        """
        from scipy.ndimage import median_filter
        
        # Create mask for valid values
        valid_mask = ~np.isnan(f0)
        
        if not np.any(valid_mask):
            return f0
        
        # Apply median filter only to valid regions
        f0_smooth = f0.copy()
        
        # Fill NaN with interpolation for filtering
        f0_filled = f0.copy()
        if np.any(valid_mask):
            # Simple forward fill for NaN values
            last_valid = None
            for i in range(len(f0_filled)):
                if valid_mask[i]:
                    last_valid = f0_filled[i]
                elif last_valid is not None:
                    f0_filled[i] = last_valid
        
        # Apply median filter
        f0_filtered = median_filter(f0_filled, size=window_size, mode='nearest')
        
        # Restore NaN where original was NaN
        f0_smooth = np.where(valid_mask, f0_filtered, np.nan)
        
        return f0_smooth
    
    def melody_to_notes(
        self,
        melody_frequencies: np.ndarray,
        times: np.ndarray,
        min_duration: float = 0.1
    ) -> List[Dict[str, any]]:
        """
        Convert melody frequency contour to discrete notes.
        
        Args:
            melody_frequencies: Array of melody frequencies
            times: Corresponding time array
            min_duration: Minimum note duration in seconds
            
        Returns:
            List of melody notes
        """
        notes = []
        current_note = None
        
        for i, (freq, time) in enumerate(zip(melody_frequencies, times)):
            if np.isnan(freq):
                # End current note if exists
                if current_note is not None:
                    duration = time - current_note["onset"]
                    if duration >= min_duration:
                        current_note["duration"] = float(duration)
                        notes.append(current_note)
                    current_note = None
                continue
            
            # Convert to MIDI note
            midi_note = librosa.hz_to_midi(freq)
            midi_note_rounded = int(np.round(midi_note))
            
            # Start new note or continue current
            if current_note is None:
                current_note = {
                    "onset": float(time),
                    "pitch": midi_note_rounded,
                    "frequency": float(freq)
                }
            else:
                # Check if pitch changed significantly
                if abs(midi_note_rounded - current_note["pitch"]) > 0.5:
                    # End current note
                    duration = time - current_note["onset"]
                    if duration >= min_duration:
                        current_note["duration"] = float(duration)
                        notes.append(current_note)
                    
                    # Start new note
                    current_note = {
                        "onset": float(time),
                        "pitch": midi_note_rounded,
                        "frequency": float(freq)
                    }
        
        # Add final note
        if current_note is not None:
            if len(times) > 0:
                duration = times[-1] - current_note["onset"]
                if duration >= min_duration:
                    current_note["duration"] = float(duration)
                    notes.append(current_note)
        
        logger.info(f"Converted melody to {len(notes)} notes")
        return notes
    
    def scan_melody(self, y: np.ndarray) -> List[Dict[str, any]]:
        """
        Complete melody scanning pipeline.
        
        Args:
            y: Audio time series
            
        Returns:
            List of melody notes
        """
        # Extract melody
        melody_frequencies, times = self.extract_melody(y)
        
        # Convert to notes
        notes = self.melody_to_notes(melody_frequencies, times)
        
        return notes
