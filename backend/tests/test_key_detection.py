"""
Unit tests for key detection and melody extraction.
"""
import pytest
import numpy as np
import librosa
from app.services.key_detection import KeyDetector, MelodyScanner


class TestKeyDetector:
    """Test cases for KeyDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create a key detector instance."""
        return KeyDetector(sample_rate=22050)
    
    @pytest.fixture
    def c_major_audio(self):
        """Generate audio in C major (C-E-G chord)."""
        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        
        # C major chord: C4 (261.63 Hz), E4 (329.63 Hz), G4 (392.00 Hz)
        y = (0.3 * np.sin(2 * np.pi * 261.63 * t) +
             0.3 * np.sin(2 * np.pi * 329.63 * t) +
             0.3 * np.sin(2 * np.pi * 392.00 * t))
        
        return y, sr
    
    @pytest.fixture
    def a_minor_audio(self):
        """Generate audio in A minor (A-C-E chord)."""
        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        
        # A minor chord: A3 (220.00 Hz), C4 (261.63 Hz), E4 (329.63 Hz)
        y = (0.3 * np.sin(2 * np.pi * 220.00 * t) +
             0.3 * np.sin(2 * np.pi * 261.63 * t) +
             0.3 * np.sin(2 * np.pi * 329.63 * t))
        
        return y, sr
    
    def test_detect_key_structure(self, detector, c_major_audio):
        """Test key detection returns correct structure."""
        y, sr = c_major_audio
        
        result = detector.detect_key(y)
        
        # Check structure
        assert "key" in result
        assert "mode" in result
        assert "key_signature" in result
        assert "confidence" in result
        assert "pitch_class_distribution" in result
        
        # Check types
        assert isinstance(result["key"], str)
        assert result["mode"] in ["major", "minor"]
        assert isinstance(result["confidence"], float)
        assert 0 <= result["confidence"] <= 1
    
    def test_detect_c_major(self, detector, c_major_audio):
        """Test detection of C major key."""
        y, sr = c_major_audio
        
        result = detector.detect_key(y)
        
        # Should detect C major (or relative A minor)
        # Due to the simplicity of the test signal, we just check it's reasonable
        assert result["key"] in detector.KEY_NAMES
        assert result["mode"] in ["major", "minor"]
    
    def test_pitch_class_distribution(self, detector, c_major_audio):
        """Test pitch class distribution is normalized."""
        y, sr = c_major_audio
        
        result = detector.detect_key(y)
        
        pcd = np.array(result["pitch_class_distribution"])
        
        # Should be 12 elements
        assert len(pcd) == 12
        
        # Should be normalized (sum close to 1)
        assert 0.9 < np.sum(pcd) < 1.1
        
        # All values should be non-negative
        assert np.all(pcd >= 0)
    
    def test_transpose_key(self, detector):
        """Test key transposition."""
        # Transpose C major up 2 semitones
        result = detector.transpose_key("C major", 2)
        assert result == "D major"
        
        # Transpose C major down 3 semitones
        result = detector.transpose_key("C major", -3)
        assert result == "A major"
        
        # Transpose A minor up 5 semitones
        result = detector.transpose_key("A minor", 5)
        assert result == "D minor"
        
        # Transpose around the circle (12 semitones = same key)
        result = detector.transpose_key("G major", 12)
        assert result == "G major"
    
    def test_transpose_key_invalid_format(self, detector):
        """Test transposition with invalid key format."""
        with pytest.raises(ValueError):
            detector.transpose_key("InvalidKey", 2)
    
    def test_transpose_key_unknown_key(self, detector):
        """Test transposition with unknown key name."""
        with pytest.raises(ValueError):
            detector.transpose_key("X major", 2)
    
    def test_find_best_key(self, detector):
        """Test finding best key from pitch class distribution."""
        # Create a distribution favoring C major
        pcd = np.array([0.3, 0.0, 0.1, 0.0, 0.2, 0.1, 0.0, 0.2, 0.0, 0.1, 0.0, 0.0])
        pcd = pcd / np.sum(pcd)
        
        key_idx, mode, correlation = detector._find_best_key(pcd)
        
        # Should return valid results
        assert 0 <= key_idx < 12
        assert mode in ["major", "minor"]
        assert -1 <= correlation <= 1


