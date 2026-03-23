"""
Instrument-specific transcription models.

This module provides specialized processing for different instrument types:
- Guitar/bass tablature generation
- Piano grand staff notation
- Drums percussion notation
- Instrument model selector and routing
"""
import numpy as np
import librosa
from typing import Dict, List, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class InstrumentType(str, Enum):
    """Supported instrument types."""
    PIANO = "piano"
    GUITAR = "guitar"
    BASS = "bass"
    VOCALS = "vocals"
    DRUMS = "drums"
    STRINGS = "strings"
    WOODWINDS = "woodwinds"
    BRASS = "brass"


class InstrumentModelRouter:
    """Routes transcription to specialized instrument models."""
    
    @staticmethod
    def get_processor(instrument_type: str):
        """
        Get the appropriate processor for an instrument type.
        
        Args:
            instrument_type: Type of instrument
            
        Returns:
            Processor instance for the instrument
        """
        instrument_type = instrument_type.lower()
        
        if instrument_type == InstrumentType.GUITAR:
            return GuitarProcessor()
        elif instrument_type == InstrumentType.BASS:
            return BassProcessor()
        elif instrument_type == InstrumentType.PIANO:
            return PianoProcessor()
        elif instrument_type == InstrumentType.DRUMS:
            return DrumsProcessor()
        else:
            # Default processor for other instruments
            return DefaultProcessor()


