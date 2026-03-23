"""
Unit tests for transcription engine core functions.
"""
import pytest
import numpy as np
import librosa
from app.services.transcription_engine import TranscriptionEngine
from app.services.polyphonic_transcription import PolyphonicTranscriber


class TestTranscriptionEngine:
    """Test cases for TranscriptionEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create a transcription engine instance."""
        return TranscriptionEngine(sample_rate=22050)
    
    @pytest.fixture
    def sample_audio(self):
        """Generate a simple test audio signal (440 Hz sine wave)."""
        sr = 22050
        duration = 2.0
        frequency = 440.0  # A4
        t = np.linspace(0, duration, int(sr * duration))
        y = 0.5 * np.sin(2 * np.pi * frequency * t)
        return y, sr
    
    def test_preprocess_audio(self, engine, sample_audio):
        """Test audio preprocessing."""
        y, sr = sample_audio
        
        # Preprocess
        y_processed = engine.preprocess_audio(y)
        
        # Check output is normalized
        assert np.max(np.abs(y_processed)) <= 1.0
        assert len(y_processed) == len(y)
        assert isinstance(y_processed, np.ndarray)
    
    def test_detect_onsets(self, engine):
        """Test onset detection."""
        # Create audio with clear onsets (two notes)
        sr = 22050
        note1 = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, int(sr * 0.5)))
        silence = np.zeros(int(sr * 0.2))
        note2 = 0.5 * np.sin(2 * np.pi * 523 * np.linspace(0, 0.5, int(sr * 0.5)))
        y = np.concatenate([note1, silence, note2])
        
        # Detect onsets
        onset_times = engine.detect_onsets(y)
        
        # Should detect at least one onset
        assert len(onset_times) >= 1
        assert isinstance(onset_times, np.ndarray)
        # Onsets should be in valid time range
        assert np.all(onset_times >= 0)
        assert np.all(onset_times <= librosa.get_duration(y=y, sr=sr))
    
    def test_track_pitch(self, engine, sample_audio):
        """Test pitch tracking."""
        y, sr = sample_audio
        
        # Track pitch
        f0, times = engine.track_pitch(y)
        
        # Check output shapes
        assert len(f0) == len(times)
        assert len(f0) > 0
        
        # Check that detected frequency is close to 440 Hz (allowing for some error)
        valid_f0 = f0[~np.isnan(f0)]
        if len(valid_f0) > 0:
            mean_freq = np.mean(valid_f0)
            assert 400 < mean_freq < 480  # Within reasonable range of 440 Hz
    
    def test_detect_notes(self, engine):
        """Test note detection."""
        # Create simple audio with one clear note
        sr = 22050
        duration = 1.0
        frequency = 440.0  # A4 (MIDI 69)
        t = np.linspace(0, duration, int(sr * duration))
        y = 0.5 * np.sin(2 * np.pi * frequency * t)
        
        # Detect notes
        notes = engine.detect_notes(y)
        
        # Should detect at least one note
        assert len(notes) >= 1
        
        # Check note structure
        for note in notes:
            assert "onset" in note
            assert "pitch" in note
            assert "frequency" in note
            assert "duration" in note
            assert note["onset"] >= 0
            assert 0 <= note["pitch"] <= 127  # Valid MIDI range
            assert note["duration"] > 0
    
    def test_detect_tempo_and_beats(self, engine):
        """Test tempo and beat detection."""
        # Create audio with regular beats
        sr = 22050
        tempo = 120  # BPM
        beat_duration = 60.0 / tempo
        num_beats = 8
        
        # Create clicks at beat positions
        y = np.zeros(int(sr * num_beats * beat_duration))
        for i in range(num_beats):
            pos = int(i * beat_duration * sr)
            if pos < len(y):
                y[pos:pos+100] = 0.5
        
        # Detect tempo and beats
        detected_tempo, beat_times = engine.detect_tempo_and_beats(y)
        
        # Check tempo is reasonable
        assert 60 <= detected_tempo <= 200
        
        # Check beats are detected
        assert len(beat_times) > 0
        assert isinstance(beat_times, np.ndarray)
    
    def test_quantize_rhythm(self, engine):
        """Test rhythm quantization."""
        # Create test notes with slightly off-grid timings
        notes = [
            {"onset": 0.01, "pitch": 60, "frequency": 261.63, "duration": 0.48},
            {"onset": 0.52, "pitch": 62, "frequency": 293.66, "duration": 0.47},
            {"onset": 1.03, "pitch": 64, "frequency": 329.63, "duration": 0.49},
        ]
        
        tempo = 120.0
        beat_times = np.array([0.0, 0.5, 1.0, 1.5])
        
        # Quantize
        quantized = engine.quantize_rhythm(notes, tempo, beat_times)
        
        # Check quantization
        assert len(quantized) == len(notes)
        for note in quantized:
            assert "onset" in note
            assert "duration" in note
            assert "original_onset" in note
            assert "original_duration" in note
            # Quantized values should be on grid
            beat_duration = 60.0 / tempo
            grid_resolution = beat_duration / 4
            assert note["onset"] % grid_resolution < 0.001 or note["onset"] % grid_resolution > grid_resolution - 0.001
    
    def test_generate_notation_data(self, engine):
        """Test notation data structure generation."""
        notes = [
            {"onset": 0.0, "pitch": 60, "frequency": 261.63, "duration": 0.5},
            {"onset": 0.5, "pitch": 62, "frequency": 293.66, "duration": 0.5},
            {"onset": 1.0, "pitch": 64, "frequency": 329.63, "duration": 0.5},
        ]
        
        tempo = 120.0
        duration = 2.0
        instrument_type = "piano"
        
        # Generate notation data
        notation_data = engine.generate_notation_data(notes, tempo, duration, instrument_type)
        
        # Check structure
        assert "version" in notation_data
        assert "instrument" in notation_data
        assert "tempo" in notation_data
        assert "key" in notation_data
        assert "time_signature" in notation_data
        assert "duration" in notation_data
        assert "notes" in notation_data
        assert "metadata" in notation_data
        
        # Check values
        assert notation_data["instrument"] == instrument_type
        assert notation_data["tempo"] == tempo
        assert notation_data["duration"] == duration
        assert len(notation_data["notes"]) == len(notes)
        assert notation_data["metadata"]["total_notes"] == len(notes)
        
        # Check time signature structure
        assert "numerator" in notation_data["time_signature"]
        assert "denominator" in notation_data["time_signature"]
    
    def test_empty_audio_handling(self, engine):
        """Test handling of silent/empty audio."""
        # Create silent audio
        y = np.zeros(22050)  # 1 second of silence
        
        # Should not crash
        notes = engine.detect_notes(y)
        
        # May detect no notes or very few
        assert isinstance(notes, list)


