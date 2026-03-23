import ffmpeg
import tempfile
import os
from typing import Tuple, Optional
import logging
import yt_dlp

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Service for processing audio and video files"""
    
    @staticmethod
    def extract_audio_from_video(video_path: str, output_format: str = "mp3") -> str:
        """
        Extract audio from video file using FFmpeg.
        
        Args:
            video_path: Path to the video file
            output_format: Desired audio format (default: mp3)
        
        Returns:
            Path to the extracted audio file
        
        Raises:
            ffmpeg.Error: If extraction fails
        """
        try:
            # Create temporary file for extracted audio
            temp_audio = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f".{output_format}"
            )
            temp_audio.close()
            
            # Extract audio using ffmpeg
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, temp_audio.name, acodec='libmp3lame', audio_bitrate='192k')
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            logger.info(f"Extracted audio from video: {video_path} -> {temp_audio.name}")
            return temp_audio.name
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error extracting audio: {e.stderr.decode() if e.stderr else str(e)}")
            raise
    
    @staticmethod
    def convert_audio_format(audio_path: str, output_format: str = "mp3") -> str:
        """
        Convert audio file to a different format using FFmpeg.
        
        Args:
            audio_path: Path to the audio file
            output_format: Desired audio format (default: mp3)
        
        Returns:
            Path to the converted audio file
        
        Raises:
            ffmpeg.Error: If conversion fails
        """
        try:
            # Create temporary file for converted audio
            temp_audio = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f".{output_format}"
            )
            temp_audio.close()
            
            # Convert audio using ffmpeg
            stream = ffmpeg.input(audio_path)
            stream = ffmpeg.output(stream, temp_audio.name, acodec='libmp3lame', audio_bitrate='192k')
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            logger.info(f"Converted audio format: {audio_path} -> {temp_audio.name}")
            return temp_audio.name
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error converting audio: {e.stderr.decode() if e.stderr else str(e)}")
            raise
    
    @staticmethod
    def get_audio_duration(file_path: str) -> Optional[float]:
        """
        Get duration of audio/video file in seconds.
        
        Args:
            file_path: Path to the audio or video file
        
        Returns:
            Duration in seconds, or None if unable to determine
        """
        try:
            probe = ffmpeg.probe(file_path)
            duration = float(probe['format']['duration'])
            return duration
        except (ffmpeg.Error, KeyError, ValueError) as e:
            logger.error(f"Error getting audio duration: {e}")
            return None
    
    @staticmethod
    def get_audio_info(file_path: str) -> dict:
        """
        Get detailed information about audio/video file.
        
        Args:
            file_path: Path to the audio or video file
        
        Returns:
            Dictionary with audio information (duration, bitrate, codec, etc.)
        """
        try:
            probe = ffmpeg.probe(file_path)
            audio_info = {
                'duration': float(probe['format'].get('duration', 0)),
                'bitrate': int(probe['format'].get('bit_rate', 0)),
                'format': probe['format'].get('format_name', ''),
                'size': int(probe['format'].get('size', 0))
            }
            
            # Get audio stream info if available
            audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
            if audio_streams:
                audio_stream = audio_streams[0]
                audio_info['codec'] = audio_stream.get('codec_name', '')
                audio_info['sample_rate'] = int(audio_stream.get('sample_rate', 0))
                audio_info['channels'] = int(audio_stream.get('channels', 0))
            
            return audio_info
            
        except (ffmpeg.Error, KeyError, ValueError) as e:
            logger.error(f"Error getting audio info: {e}")
            return {}
    
    @staticmethod
    def extract_audio_from_youtube(youtube_url: str, max_duration_seconds: int = 900) -> Tuple[str, float]:
        """
        Extract audio from YouTube video using yt-dlp.
        
        Args:
            youtube_url: YouTube video URL
            max_duration_seconds: Maximum duration to extract in seconds (default: 900 = 15 minutes)
        
        Returns:
            Tuple of (audio_file_path, duration_in_seconds)
        
        Raises:
            ValueError: If URL is invalid or video is restricted
            Exception: If extraction fails
        """
        try:
            # Create temporary file for extracted audio
            temp_audio = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".mp3"
            )
            temp_audio.close()
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': temp_audio.name.replace('.mp3', ''),
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            # Extract video info first to check duration
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                try:
                    info = ydl.extract_info(youtube_url, download=False)
                    video_duration = info.get('duration', 0)
                    
                    if video_duration == 0:
                        raise ValueError("Unable to determine video duration")
                    
                    # Check if we need to limit duration
                    if video_duration > max_duration_seconds:
                        logger.info(f"Video duration {video_duration}s exceeds limit {max_duration_seconds}s, extracting first {max_duration_seconds}s")
                        # Add postprocessor args to limit duration
                        ydl_opts['postprocessor_args'] = [
                            '-t', str(max_duration_seconds)
                        ]
                        actual_duration = max_duration_seconds
                    else:
                        actual_duration = video_duration
                        
                except yt_dlp.utils.DownloadError as e:
                    logger.error(f"Failed to extract YouTube video info: {e}")
                    raise ValueError("Invalid YouTube URL or video is not accessible")
            
            # Download and extract audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([youtube_url])
                except yt_dlp.utils.DownloadError as e:
                    error_msg = str(e)
                    if 'private' in error_msg.lower() or 'unavailable' in error_msg.lower():
                        raise ValueError("Video is private, unavailable, or restricted")
                    elif 'copyright' in error_msg.lower():
                        raise ValueError("Video is restricted due to copyright")
                    else:
                        raise ValueError(f"Failed to download video: {error_msg}")
            
            # Verify the file was created
            if not os.path.exists(temp_audio.name):
                raise Exception("Audio extraction completed but file was not created")
            
            # Get actual duration of extracted audio
            extracted_duration = AudioProcessor.get_audio_duration(temp_audio.name)
            if extracted_duration is None:
                extracted_duration = actual_duration
            
            logger.info(f"Extracted audio from YouTube: {youtube_url} -> {temp_audio.name} ({extracted_duration}s)")
            return temp_audio.name, extracted_duration
            
        except ValueError:
            # Re-raise ValueError as-is (these are user-facing errors)
            raise
        except Exception as e:
            logger.error(f"Unexpected error extracting audio from YouTube: {e}")
            # Clean up temp file if it exists
            try:
                if os.path.exists(temp_audio.name):
                    os.unlink(temp_audio.name)
            except:
                pass
            raise Exception(f"Failed to extract audio from YouTube: {str(e)}")


# Singleton instance
audio_processor = AudioProcessor()