class DefaultProcessor:
    """Default processor for instruments without specialized handling."""
    
    def process_notation(self, notation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process notation data (no special processing).
        
        Args:
            notation_data: Base notation data
            
        Returns:
            Processed notation data
        """
        return notation_data


class GuitarProcessor:
    """Specialized processor for guitar transcription."""
    
    def __init__(self):
        """Initialize guitar processor."""
        self.num_strings = 6
        # Standard tuning: E2, A2, D3, G3, B3, E4
        self.string_tunings = [40, 45, 50, 55, 59, 64]  # MIDI note numbers
        self.max_fret = 24
    
    def process_notation(self, notation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process notation data and add tablature.
        
        Args:
            notation_data: Base notation data
            
        Returns:
            Notation data with tablature added
        """
        notes = notation_data.get("notes", [])
        
        # Generate tablature
        tablature = self.generate_tablature(notes)
        
        # Add to notation data
        notation_data["tablature"] = tablature
        notation_data["instrument_config"] = {
            "num_strings": self.num_strings,
            "tuning": self.string_tunings,
            "max_fret": self.max_fret
        }
        
        logger.info(f"Generated guitar tablature with {len(tablature)} positions")
        return notation_data
    
    def generate_tablature(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate guitar tablature from notes.
        
        Args:
            notes: List of detected notes
            
        Returns:
            List of tablature positions
        """
        tablature = []
        
        for note in notes:
            pitch = note["pitch"]
            onset = note["onset"]
            duration = note["duration"]
            
            # Find best string and fret position
            string_num, fret = self._find_best_position(pitch, tablature)
            
            if string_num is not None and fret is not None:
                tablature.append({
                    "onset": onset,
                    "duration": duration,
                    "string": string_num,
                    "fret": fret,
                    "pitch": pitch
                })
        
        return tablature
    
    def _find_best_position(
        self,
        pitch: int,
        previous_positions: List[Dict[str, Any]]
    ) -> tuple[Optional[int], Optional[int]]:
        """
        Find the best string and fret position for a pitch.
        
        Args:
            pitch: MIDI note number
            previous_positions: Previously assigned positions for context
            
        Returns:
            Tuple of (string_number, fret_number) or (None, None) if not playable
        """
        possible_positions = []
        
        # Check each string
        for string_idx, open_string_pitch in enumerate(self.string_tunings):
            fret = pitch - open_string_pitch
            
            # Check if playable on this string
            if 0 <= fret <= self.max_fret:
                # Calculate position score (prefer lower frets and middle strings)
                position_score = fret + abs(string_idx - 2) * 2
                possible_positions.append((string_idx, fret, position_score))
        
        if not possible_positions:
            return None, None
        
        # Sort by score and return best position
        possible_positions.sort(key=lambda x: x[2])
        string_num, fret, _ = possible_positions[0]
        
        return string_num, fret


class BassProcessor:
    """Specialized processor for bass guitar transcription."""
    
    def __init__(self):
        """Initialize bass processor."""
        self.num_strings = 4
        # Standard bass tuning: E1, A1, D2, G2
        self.string_tunings = [28, 33, 38, 43]  # MIDI note numbers
        self.max_fret = 24
    
    def process_notation(self, notation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process notation data and add bass tablature.
        
        Args:
            notation_data: Base notation data
            
        Returns:
            Notation data with tablature added
        """
        notes = notation_data.get("notes", [])
        
        # Generate tablature
        tablature = self.generate_tablature(notes)
        
        # Add to notation data
        notation_data["tablature"] = tablature
        notation_data["instrument_config"] = {
            "num_strings": self.num_strings,
            "tuning": self.string_tunings,
            "max_fret": self.max_fret
        }
        
        logger.info(f"Generated bass tablature with {len(tablature)} positions")
        return notation_data
    
    def generate_tablature(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate bass tablature from notes.
        
        Args:
            notes: List of detected notes
            
        Returns:
            List of tablature positions
        """
        tablature = []
        
        for note in notes:
            pitch = note["pitch"]
            onset = note["onset"]
            duration = note["duration"]
            
            # Find best string and fret position
            string_num, fret = self._find_best_position(pitch)
            
            if string_num is not None and fret is not None:
                tablature.append({
                    "onset": onset,
                    "duration": duration,
                    "string": string_num,
                    "fret": fret,
                    "pitch": pitch
                })
        
        return tablature
    
    def _find_best_position(self, pitch: int) -> tuple[Optional[int], Optional[int]]:
        """
        Find the best string and fret position for a pitch.
        
        Args:
            pitch: MIDI note number
            
        Returns:
            Tuple of (string_number, fret_number) or (None, None) if not playable
        """
        possible_positions = []
        
        # Check each string
        for string_idx, open_string_pitch in enumerate(self.string_tunings):
            fret = pitch - open_string_pitch
            
            # Check if playable on this string
            if 0 <= fret <= self.max_fret:
                # Prefer lower frets
                possible_positions.append((string_idx, fret, fret))
        
        if not possible_positions:
            return None, None
        
        # Sort by score and return best position
        possible_positions.sort(key=lambda x: x[2])
        string_num, fret, _ = possible_positions[0]
        
        return string_num, fret


class PianoProcessor:
    """Specialized processor for piano transcription."""
    
    def __init__(self):
        """Initialize piano processor."""
        # Middle C (C4) is MIDI note 60
        self.treble_bass_split = 60
    
    def process_notation(self, notation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process notation data and split into grand staff.
        
        Args:
            notation_data: Base notation data
            
        Returns:
            Notation data with treble and bass clef notes
        """
        notes = notation_data.get("notes", [])
        
        # Split notes into treble and bass clef
        treble_notes, bass_notes = self.split_grand_staff(notes)
        
        # Add to notation data
        notation_data["grand_staff"] = {
            "treble_clef": treble_notes,
            "bass_clef": bass_notes
        }
        notation_data["instrument_config"] = {
            "split_point": self.treble_bass_split,
            "clefs": ["treble", "bass"]
        }
        
        logger.info(f"Split piano notation: {len(treble_notes)} treble, {len(bass_notes)} bass")
        return notation_data
    
    def split_grand_staff(
        self,
        notes: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Split notes into treble and bass clef ranges.
        
        Args:
            notes: List of all notes
            
        Returns:
            Tuple of (treble_notes, bass_notes)
        """
        treble_notes = []
        bass_notes = []
        
        for note in notes:
            pitch = note["pitch"]
            
            # Add clef information to note
            note_with_clef = note.copy()
            
            if pitch >= self.treble_bass_split:
                note_with_clef["clef"] = "treble"
                treble_notes.append(note_with_clef)
            else:
                note_with_clef["clef"] = "bass"
                bass_notes.append(note_with_clef)
        
        return treble_notes, bass_notes


class DrumsProcessor:
    """Specialized processor for drums/percussion transcription."""
    
    def __init__(self):
        """Initialize drums processor."""
        # General MIDI drum map
        self.drum_map = {
            36: {"name": "Bass Drum", "notation": "bass_drum"},
            38: {"name": "Snare", "notation": "snare"},
            42: {"name": "Closed Hi-Hat", "notation": "hi_hat_closed"},
            46: {"name": "Open Hi-Hat", "notation": "hi_hat_open"},
            41: {"name": "Low Tom", "notation": "tom_low"},
            43: {"name": "Low-Mid Tom", "notation": "tom_low_mid"},
            45: {"name": "Mid Tom", "notation": "tom_mid"},
            47: {"name": "High-Mid Tom", "notation": "tom_high_mid"},
            48: {"name": "High Tom", "notation": "tom_high"},
            49: {"name": "Crash Cymbal", "notation": "crash"},
            51: {"name": "Ride Cymbal", "notation": "ride"},
        }
    
    def process_notation(self, notation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process notation data and map to percussion notation.
        
        Args:
            notation_data: Base notation data
            
        Returns:
            Notation data with percussion mapping
        """
        notes = notation_data.get("notes", [])
        
        # Map notes to drum elements
        percussion_notes = self.map_to_percussion(notes)
        
        # Add to notation data
        notation_data["percussion"] = percussion_notes
        notation_data["instrument_config"] = {
            "drum_map": self.drum_map,
            "notation_type": "percussion_staff"
        }
        
        logger.info(f"Mapped {len(percussion_notes)} percussion hits")
        return notation_data
    
    def map_to_percussion(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map detected notes to percussion elements.
        
        Args:
            notes: List of detected notes
            
        Returns:
            List of percussion hits with drum element identification
        """
        percussion_notes = []
        
        for note in notes:
            pitch = note["pitch"]
            
            # Find closest drum element
            drum_element = self._identify_drum_element(pitch)
            
            percussion_note = note.copy()
            percussion_note["drum_element"] = drum_element["name"]
            percussion_note["notation"] = drum_element["notation"]
            
            percussion_notes.append(percussion_note)
        
        return percussion_notes
    
    def _identify_drum_element(self, pitch: int) -> Dict[str, str]:
        """
        Identify drum element from pitch.
        
        Args:
            pitch: MIDI note number
            
        Returns:
            Dictionary with drum element information
        """
        # Check if exact match in drum map
        if pitch in self.drum_map:
            return self.drum_map[pitch]
        
        # Find closest drum element
        closest_pitch = min(self.drum_map.keys(), key=lambda x: abs(x - pitch))
        return self.drum_map[closest_pitch]
