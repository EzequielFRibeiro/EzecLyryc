"""
Unit tests for export service.

Tests export format generation, validation, and copyright metadata.
"""

import pytest
import json
from app.services.export_service import export_service, ExportFormat


class TestExportFormatValidation:
    """Test export format validation"""
    
    def test_validate_pdf_format_free_user(self):
        """Free users can export PDF"""
        is_valid, error = export_service.validate_format("pdf", "free")
        assert is_valid is True
        assert error is None
    
    def test_validate_pdf_format_pro_user(self):
        """Pro users can export PDF"""
        is_valid, error = export_service.validate_format("pdf", "pro")
        assert is_valid is True
        assert error is None
    
    def test_validate_musicxml_format_free_user(self):
        """Free users cannot export MusicXML"""
        is_valid, error = export_service.validate_format("musicxml", "free")
        assert is_valid is False
        assert "Pro users" in error
    
    def test_validate_musicxml_format_pro_user(self):
        """Pro users can export MusicXML"""
        is_valid, error = export_service.validate_format("musicxml", "pro")
        assert is_valid is True
        assert error is None
    
    def test_validate_midi_format_free_user(self):
        """Free users cannot export MIDI"""
        is_valid, error = export_service.validate_format("midi", "free")
        assert is_valid is False
        assert "Pro users" in error
    
    def test_validate_midi_format_pro_user(self):
        """Pro users can export MIDI"""
        is_valid, error = export_service.validate_format("midi", "pro")
        assert is_valid is True
        assert error is None
    
    def test_validate_gpx_format_free_user(self):
        """Free users cannot export GPX"""
        is_valid, error = export_service.validate_format("gpx", "free")
        assert is_valid is False
        assert "Pro users" in error
    
    def test_validate_gpx_format_pro_user(self):
        """Pro users can export GPX"""
        is_valid, error = export_service.validate_format("gpx", "pro")
        assert is_valid is True
        assert error is None
    
    def test_validate_gp5_format_free_user(self):
        """Free users cannot export GP5"""
        is_valid, error = export_service.validate_format("gp5", "free")
        assert is_valid is False
        assert "Pro users" in error
    
    def test_validate_gp5_format_pro_user(self):
        """Pro users can export GP5"""
        is_valid, error = export_service.validate_format("gp5", "pro")
        assert is_valid is True
        assert error is None
    
    def test_validate_invalid_format(self):
        """Invalid format returns error"""
        is_valid, error = export_service.validate_format("invalid", "pro")
        assert is_valid is False
        assert "Invalid format" in error


class TestPDFExport:
    """Test PDF export generation"""
    
    def test_export_pdf_generates_bytes(self):
        """PDF export returns bytes"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        result = export_service.export_to_pdf(notation_data, "Test Song")
        
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_export_pdf_contains_copyright(self):
        """PDF contains copyright metadata"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        result = export_service.export_to_pdf(notation_data, "Test Song")
        
        # Check for copyright text in PDF
        pdf_text = result.decode('latin-1', errors='ignore')
        assert "© 2024 Ezequiel Ribeiro" in pdf_text
    
    def test_export_pdf_contains_title(self):
        """PDF contains title"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        title = "My Test Song"
        result = export_service.export_to_pdf(notation_data, title)
        
        pdf_text = result.decode('latin-1', errors='ignore')
        assert title in pdf_text
    
    def test_export_pdf_valid_structure(self):
        """PDF has valid structure"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        result = export_service.export_to_pdf(notation_data, "Test Song")
        
        # Check PDF header
        assert result.startswith(b'%PDF-1.4')
        # Check PDF EOF marker
        assert b'%%EOF' in result


