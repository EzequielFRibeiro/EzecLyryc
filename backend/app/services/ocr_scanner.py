"""
OCR Sheet Music Scanner for optical music recognition.

This module provides:
- Image preprocessing for sheet music
- Musical notation element detection
- Conversion to editable transcription format
"""
import numpy as np
from PIL import Image
import io
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class OCRScanner:
    """Optical Music Recognition scanner for sheet music images."""
    
    def __init__(self):
        """Initialize OCR scanner."""
        self.supported_formats = ['jpg', 'jpeg', 'png', 'pdf']
        self.min_image_width = 300
        self.min_image_height = 200
    
    def validate_image(self, image_data: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image quality and format.
        
        Args:
            image_data: Raw image bytes
            filename: Original filename
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file extension
            ext = filename.lower().split('.')[-1]
            if ext not in self.supported_formats:
                return False, f"Unsupported format. Please use: {', '.join(self.supported_formats)}"
            
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Check dimensions
            width, height = image.size
            if width < self.min_image_width or height < self.min_image_height:
                return False, f"Image too small. Minimum size: {self.min_image_width}x{self.min_image_height}px"
            
            # Check if image is too dark or too bright
            if image.mode != 'L':
                image = image.convert('L')
            
            img_array = np.array(image)
            mean_brightness = np.mean(img_array)
            
            if mean_brightness < 30:
                return False, "Image too dark. Please use a brighter scan or photo."
            elif mean_brightness > 240:  # Adjusted threshold
                return False, "Image too bright or washed out. Please adjust exposure."
            
            return True, None
            
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False, f"Invalid image file: {str(e)}"
    
    def preprocess_image(self, image_data: bytes) -> np.ndarray:
        """
        Preprocess image for OCR.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Preprocessed image array
        """
        # Load image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Normalize contrast
        img_array = self._normalize_contrast(img_array)
        
        # Denoise
        img_array = self._denoise(img_array)
        
        # Binarize (convert to black and white)
        img_array = self._binarize(img_array)
        
        logger.info(f"Preprocessed image: {img_array.shape}")
        return img_array
    
    def _normalize_contrast(self, img: np.ndarray) -> np.ndarray:
        """
        Normalize image contrast using histogram equalization.
        
        Args:
            img: Grayscale image array
            
        Returns:
            Contrast-normalized image
        """
        # Simple contrast stretching
        min_val = np.min(img)
        max_val = np.max(img)
        
        if max_val > min_val:
            img_normalized = ((img - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        else:
            img_normalized = img
        
        return img_normalized
    
    def _denoise(self, img: np.ndarray) -> np.ndarray:
        """
        Remove noise from image using median filtering.
        
        Args:
            img: Grayscale image array
            
        Returns:
            Denoised image
        """
        from scipy.ndimage import median_filter
        return median_filter(img, size=3)
    
    def _binarize(self, img: np.ndarray, threshold: Optional[int] = None) -> np.ndarray:
        """
        Convert grayscale image to binary using adaptive thresholding.
        
        Args:
            img: Grayscale image array
            threshold: Optional fixed threshold (if None, uses Otsu's method)
            
        Returns:
            Binary image
        """
        if threshold is None:
            # Use Otsu's method to find optimal threshold
            threshold = self._otsu_threshold(img)
        
        binary = (img > threshold).astype(np.uint8) * 255
        return binary
    
    def _otsu_threshold(self, img: np.ndarray) -> int:
        """
        Calculate optimal threshold using Otsu's method.
        
        Args:
            img: Grayscale image array
            
        Returns:
            Optimal threshold value
        """
        # Calculate histogram
        hist, bins = np.histogram(img.flatten(), bins=256, range=(0, 256))
        hist = hist.astype(float)
        
        # Normalize histogram
        hist /= hist.sum()
        
        # Calculate cumulative sums
        cum_sum = np.cumsum(hist)
        cum_mean = np.cumsum(hist * np.arange(256))
        
        # Calculate between-class variance
        global_mean = cum_mean[-1]
        
        between_class_variance = np.zeros(256)
        for t in range(256):
            if cum_sum[t] == 0 or cum_sum[t] == 1:
                continue
            
            mean_bg = cum_mean[t] / cum_sum[t] if cum_sum[t] > 0 else 0
            mean_fg = (global_mean - cum_mean[t]) / (1 - cum_sum[t]) if cum_sum[t] < 1 else 0
            
            between_class_variance[t] = cum_sum[t] * (1 - cum_sum[t]) * (mean_bg - mean_fg) ** 2
        
        # Find threshold with maximum variance
        threshold = np.argmax(between_class_variance)
        return threshold
    
    def detect_staff_lines(self, img: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect staff lines in the image.
        
        Args:
            img: Binary image array
            
        Returns:
            List of detected staff line groups
        """
        # Horizontal projection to find staff lines
        horizontal_projection = np.sum(img == 0, axis=1)  # Count black pixels per row
        
        # Find peaks (staff lines have many black pixels)
        threshold = np.mean(horizontal_projection) + np.std(horizontal_projection)
        staff_line_rows = np.where(horizontal_projection > threshold)[0]
        
        # Group consecutive rows into staff lines
        staff_lines = []
        if len(staff_line_rows) > 0:
            current_group = [staff_line_rows[0]]
            
            for row in staff_line_rows[1:]:
                if row - current_group[-1] <= 3:  # Lines within 3 pixels are same staff line
                    current_group.append(row)
                else:
                    # Save current group
                    staff_lines.append({
                        "y_position": int(np.mean(current_group)),
                        "thickness": len(current_group)
                    })
                    current_group = [row]
            
            # Add last group
            if current_group:
                staff_lines.append({
                    "y_position": int(np.mean(current_group)),
                    "thickness": len(current_group)
                })
        
        logger.info(f"Detected {len(staff_lines)} staff lines")
        return staff_lines
    
    def detect_notation_elements(self, img: np.ndarray) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect musical notation elements (notes, rests, clefs, etc.).
        
        This is a simplified implementation. A production system would use
        a trained ML model or library like Audiveris.
        
        Args:
            img: Preprocessed binary image
            
        Returns:
            Dictionary of detected elements by type
        """
        elements = {
            "notes": [],
            "rests": [],
            "clefs": [],
            "time_signatures": [],
            "key_signatures": [],
            "barlines": []
        }
        
        # Detect staff lines first
        staff_lines = self.detect_staff_lines(img)
        
        if len(staff_lines) < 5:
            logger.warning("Insufficient staff lines detected for reliable OCR")
            return elements
        
        # Group staff lines into staves (5 lines per staff)
        staves = self._group_into_staves(staff_lines)
        
        # For each staff, detect elements
        for staff_idx, staff in enumerate(staves):
            # Detect vertical elements (barlines, stems)
            vertical_elements = self._detect_vertical_elements(img, staff)
            elements["barlines"].extend(vertical_elements.get("barlines", []))
            
            # Detect note heads (circular blobs)
            note_heads = self._detect_note_heads(img, staff)
            elements["notes"].extend(note_heads)
            
            # Detect clefs (at the beginning of staff)
            clef = self._detect_clef(img, staff)
            if clef:
                elements["clefs"].append(clef)
        
        logger.info(f"Detected elements: {len(elements['notes'])} notes, "
                   f"{len(elements['clefs'])} clefs, {len(elements['barlines'])} barlines")
        
        return elements
    
    def _group_into_staves(self, staff_lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group staff lines into staves (5 lines each).
        
        Args:
            staff_lines: List of detected staff lines
            
        Returns:
            List of staves with their line positions
        """
        staves = []
        i = 0
        
        while i + 4 < len(staff_lines):
            # Check if next 5 lines are evenly spaced (part of same staff)
            lines = staff_lines[i:i+5]
            positions = [line["y_position"] for line in lines]
            
            # Calculate spacing
            spacings = [positions[j+1] - positions[j] for j in range(4)]
            avg_spacing = np.mean(spacings)
            
            # If spacing is relatively uniform, it's a staff
            if np.std(spacings) < avg_spacing * 0.3:
                staves.append({
                    "lines": lines,
                    "top": positions[0],
                    "bottom": positions[4],
                    "spacing": avg_spacing
                })
                i += 5
            else:
                i += 1
        
        return staves
    
    def _detect_vertical_elements(
        self,
        img: np.ndarray,
        staff: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect vertical elements like barlines.
        
        Args:
            img: Binary image
            staff: Staff information
            
        Returns:
            Dictionary of detected vertical elements
        """
        elements = {"barlines": []}
        
        # Extract staff region
        top = max(0, staff["top"] - 20)
        bottom = min(img.shape[0], staff["bottom"] + 20)
        staff_region = img[top:bottom, :]
        
        # Vertical projection
        vertical_projection = np.sum(staff_region == 0, axis=0)
        
        # Find strong vertical lines (barlines)
        threshold = (bottom - top) * 0.6  # At least 60% of staff height
        barline_columns = np.where(vertical_projection > threshold)[0]
        
        # Group consecutive columns
        if len(barline_columns) > 0:
            current_group = [barline_columns[0]]
            
            for col in barline_columns[1:]:
                if col - current_group[-1] <= 2:
                    current_group.append(col)
                else:
                    elements["barlines"].append({
                        "x_position": int(np.mean(current_group)),
                        "staff_index": staff.get("index", 0)
                    })
                    current_group = [col]
            
            if current_group:
                elements["barlines"].append({
                    "x_position": int(np.mean(current_group)),
                    "staff_index": staff.get("index", 0)
                })
        
        return elements
    
    def _detect_note_heads(
        self,
        img: np.ndarray,
        staff: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect note heads (simplified blob detection).
        
        Args:
            img: Binary image
            staff: Staff information
            
        Returns:
            List of detected note heads
        """
        notes = []
        
        # This is a placeholder implementation
        # A real implementation would use connected component analysis
        # and shape matching to identify note heads
        
        # For now, return empty list with a note about implementation
        logger.info("Note head detection requires advanced image processing library")
        
        return notes
    
    def _detect_clef(self, img: np.ndarray, staff: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect clef symbol at the beginning of staff.
        
        Args:
            img: Binary image
            staff: Staff information
            
        Returns:
            Detected clef information or None
        """
        # Placeholder implementation
        # Real implementation would use template matching or ML model
        
        return {
            "type": "treble",  # Default assumption
            "x_position": 50,
            "confidence": 0.5
        }
    
    def generate_transcription(
        self,
        elements: Dict[str, List[Dict[str, Any]]],
        image_width: int,
        image_height: int
    ) -> Dict[str, Any]:
        """
        Generate editable transcription data from detected elements.
        
        Args:
            elements: Detected notation elements
            image_width: Original image width
            image_height: Original image height
            
        Returns:
            Transcription data structure
        """
        # Convert detected elements to notation data
        notes = []
        
        for note_element in elements.get("notes", []):
            notes.append({
                "pitch": note_element.get("pitch", 60),  # Default to middle C
                "duration": note_element.get("duration", 0.5),
                "onset": note_element.get("onset", 0.0)
            })
        
        transcription_data = {
            "version": "1.0",
            "source": "ocr",
            "instrument": "piano",  # Default
            "tempo": 120,  # Default
            "key": "C",  # Default
            "time_signature": {"numerator": 4, "denominator": 4},
            "notes": notes,
            "metadata": {
                "total_notes": len(notes),
                "image_dimensions": {
                    "width": image_width,
                    "height": image_height
                },
                "detected_elements": {
                    "clefs": len(elements.get("clefs", [])),
                    "barlines": len(elements.get("barlines", [])),
                    "time_signatures": len(elements.get("time_signatures", [])),
                    "key_signatures": len(elements.get("key_signatures", []))
                }
            }
        }
        
        logger.info(f"Generated transcription with {len(notes)} notes from OCR")
        return transcription_data
    
    def scan(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Complete OCR scanning pipeline.
        
        Args:
            image_data: Raw image bytes
            filename: Original filename
            
        Returns:
            Transcription data structure
        """
        # Validate image
        is_valid, error_msg = self.validate_image(image_data, filename)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Preprocess image
        img = self.preprocess_image(image_data)
        
        # Detect notation elements
        elements = self.detect_notation_elements(img)
        
        # Generate transcription
        transcription = self.generate_transcription(
            elements,
            img.shape[1],
            img.shape[0]
        )
        
        return transcription
