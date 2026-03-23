"""
Integration tests for instrument-specific transcription models.
"""
import pytest
from app.services.instrument_models import (
    InstrumentModelRouter,
    InstrumentType,
    GuitarProcessor,
    BassProcessor,
    PianoProcessor,
    DrumsProcessor
)


class TestInstrumentModelRouter:
    """Test cases for InstrumentModelRouter."""
    
    def test_get_guitar_processor(self):
        """Test routing to guitar processor."""
        processor = InstrumentModelRouter.get_processor("guitar")
        assert isinstance(processor, GuitarProcessor)
    
    def test_get_bass_processor(self):
        """Test routing to bass processor."""
        processor = InstrumentModelRouter.get_processor("bass")
        assert isinstance(processor, BassProcessor)
    
    def test_get_piano_processor(self):
        """Test routing to piano processor."""
        processor = InstrumentModelRouter.get_processor("piano")
        assert isinstance(processor, PianoProcessor)
    
    def test_get_drums_processor(self):
        """Test routing to drums processor."""
        processor = InstrumentModelRouter.get_processor("drums")
        assert isinstance(processor, DrumsProcessor)
    
    def test_case_insensitive_routing(self):
        """Test that routing is case-insensitive."""
        processor1 = InstrumentModelRouter.get_processor("GUITAR")
        processor2 = InstrumentModelRouter.get_processor("Guitar")
        assert isinstance(processor1, GuitarProcessor)
        assert isinstance(processor2, GuitarProcessor)


class TestGuitarProcessor:
    """Test cases for GuitarProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a guitar processor instance."""
        return GuitarProcessor()
    
    @pytest.fixture
    def sample_notes(self):
        """Create sample notes for testing."""
        return [
            {"onset": 0.0, "pitch": 64, "frequency": 329.63, "duration": 0.5},  # E4
            {"onset": 0.5, "pitch": 67, "frequency": 392.00, "duration": 0.5},  # G4
            {"onset": 1.0, "pitch": 71, "frequency": 493.88, "duration": 0.5},  # B4
        ]
    
    def test_generate_tablature(self, processor, sample_notes):
        """Test tablature generation."""
        tablature = processor.generate_tablature(sample_notes)
        
        # Should generate tablature for all notes
        assert len(tablature) == len(sample_notes)
        
        # Check tablature structure
        for tab_note in tablature:
            assert "onset" in tab_note
            assert "duration" in tab_note
            assert "string" in tab_note
            assert "fret" in tab_note
            assert "pitch" in tab_note
            
            # String should be 0-5 (6 strings)
            assert 0 <= tab_note["string"] < 6
            
            # Fret should be 0-24
            assert 0 <= tab_note["fret"] <= 24
    
    def test_find_best_position(self, processor):
        """Test finding best string/fret position."""
        # E4 (MIDI 64) should be playable on multiple strings
        string_num, fret = processor._find_best_position(64, [])
        
        assert string_num is not None
        assert fret is not None
        assert 0 <= string_num < 6
        assert 0 <= fret <= 24
        
        # Verify the position produces the correct pitch
        open_string = processor.string_tunings[string_num]
        assert open_string + fret == 64
    
    def test_unplayable_note(self, processor):
        """Test handling of notes outside guitar range."""
        # Very low note (below E2)
        string_num, fret = processor._find_best_position(20, [])
        
        # Should return None for unplayable notes
        assert string_num is None
        assert fret is None
    
    def test_process_notation(self, processor, sample_notes):
        """Test complete notation processing."""
        notation_data = {
            "notes": sample_notes,
            "tempo": 120,
            "key": "C"
        }
        
        processed = processor.process_notation(notation_data)
        
        # Should add tablature
        assert "tablature" in processed
        assert "instrument_config" in processed
        
        # Check instrument config
        config = processed["instrument_config"]
        assert config["num_strings"] == 6
        assert len(config["tuning"]) == 6
        assert config["max_fret"] == 24


class TestBassProcessor:
    """Test cases for BassProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a bass processor instance."""
        return BassProcessor()
    
    @pytest.fixture
    def sample_notes(self):
        """Create sample bass notes."""
        return [
            {"onset": 0.0, "pitch": 40, "frequency": 82.41, "duration": 0.5},   # E2
            {"onset": 0.5, "pitch": 43, "frequency": 97.99, "duration": 0.5},   # G2
            {"onset": 1.0, "pitch": 45, "frequency": 110.00, "duration": 0.5},  # A2
        ]
    
    def test_generate_tablature(self, processor, sample_notes):
        """Test bass tablature generation."""
        tablature = processor.generate_tablature(sample_notes)
        
        # Should generate tablature for all notes
        assert len(tablature) == len(sample_notes)
        
        # Check tablature structure
        for tab_note in tablature:
            assert "onset" in tab_note
            assert "duration" in tab_note
            assert "string" in tab_note
            assert "fret" in tab_note
            assert "pitch" in tab_note
            
            # String should be 0-3 (4 strings)
            assert 0 <= tab_note["string"] < 4
            
            # Fret should be 0-24
            assert 0 <= tab_note["fret"] <= 24
    
    def test_find_best_position(self, processor):
        """Test finding best string/fret position for bass."""
        # E2 (MIDI 40) should be playable on bass
        string_num, fret = processor._find_best_position(40)
        
        assert string_num is not None
        assert fret is not None
        assert 0 <= string_num < 4
        assert 0 <= fret <= 24
        
        # Verify the position produces the correct pitch
        open_string = processor.string_tunings[string_num]
        assert open_string + fret == 40
    
    def test_process_notation(self, processor, sample_notes):
        """Test complete bass notation processing."""
        notation_data = {
            "notes": sample_notes,
            "tempo": 120,
            "key": "C"
        }
        
        processed = processor.process_notation(notation_data)
        
        # Should add tablature
        assert "tablature" in processed
        assert "instrument_config" in processed
        
        # Check instrument config
        config = processed["instrument_config"]
        assert config["num_strings"] == 4
        assert len(config["tuning"]) == 4
        assert config["max_fret"] == 24


