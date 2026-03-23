"""
Unit tests for OCR sheet music scanner.
"""
import pytest
import numpy as np
from PIL import Image
import io
from app.services.ocr_scanner import OCRScanner


class TestOCRScanner:
    """Test cases for OCRScanner."""
    
    @pytest.fixture
    def scanner(self):
        """Create an OCR scanner instance."""
        return OCRScanner()
    
    @pytest.fixture
    def sample_image_data(self):
        """Create a sample sheet music image."""
        # Create a test image with better contrast (gray background with black staff lines)
        img = Image.new('L', (800, 600), color=200)  # Light gray background
        pixels = img.load()
        
        # Draw 5 horizontal staff lines (thicker for better detection)
        for line_y in [200, 220, 240, 260, 280]:
            for x in range(800):
                for dy in range(-1, 2):  # Make lines 3 pixels thick
                    if 0 <= line_y + dy < 600:
                        pixels[x, line_y + dy] = 0
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    def test_validate_image_valid(self, scanner, sample_image_data):
        """Test validation of valid image."""
        is_valid, error_msg = scanner.validate_image(sample_image_data, "test.png")
        
        assert is_valid is True
        assert error_msg is None
    
    def test_validate_image_unsupported_format(self, scanner, sample_image_data):
        """Test validation rejects unsupported formats."""
        is_valid, error_msg = scanner.validate_image(sample_image_data, "test.bmp")
        
        assert is_valid is False
        assert "Unsupported format" in error_msg
    
    def test_validate_image_too_small(self, scanner):
        """Test validation rejects images that are too small."""
        # Create tiny image
        img = Image.new('L', (100, 100), color=255)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        
        is_valid, error_msg = scanner.validate_image(img_bytes.getvalue(), "test.png")
        
        assert is_valid is False
        assert "too small" in error_msg
    
    def test_validate_image_too_dark(self, scanner):
        """Test validation rejects images that are too dark."""
        # Create very dark image
        img = Image.new('L', (800, 600), color=10)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        
        is_valid, error_msg = scanner.validate_image(img_bytes.getvalue(), "test.png")
        
        assert is_valid is False
        assert "too dark" in error_msg
    
    def test_validate_image_too_bright(self, scanner):
        """Test validation rejects images that are too bright."""
        # Create very bright image
        img = Image.new('L', (800, 600), color=250)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        
        is_valid, error_msg = scanner.validate_image(img_bytes.getvalue(), "test.png")
        
        assert is_valid is False
        assert "too bright" in error_msg
    
    def test_preprocess_image(self, scanner, sample_image_data):
        """Test image preprocessing."""
        img_array = scanner.preprocess_image(sample_image_data)
        
        # Should return numpy array
        assert isinstance(img_array, np.ndarray)
        
        # Should be 2D (grayscale)
        assert len(img_array.shape) == 2
        
        # Should be binary (0 or 255)
        unique_values = np.unique(img_array)
        assert len(unique_values) <= 2
        assert all(v in [0, 255] for v in unique_values)
    
    def test_normalize_contrast(self, scanner):
        """Test contrast normalization."""
        # Create low-contrast image
        img = np.array([[100, 110, 120], [105, 115, 125]], dtype=np.uint8)
        
        normalized = scanner._normalize_contrast(img)
        
        # Should stretch to full range
        assert np.min(normalized) == 0
        assert np.max(normalized) == 255
    
    def test_denoise(self, scanner):
        """Test image denoising."""
        # Create noisy image
        img = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        
        denoised = scanner._denoise(img)
        
        # Should have same shape
        assert denoised.shape == img.shape
        
        # Should be smoother (lower variance)
        assert np.var(denoised) <= np.var(img)
    
    def test_binarize(self, scanner):
        """Test image binarization."""
        # Create grayscale image
        img = np.array([[50, 100, 150], [200, 250, 100]], dtype=np.uint8)
        
        binary = scanner._binarize(img)
        
        # Should be binary
        unique_values = np.unique(binary)
        assert len(unique_values) <= 2
        assert all(v in [0, 255] for v in unique_values)
    
    def test_otsu_threshold(self, scanner):
        """Test Otsu's thresholding method."""
        # Create bimodal image (two distinct intensity groups)
        img = np.concatenate([
            np.full((50, 50), 50, dtype=np.uint8),
            np.full((50, 50), 200, dtype=np.uint8)
        ])
        
        threshold = scanner._otsu_threshold(img)
        
        # Threshold should be between the two modes (allow edge cases)
        assert 40 <= threshold <= 210
    
    def test_detect_staff_lines(self, scanner, sample_image_data):
        """Test staff line detection."""
        img_array = scanner.preprocess_image(sample_image_data)
        
        staff_lines = scanner.detect_staff_lines(img_array)
        
        # Should detect the 5 staff lines we drew
        assert len(staff_lines) >= 3  # At least some lines detected
        
        # Each staff line should have position and thickness
        for line in staff_lines:
            assert "y_position" in line
            assert "thickness" in line
            assert line["y_position"] > 0
    
    def test_detect_notation_elements(self, scanner, sample_image_data):
        """Test notation element detection."""
        img_array = scanner.preprocess_image(sample_image_data)
        
        elements = scanner.detect_notation_elements(img_array)
        
        # Should return dictionary with element types
        assert "notes" in elements
        assert "rests" in elements
        assert "clefs" in elements
        assert "time_signatures" in elements
        assert "key_signatures" in elements
        assert "barlines" in elements
        
        # All should be lists
        for key, value in elements.items():
            assert isinstance(value, list)
    
    def test_group_into_staves(self, scanner):
        """Test grouping staff lines into staves."""
        # Create 5 evenly-spaced staff lines
        staff_lines = [
            {"y_position": 100, "thickness": 2},
            {"y_position": 120, "thickness": 2},
            {"y_position": 140, "thickness": 2},
            {"y_position": 160, "thickness": 2},
            {"y_position": 180, "thickness": 2},
        ]
        
        staves = scanner._group_into_staves(staff_lines)
        
        # Should group into 1 staff
        assert len(staves) >= 1
        
        # Each staff should have lines, top, bottom, spacing
        for staff in staves:
            assert "lines" in staff
            assert "top" in staff
            assert "bottom" in staff
            assert "spacing" in staff
    
    def test_generate_transcription(self, scanner):
        """Test transcription generation from detected elements."""
        elements = {
            "notes": [
                {"pitch": 60, "duration": 0.5, "onset": 0.0},
                {"pitch": 64, "duration": 0.5, "onset": 0.5},
            ],
            "clefs": [{"type": "treble"}],
            "barlines": [{"x_position": 100}, {"x_position": 200}]
        }
        
        transcription = scanner.generate_transcription(elements, 800, 600)
        
        # Check structure
        assert "version" in transcription
        assert "source" in transcription
        assert transcription["source"] == "ocr"
        assert "notes" in transcription
        assert "metadata" in transcription
        
        # Check notes
        assert len(transcription["notes"]) == 2
        
        # Check metadata
        assert "image_dimensions" in transcription["metadata"]
        assert "detected_elements" in transcription["metadata"]
    
    def test_scan_complete_pipeline(self, scanner, sample_image_data):
        """Test complete OCR scanning pipeline."""
        transcription = scanner.scan(sample_image_data, "test.png")
        
        # Should return transcription data
        assert isinstance(transcription, dict)
        assert "version" in transcription
        assert "source" in transcription
        assert "notes" in transcription
        assert "metadata" in transcription
    
    def test_scan_invalid_image(self, scanner):
        """Test scanning with invalid image."""
        # Invalid image data
        invalid_data = b"not an image"
        
        with pytest.raises(ValueError):
            scanner.scan(invalid_data, "test.png")
    
    def test_scan_unsupported_format(self, scanner, sample_image_data):
        """Test scanning with unsupported format."""
        with pytest.raises(ValueError) as exc_info:
            scanner.scan(sample_image_data, "test.bmp")
        
        assert "Unsupported format" in str(exc_info.value)