class TestPolyphonicTranscriber:
    """Test cases for PolyphonicTranscriber."""
    
    @pytest.fixture
    def transcriber(self):
        """Create a polyphonic transcriber instance."""
        return PolyphonicTranscriber(sample_rate=22050)
    
    def test_detect_multi_pitch(self, transcriber):
        """Test multi-pitch detection."""
        # Create audio with two simultaneous frequencies (chord)
        sr = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration))
        
        # C major chord: C (261.63 Hz), E (329.63 Hz), G (392.00 Hz)
        y = (0.3 * np.sin(2 * np.pi * 261.63 * t) +
             0.3 * np.sin(2 * np.pi * 329.63 * t) +
             0.3 * np.sin(2 * np.pi * 392.00 * t))
        
        # Detect multiple pitches
        voice_frequencies, times = transcriber.detect_multi_pitch(y, max_voices=3)
        
        # Check output structure
        assert len(voice_frequencies) == 3
        assert len(times) > 0
        for voice in voice_frequencies:
            assert len(voice) == len(times)
    
    def test_separate_voices(self, transcriber):
        """Test voice separation."""
        # Create mock voice frequencies
        times = np.linspace(0, 2.0, 100)
        voice_frequencies = [
            np.full(100, 440.0),  # Voice 1: constant A4
            np.full(100, 523.25),  # Voice 2: constant C5
        ]
        
        onset_times = np.array([0.0, 0.5, 1.0, 1.5])
        
        # Separate voices
        separated = transcriber.separate_voices(voice_frequencies, times, onset_times)
        
        # Check output structure
        assert len(separated) == 2
        for voice_notes in separated:
            assert isinstance(voice_notes, list)
            for note in voice_notes:
                assert "onset" in note
                assert "pitch" in note
                assert "frequency" in note
                assert "voice" in note
    
    def test_merge_voices(self, transcriber):
        """Test merging separated voices."""
        # Create mock separated voices
        separated_voices = [
            [
                {"onset": 0.0, "pitch": 60, "frequency": 261.63, "duration": 0.5, "voice": 0},
                {"onset": 1.0, "pitch": 62, "frequency": 293.66, "duration": 0.5, "voice": 0},
            ],
            [
                {"onset": 0.5, "pitch": 64, "frequency": 329.63, "duration": 0.5, "voice": 1},
                {"onset": 1.5, "pitch": 65, "frequency": 349.23, "duration": 0.5, "voice": 1},
            ]
        ]
        
        # Merge
        merged = transcriber.merge_voices(separated_voices)
        
        # Check output
        assert len(merged) == 4
        # Should be sorted by onset
        for i in range(len(merged) - 1):
            assert merged[i]["onset"] <= merged[i + 1]["onset"]
    
    def test_find_spectral_peaks(self, transcriber):
        """Test spectral peak finding."""
        # Create spectrum with clear peaks
        spectrum = np.zeros(100)
        spectrum[20] = 0.8  # Peak 1
        spectrum[50] = 1.0  # Peak 2 (highest)
        spectrum[80] = 0.6  # Peak 3
        
        # Find peaks
        peaks = transcriber._find_spectral_peaks(spectrum, max_peaks=3, threshold=0.1)
        
        # Check output
        assert len(peaks) == 3
        # Should find the three peaks
        assert 50 in peaks  # Highest peak should be found
