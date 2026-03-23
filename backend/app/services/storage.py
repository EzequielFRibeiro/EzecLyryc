import boto3
from botocore.exceptions import ClientError
from app.config import settings
import uuid
from typing import BinaryIO, Optional
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage in S3-compatible storage (MinIO)"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise
    
    def upload_file(
        self,
        file_data: BinaryIO,
        file_extension: str,
        content_type: str,
        user_id: Optional[int] = None
    ) -> str:
        """
        Upload a file to S3 storage with a unique key.
        
        Args:
            file_data: Binary file data
            file_extension: File extension (e.g., 'mp3', 'wav')
            content_type: MIME type of the file
            user_id: Optional user ID for organizing files
        
        Returns:
            Unique file key in storage
        
        Raises:
            ClientError: If upload fails
        """
        # Generate unique file key
        unique_id = str(uuid.uuid4())
        if user_id:
            file_key = f"uploads/user_{user_id}/{unique_id}.{file_extension}"
        else:
            file_key = f"uploads/anonymous/{unique_id}.{file_extension}"
        
        try:
            self.s3_client.upload_fileobj(
                file_data,
                self.bucket_name,
                file_key,
                ExtraArgs={'ContentType': content_type}
            )
            logger.info(f"Uploaded file: {file_key}")
            return file_key
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    def get_file(self, file_key: str) -> bytes:
        """
        Retrieve a file from S3 storage.
        
        Args:
            file_key: Unique file key in storage
        
        Returns:
            File data as bytes
        
        Raises:
            ClientError: If file not found or retrieval fails
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Failed to retrieve file {file_key}: {e}")
            raise
    
    def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from S3 storage.
        
        Args:
            file_key: Unique file key in storage
        
        Returns:
            True if deletion successful
        
        Raises:
            ClientError: If deletion fails
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            logger.info(f"Deleted file: {file_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file {file_key}: {e}")
            raise
    
    def get_file_url(self, file_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary file access.
        
        Args:
            file_key: Unique file key in storage
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {file_key}: {e}")
            raise


# Singleton instance
storage_service = StorageService()
