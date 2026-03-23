"""
Polyphonic transcription module for detecting multiple simultaneous notes.

This module extends the base transcription engine with:
- Multi-pitch detection algorithms for simultaneous notes
- Voice separation for multiple melodic lines
"""
import librosa
import numpy as np
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class PolyphonicTranscriber:
    """Handles polyphonic transcription with multi-pitch detection."""
    
    def __init__(self, sample_rate: int = 22050):
        """
        Initialize polyphonic transcriber.
        
        Args:
            sample_rate: Target sample rate for audio processing
        """
        self.sample_rate = sample_rate
        self.hop_length = 512
        self.n_fft = 2048
    
    def detect_multi_pitch(
        self,
        y: np.ndarray,
        max_voices: int = 4
    ) -> Tuple[List[np.ndarray], np.ndarray]:
        """
        Detect multiple simultaneous pitches using spectral analysis.
        
        Args:
            y: Audio time series
            max_voices: Maximum number of simultaneous voices to detect
            
        Returns:
            Tuple of (list of frequency arrays for each voice, time array)
        """
        # Compute CQT (Constant-Q Transform) for better pitch resolution
        cqt = np.abs(librosa.cqt(
            y,
            sr=self.sample_rate,
            hop_length=self.hop_length,
            n_bins=84,  # 7 octaves
            bins_per_octave=12
        ))
        
        # Get time array
        times = librosa.times_like(cqt, sr=self.sample_rate, hop_length=self.hop_length)
        
        # Detect peaks in each time frame
        voices = [[] for _ in range(max_voices)]
        
        for frame_idx in range(cqt.shape[1]):
            frame = cqt[:, frame_idx]
            
            # Find peaks in the spectrum
            peaks = self._find_spectral_peaks(frame, max_peaks=max_voices)
            
            # Assign peaks to voices
            for voice_idx, peak_bin in enumerate(peaks):
                if peak_bin is not None:
                    # Convert CQT bin to frequency
                    freq = librosa.cqt_frequencies(
                        n_bins=84,
                        fmin=librosa.note_to_hz('C2'),
                        bins_per_octave=12
                    )[peak_bin]
                    voices[voice_idx].append(freq)
                else:
                    voices[voice_idx].append(np.nan)
        
        # Convert to numpy arrays
        voice_arrays = [np.array(voice) for voice in voices]
        
        logger.info(f"Detected up to {max_voices} simultaneous voices over {len(times)} frames")
        return voice_arrays, times
    
    def _find_spectral_peaks(
        self,
        spectrum: np.ndarray,
        max_peaks: int = 4,
        threshold: float = 0.1
    ) -> List[int]:
        """
        Find peaks in a spectrum frame.
        
        Args:
            spectrum: Magnitude spectrum
            max_peaks: Maximum number of peaks to find
            threshold: Minimum relative magnitude threshold
            
        Returns:
            List of peak bin indices (None for missing peaks)
        """
        # Normalize spectrum
        if np.max(spectrum) > 0:
            spectrum_norm = spectrum / np.max(spectrum)
        else:
            return [None] * max_peaks
        
        # Find local maxima
        peaks = []
        for i in range(1, len(spectrum_norm) - 1):
            if (spectrum_norm[i] > spectrum_norm[i-1] and
                spectrum_norm[i] > spectrum_norm[i+1] and
                spectrum_norm[i] > threshold):
                peaks.append((i, spectrum_norm[i]))
        
        # Sort by magnitude and take top peaks
        peaks.sort(key=lambda x: x[1], reverse=True)
        peak_bins = [p[0] for p in peaks[:max_peaks]]
        
        # Pad with None if fewer peaks found
        while len(peak_bins) < max_peaks:
            peak_bins.append(None)
        
        return peak_bins
    
    def separate_voices(
        self,
        voice_frequencies: List[np.ndarray],
        times: np.ndarray,
        onset_times: np.ndarray
    ) -> List[List[Dict[str, Any]]]:
        """
        Separate detected pitches into distinct melodic lines.
        
        Args:
            voice_frequencies: List of frequency arrays for each voice
            times: Time array corresponding to frequency frames
            onset_times: Detected onset times
            
        Returns:
            List of note lists, one for each voice
        """
        separated_voices = []
        
        for voice_idx, frequencies in enumerate(voice_frequencies):
            notes = []
            
            # Track continuous pitch segments
            current_note = None
            
            for onset in onset_times:
                # Find frequency at this onset
                idx = np.argmin(np.abs(times - onset))
                freq = frequencies[idx]
                
                # Skip if no pitch detected
                if np.isnan(freq):
                    if current_note is not None:
                        notes.append(current_note)
                        current_note = None
                    continue
                
                # Convert to MIDI note
                midi_note = librosa.hz_to_midi(freq)
                
                # Start new note or continue current
                if current_note is None:
                    current_note = {
                        "onset": float(onset),
                        "pitch": int(np.round(midi_note)),
                        "frequency": float(freq),
                        "voice": voice_idx
                    }
                else:
                    # Check if pitch changed significantly (more than 1 semitone)
                    if abs(midi_note - current_note["pitch"]) > 1:
                        # End current note and start new one
                        current_note["duration"] = float(onset - current_note["onset"])
                        notes.append(current_note)
                        
                        current_note = {
                            "onset": float(onset),
                            "pitch": int(np.round(midi_note)),
                            "frequency": float(freq),
                            "voice": voice_idx
                        }
            
            # Add final note if exists
            if current_note is not None:
                # Estimate duration from last onset to end
                current_note["duration"] = 0.5  # Default duration
                notes.append(current_note)
            
            separated_voices.append(notes)
            logger.info(f"Voice {voice_idx}: {len(notes)} notes")
        
        return separated_voices
    
    def merge_voices(
        self,
        separated_voices: List[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Merge separated voices into a single note list with voice labels.
        
        Args:
            separated_voices: List of note lists for each voice
            
        Returns:
            Combined and sorted note list
        """
        # Flatten all voices
        all_notes = []
        for notes in separated_voices:
            all_notes.extend(notes)
        
        # Sort by onset time
        all_notes.sort(key=lambda n: n["onset"])
        
        logger.info(f"Merged {len(all_notes)} notes from {len(separated_voices)} voices")
        return all_notes
    
    def transcribe_polyphonic(
        self,
        y: np.ndarray,
        onset_times: np.ndarray,
        max_voices: int = 4
    ) -> Dict[str, Any]:
        """
        Complete polyphonic transcription pipeline.
        
        Args:
            y: Audio time series
            onset_times: Detected onset times
            max_voices: Maximum number of simultaneous voices
            
        Returns:
            Dictionary with separated voices and merged notes
        """
        # Detect multiple pitches
        voice_frequencies, times = self.detect_multi_pitch(y, max_voices=max_voices)
        
        # Separate into melodic lines
        separated_voices = self.separate_voices(voice_frequencies, times, onset_times)
        
        # Merge all voices
        all_notes = self.merge_voices(separated_voices)
        
        return {
            "voices": separated_voices,
            "all_notes": all_notes,
            "num_voices": len([v for v in separated_voices if len(v) > 0])
        }