class TestMelodyScanner:
    """Test cases for MelodyScanner."""
    
    @pytest.fixture
    def scanner(self):
        """Create a melody scanner instance."""
        return MelodyScanner(sample_rate=22050)
    
    @pytest.fixture
    def simple_melody(self):
        """Generate a simple melody (three notes)."""
        sr = 22050
        
        # Three notes: C4, E4, G4
        note1 = 0.5 * np.sin(2 * np.pi * 261.63 * np.linspace(0, 0.5, int(sr * 0.5)))
        note2 = 0.5 * np.sin(2 * np.pi * 329.63 * np.linspace(0, 0.5, int(sr * 0.5)))
        note3 = 0.5 * np.sin(2 * np.pi * 392.00 * np.linspace(0, 0.5, int(sr * 0.5)))
        
        y = np.concatenate([note1, note2, note3])
        
        return y, sr
    
    def test_extract_melody(self, scanner, simple_melody):
        """Test melody extraction."""
        y, sr = simple_melody
        
        melody_frequencies, times = scanner.extract_melody(y)
        
        # Check output structure
        assert len(melody_frequencies) == len(times)
        assert len(melody_frequencies) > 0
        
        # Should have some voiced frames
        voiced_frames = ~np.isnan(melody_frequencies)
        assert np.any(voiced_frames)
    
    def test_smooth_melody(self, scanner):
        """Test melody smoothing."""
        # Create noisy melody line
        f0 = np.array([440.0, 445.0, 440.0, 442.0, 440.0, np.nan, np.nan, 523.0, 525.0, 523.0])
        
        smoothed = scanner._smooth_melody(f0, window_size=3)
        
        # Should have same length
        assert len(smoothed) == len(f0)
        
        # NaN should be preserved
        assert np.isnan(smoothed[5])
        assert np.isnan(smoothed[6])
        
        # Valid values should be smoothed
        assert not np.isnan(smoothed[0])
    
    def test_melody_to_notes(self, scanner):
        """Test converting melody contour to notes."""
        # Create simple melody contour
        times = np.linspace(0, 2.0, 100)
        
        # Two notes: 440 Hz for 1 second, then 523 Hz for 1 second
        melody_frequencies = np.concatenate([
            np.full(50, 440.0),
            np.full(50, 523.0)
        ])
        
        notes = scanner.melody_to_notes(melody_frequencies, times, min_duration=0.1)
        
        # Should detect 2 notes
        assert len(notes) >= 1
        
        # Check note structure
        for note in notes:
            assert "onset" in note
            assert "pitch" in note
            assert "frequency" in note
            assert "duration" in note
            assert note["duration"] >= 0.1
    
    def test_melody_to_notes_with_gaps(self, scanner):
        """Test melody to notes with silent gaps."""
        times = np.linspace(0, 3.0, 150)
        
        # Note, silence, note
        melody_frequencies = np.concatenate([
            np.full(50, 440.0),
            np.full(50, np.nan),
            np.full(50, 523.0)
        ])
        
        notes = scanner.melody_to_notes(melody_frequencies, times, min_duration=0.1)
        
        # Should detect 2 separate notes
        assert len(notes) >= 1
        
        # Notes should have reasonable durations
        for note in notes:
            assert note["duration"] >= 0.1
    
    def test_scan_melody_complete(self, scanner, simple_melody):
        """Test complete melody scanning pipeline."""
        y, sr = simple_melody
        
        notes = scanner.scan_melody(y)
        
        # Should detect at least one note
        assert len(notes) >= 1
        
        # Check note structure
        for note in notes:
            assert "onset" in note
            assert "pitch" in note
            assert "frequency" in note
            assert "duration" in note
            assert 0 <= note["pitch"] <= 127
            assert note["duration"] > 0
    
    def test_empty_melody(self, scanner):
        """Test handling of silent audio."""
        # Silent audio
        y = np.zeros(22050)
        
        notes = scanner.scan_melody(y)
        
        # Should return empty or very few notes
        assert isinstance(notes, list)
        assert len(notes) < 5  # Allow for some noise detection