class TestMusicXMLExport:
    """Test MusicXML export generation"""
    
    def test_export_musicxml_generates_bytes(self):
        """MusicXML export returns bytes"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        result = export_service.export_to_musicxml(notation_data, "Test Song")
        
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_export_musicxml_valid_xml(self):
        """MusicXML is valid XML"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        result = export_service.export_to_musicxml(notation_data, "Test Song")
        
        xml_text = result.decode('utf-8')
        assert xml_text.startswith('<?xml version="1.0"')
        assert '<score-partwise' in xml_text
        assert '</score-partwise>' in xml_text
    
    def test_export_musicxml_contains_title(self):
        """MusicXML contains title"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        title = "My Test Song"
        result = export_service.export_to_musicxml(notation_data, title)
        
        xml_text = result.decode('utf-8')
        assert f'<work-title>{title}</work-title>' in xml_text
    
    def test_export_musicxml_contains_copyright(self):
        """MusicXML contains copyright"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        result = export_service.export_to_musicxml(notation_data, "Test Song")
        
        xml_text = result.decode('utf-8')
        assert "© 2024 Ezequiel Ribeiro" in xml_text


class TestMIDIExport:
    """Test MIDI export generation"""
    
    def test_export_midi_generates_bytes(self):
        """MIDI export returns bytes"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        result = export_service.export_to_midi(notation_data, "Test Song")
        
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_export_midi_valid_header(self):
        """MIDI has valid header"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        result = export_service.export_to_midi(notation_data, "Test Song")
        
        # Check MIDI header chunk
        assert result.startswith(b'MThd')
        # Check for track chunk
        assert b'MTrk' in result


class TestGuitarProExport:
    """Test Guitar Pro export generation"""
    
    def test_export_gpx_generates_bytes(self):
        """GPX export returns bytes"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        result = export_service.export_to_gpx(notation_data, "Test Song")
        
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_export_gp5_generates_bytes(self):
        """GP5 export returns bytes"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        result = export_service.export_to_gp5(notation_data, "Test Song")
        
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestExportService:
    """Test export service main methods"""
    
    def test_export_dispatches_to_correct_handler(self):
        """Export method dispatches to correct format handler"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        
        # Test each format
        pdf_result = export_service.export("pdf", notation_data, "Test")
        assert pdf_result.startswith(b'%PDF')
        
        musicxml_result = export_service.export("musicxml", notation_data, "Test")
        assert b'<?xml' in musicxml_result
        
        midi_result = export_service.export("midi", notation_data, "Test")
        assert midi_result.startswith(b'MThd')
    
    def test_export_invalid_format_raises_error(self):
        """Export with invalid format raises ValueError"""
        notation_data = {"notes": [{"pitch": "C4", "duration": 1.0}]}
        
        with pytest.raises(ValueError, match="Unsupported format"):
            export_service.export("invalid", notation_data, "Test")
    
    def test_get_content_type(self):
        """Get correct content type for each format"""
        assert export_service.get_content_type("pdf") == "application/pdf"
        assert export_service.get_content_type("musicxml") == "application/vnd.recordare.musicxml+xml"
        assert export_service.get_content_type("midi") == "audio/midi"
        assert export_service.get_content_type("gpx") == "application/x-guitar-pro"
        assert export_service.get_content_type("gp5") == "application/x-guitar-pro"
    
    def test_get_file_extension(self):
        """Get correct file extension for each format"""
        assert export_service.get_file_extension("pdf") == "pdf"
        assert export_service.get_file_extension("musicxml") == "musicxml"
        assert export_service.get_file_extension("midi") == "mid"
        assert export_service.get_file_extension("gpx") == "gpx"
        assert export_service.get_file_extension("gp5") == "gp5"


class TestExportFormatClass:
    """Test ExportFormat class"""
    
    def test_all_formats(self):
        """All formats list is correct"""
        formats = ExportFormat.all_formats()
        assert "pdf" in formats
        assert "musicxml" in formats
        assert "midi" in formats
        assert "gpx" in formats
        assert "gp5" in formats
        assert len(formats) == 5
    
    def test_free_tier_formats(self):
        """Free tier formats list is correct"""
        formats = ExportFormat.free_tier_formats()
        assert formats == ["pdf"]
    
    def test_pro_only_formats(self):
        """Pro only formats list is correct"""
        formats = ExportFormat.pro_only_formats()
        assert "musicxml" in formats
        assert "midi" in formats
        assert "gpx" in formats
        assert "gp5" in formats
        assert "pdf" not in formats
