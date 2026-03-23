from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # S3-Compatible Storage
    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    FROM_EMAIL: str
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str
    FRONTEND_URL: str = "http://localhost:5173"
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_AUDIO_FORMATS: str
    ALLOWED_VIDEO_FORMATS: str
    
    # Transcription Limits
    FREE_TIER_MAX_DURATION_SECONDS: int = 30
    FREE_TIER_MAX_TRANSCRIPTIONS_PER_DAY: int = 3
    PRO_TIER_MAX_DURATION_SECONDS: int = 900
    YOUTUBE_MAX_DURATION_SECONDS: int = 900
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_audio_formats_list(self) -> List[str]:
        return [fmt.strip() for fmt in self.ALLOWED_AUDIO_FORMATS.split(",")]
    
    @property
    def allowed_video_formats_list(self) -> List[str]:
        return [fmt.strip() for fmt in self.ALLOWED_VIDEO_FORMATS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