class TestPianoProcessor:
    """Test cases for PianoProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a piano processor instance."""
        return PianoProcessor()
    
    @pytest.fixture
    def sample_notes(self):
        """Create sample piano notes spanning both clefs."""
        return [
            {"onset": 0.0, "pitch": 48, "frequency": 130.81, "duration": 0.5},  # C3 (bass)
            {"onset": 0.0, "pitch": 60, "frequency": 261.63, "duration": 0.5},  # C4 (treble)
            {"onset": 0.5, "pitch": 55, "frequency": 196.00, "duration": 0.5},  # G3 (bass)
            {"onset": 0.5, "pitch": 67, "frequency": 392.00, "duration": 0.5},  # G4 (treble)
            {"onset": 1.0, "pitch": 72, "frequency": 523.25, "duration": 0.5},  # C5 (treble)
        ]
    
    def test_split_grand_staff(self, processor, sample_notes):
        """Test splitting notes into treble and bass clef."""
        treble_notes, bass_notes = processor.split_grand_staff(sample_notes)
        
        # Should split correctly
        assert len(treble_notes) + len(bass_notes) == len(sample_notes)
        
        # Treble notes should be >= C4 (MIDI 60)
        for note in treble_notes:
            assert note["pitch"] >= 60
            assert note["clef"] == "treble"
        
        # Bass notes should be < C4 (MIDI 60)
        for note in bass_notes:
            assert note["pitch"] < 60
            assert note["clef"] == "bass"
    
    def test_process_notation(self, processor, sample_notes):
        """Test complete piano notation processing."""
        notation_data = {
            "notes": sample_notes,
            "tempo": 120,
            "key": "C"
        }
        
        processed = processor.process_notation(notation_data)
        
        # Should add grand staff
        assert "grand_staff" in processed
        assert "treble_clef" in processed["grand_staff"]
        assert "bass_clef" in processed["grand_staff"]
        assert "instrument_config" in processed
        
        # Check instrument config
        config = processed["instrument_config"]
        assert config["split_point"] == 60
        assert "treble" in config["clefs"]
        assert "bass" in config["clefs"]
    
    def test_empty_clef_handling(self, processor):
        """Test handling when one clef has no notes."""
        # Only treble notes
        treble_only = [
            {"onset": 0.0, "pitch": 72, "frequency": 523.25, "duration": 0.5},
            {"onset": 0.5, "pitch": 76, "frequency": 659.25, "duration": 0.5},
        ]
        
        treble_notes, bass_notes = processor.split_grand_staff(treble_only)
        
        assert len(treble_notes) == 2
        assert len(bass_notes) == 0


class TestDrumsProcessor:
    """Test cases for DrumsProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a drums processor instance."""
        return DrumsProcessor()
    
    @pytest.fixture
    def sample_notes(self):
        """Create sample drum hits."""
        return [
            {"onset": 0.0, "pitch": 36, "frequency": 65.41, "duration": 0.1},   # Bass drum
            {"onset": 0.5, "pitch": 38, "frequency": 77.78, "duration": 0.1},   # Snare
            {"onset": 0.25, "pitch": 42, "frequency": 87.31, "duration": 0.1},  # Hi-hat
            {"onset": 0.75, "pitch": 42, "frequency": 87.31, "duration": 0.1},  # Hi-hat
        ]
    
    def test_map_to_percussion(self, processor, sample_notes):
        """Test mapping notes to percussion elements."""
        percussion_notes = processor.map_to_percussion(sample_notes)
        
        # Should map all notes
        assert len(percussion_notes) == len(sample_notes)
        
        # Check percussion structure
        for perc_note in percussion_notes:
            assert "drum_element" in perc_note
            assert "notation" in perc_note
            assert "onset" in perc_note
            assert "duration" in perc_note
    
    def test_identify_drum_element(self, processor):
        """Test drum element identification."""
        # Test exact matches
        bass_drum = processor._identify_drum_element(36)
        assert bass_drum["name"] == "Bass Drum"
        assert bass_drum["notation"] == "bass_drum"
        
        snare = processor._identify_drum_element(38)
        assert snare["name"] == "Snare"
        assert snare["notation"] == "snare"
        
        hi_hat = processor._identify_drum_element(42)
        assert hi_hat["name"] == "Closed Hi-Hat"
        assert hi_hat["notation"] == "hi_hat_closed"
    
    def test_closest_drum_element(self, processor):
        """Test finding closest drum element for non-exact pitches."""
        # Pitch 37 should map to closest element (36 or 38)
        element = processor._identify_drum_element(37)
        assert element["name"] in ["Bass Drum", "Snare"]
    
    def test_process_notation(self, processor, sample_notes):
        """Test complete drums notation processing."""
        notation_data = {
            "notes": sample_notes,
            "tempo": 120,
            "key": "C"
        }
        
        processed = processor.process_notation(notation_data)
        
        # Should add percussion mapping
        assert "percussion" in processed
        assert "instrument_config" in processed
        
        # Check instrument config
        config = processed["instrument_config"]
        assert "drum_map" in config
        assert config["notation_type"] == "percussion_staff"
