"""
AI Transcription Engine using librosa for audio processing.

This module provides core transcription functionality including:
- Audio loading and preprocessing
- Note detection using onset detection and pitch tracking
- Rhythm quantization and beat tracking
- Basic notation data structure generation
"""
import librosa
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TranscriptionEngine:
    """Core transcription engine for converting audio to musical notation."""
    
    def __init__(self, sample_rate: int = 22050):
        """
        Initialize transcription engine.
        
        Args:
            sample_rate: Target sample rate for audio processing
        """
        self.sample_rate = sample_rate
    
    def load_audio(self, audio_path: str, duration: Optional[float] = None) -> Tuple[np.ndarray, float]:
        """
        Load and preprocess audio file.
        
        Args:
            audio_path: Path to audio file
            duration: Optional duration limit in seconds
            
        Returns:
            Tuple of (audio_data, actual_duration)
        """
        try:
            # Load audio with librosa
            y, sr = librosa.load(audio_path, sr=self.sample_rate, duration=duration)
            
            # Calculate actual duration
            actual_duration = librosa.get_duration(y=y, sr=sr)
            
            logger.info(f"Loaded audio: {actual_duration:.2f}s at {sr}Hz")
            return y, actual_duration
            
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            raise ValueError(f"Failed to load audio file: {str(e)}")
    
    def preprocess_audio(self, y: np.ndarray) -> np.ndarray:
        """
        Preprocess audio for transcription.
        
        Args:
            y: Audio time series
            
        Returns:
            Preprocessed audio
        """
        # Normalize audio
        y = librosa.util.normalize(y)
        
        # Apply pre-emphasis filter to enhance high frequencies
        y = librosa.effects.preemphasis(y)
        
        return y
    
    def detect_onsets(self, y: np.ndarray) -> np.ndarray:
        """
        Detect note onsets in audio.
        
        Args:
            y: Audio time series
            
        Returns:
            Array of onset times in seconds
        """
        # Detect onsets using spectral flux
        onset_frames = librosa.onset.onset_detect(
            y=y,
            sr=self.sample_rate,
            units='frames',
            hop_length=512,
            backtrack=True
        )
        
        # Convert frames to time
        onset_times = librosa.frames_to_time(
            onset_frames,
            sr=self.sample_rate,
            hop_length=512
        )
        
        logger.info(f"Detected {len(onset_times)} onsets")
        return onset_times
    
    def track_pitch(self, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Track pitch over time using pYIN algorithm.
        
        Args:
            y: Audio time series
            
        Returns:
            Tuple of (frequencies, times) arrays
        """
        # Use pYIN for pitch tracking (better for music)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=self.sample_rate
        )
        
        # Get time array
        times = librosa.times_like(f0, sr=self.sample_rate)
        
        # Filter out unvoiced regions
        f0_filtered = np.where(voiced_flag, f0, np.nan)
        
        logger.info(f"Tracked pitch over {len(times)} frames")
        return f0_filtered, times

    
    def detect_notes(self, y: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect notes using onset detection and pitch tracking.
        
        Args:
            y: Audio time series
            
        Returns:
            List of note dictionaries with onset, pitch, and duration
        """
        # Detect onsets
        onset_times = self.detect_onsets(y)
        
        # Track pitch
        f0, times = self.track_pitch(y)
        
        # Match onsets with pitches
        notes = []
        for i, onset in enumerate(onset_times):
            # Find the pitch at this onset time
            idx = np.argmin(np.abs(times - onset))
            frequency = f0[idx]
            
            # Skip if no pitch detected
            if np.isnan(frequency):
                continue
            
            # Convert frequency to MIDI note number
            midi_note = librosa.hz_to_midi(frequency)
            
            # Calculate duration (time to next onset or end)
            if i < len(onset_times) - 1:
                duration = onset_times[i + 1] - onset
            else:
                duration = librosa.get_duration(y=y, sr=self.sample_rate) - onset
            
            notes.append({
                "onset": float(onset),
                "pitch": int(np.round(midi_note)),
                "frequency": float(frequency),
                "duration": float(duration)
            })
        
        logger.info(f"Detected {len(notes)} notes")
        return notes
    
    def detect_tempo_and_beats(self, y: np.ndarray) -> Tuple[float, np.ndarray]:
        """
        Detect tempo and beat positions.
        
        Args:
            y: Audio time series
            
        Returns:
            Tuple of (tempo_bpm, beat_times)
        """
        # Estimate tempo
        tempo, beats = librosa.beat.beat_track(y=y, sr=self.sample_rate, units='time')
        
        # Convert tempo to float (librosa returns array in newer versions)
        tempo_value = float(tempo) if isinstance(tempo, (int, float)) else float(tempo[0])
        
        logger.info(f"Detected tempo: {tempo_value:.2f} BPM with {len(beats)} beats")
        return tempo_value, beats
    
    def quantize_rhythm(
        self,
        notes: List[Dict[str, Any]],
        tempo: float,
        beat_times: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Quantize note timings to musical grid.
        
        Args:
            notes: List of detected notes
            tempo: Tempo in BPM
            beat_times: Array of beat times in seconds
            
        Returns:
            List of quantized notes
        """
        if len(beat_times) == 0:
            logger.warning("No beats detected, skipping quantization")
            return notes
        
        # Calculate beat duration
        beat_duration = 60.0 / tempo
        
        # Define quantization grid (16th notes)
        grid_resolution = beat_duration / 4  # 16th note
        
        quantized_notes = []
        for note in notes:
            # Quantize onset to nearest grid position
            quantized_onset = np.round(note["onset"] / grid_resolution) * grid_resolution
            
            # Quantize duration to nearest grid position
            quantized_duration = max(
                grid_resolution,
                np.round(note["duration"] / grid_resolution) * grid_resolution
            )
            
            quantized_notes.append({
                **note,
                "onset": float(quantized_onset),
                "duration": float(quantized_duration),
                "original_onset": note["onset"],
                "original_duration": note["duration"]
            })
        
        logger.info(f"Quantized {len(quantized_notes)} notes to {grid_resolution:.4f}s grid")
        return quantized_notes
    
    def generate_notation_data(
        self,
        notes: List[Dict[str, Any]],
        tempo: float,
        duration: float,
        instrument_type: str
    ) -> Dict[str, Any]:
        """
        Generate notation data structure from detected notes.
        
        Args:
            notes: List of detected and quantized notes
            tempo: Tempo in BPM
            duration: Total audio duration in seconds
            instrument_type: Type of instrument
            
        Returns:
            Notation data structure
        """
        # Detect key signature (simplified - use most common pitch class)
        if notes:
            pitch_classes = [note["pitch"] % 12 for note in notes]
            most_common_pc = max(set(pitch_classes), key=pitch_classes.count)
            # Map to key names (simplified)
            key_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            key = key_names[most_common_pc]
        else:
            key = "C"
        
        # Determine time signature (simplified - assume 4/4)
        time_signature = {"numerator": 4, "denominator": 4}
        
        notation_data = {
            "version": "1.0",
            "instrument": instrument_type,
            "tempo": tempo,
            "key": key,
            "time_signature": time_signature,
            "duration": duration,
            "notes": notes,
            "metadata": {
                "total_notes": len(notes),
                "pitch_range": {
                    "min": min([n["pitch"] for n in notes]) if notes else 0,
                    "max": max([n["pitch"] for n in notes]) if notes else 0
                }
            }
        }
        
        logger.info(f"Generated notation data: {len(notes)} notes, {tempo:.2f} BPM, key of {key}")
        return notation_data
    
    def transcribe(
        self,
        audio_path: str,
        instrument_type: str,
        duration_limit: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Complete transcription pipeline.
        
        Args:
            audio_path: Path to audio file
            instrument_type: Type of instrument
            duration_limit: Optional duration limit in seconds
            
        Returns:
            Complete notation data structure
        """
        # Load audio
        y, duration = self.load_audio(audio_path, duration=duration_limit)
        
        # Preprocess
        y = self.preprocess_audio(y)
        
        # Detect notes
        notes = self.detect_notes(y)
        
        # Detect tempo and beats
        tempo, beat_times = self.detect_tempo_and_beats(y)
        
        # Quantize rhythm
        quantized_notes = self.quantize_rhythm(notes, tempo, beat_times)
        
        # Generate notation data
        notation_data = self.generate_notation_data(
            quantized_notes,
            tempo,
            duration,
            instrument_type
        )
        
        return notation_data
