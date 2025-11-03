"""MinIO/S3 client utilities"""

from minio import Minio
from minio.error import S3Error
from app.config import settings
import io
from typing import Optional


class S3Client:
    """MinIO/S3 client wrapper"""

    def __init__(self):
        """Initialize MinIO client"""
        # Remove http:// or https:// from endpoint
        endpoint = settings.S3_ENDPOINT.replace("http://", "").replace("https://", "")
        secure = settings.S3_ENDPOINT.startswith("https://")

        self.client = Minio(
            endpoint,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=secure
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        """Create buckets if they don't exist"""
        buckets = [
            settings.S3_BUCKET_RAW,
            settings.S3_BUCKET_CLEAN,
            settings.S3_BUCKET_ATTACHMENTS
        ]

        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    print(f"✅ Created bucket: {bucket}")
            except S3Error as e:
                print(f"❌ Error ensuring bucket {bucket}: {e}")

    def upload_text(self, content: str, bucket: str, object_name: str) -> bool:
        """
        Upload text content to S3

        Args:
            content: Text content to upload
            bucket: Bucket name
            object_name: Object key/path

        Returns:
            True if successful, False otherwise
        """
        try:
            data = content.encode('utf-8')
            data_stream = io.BytesIO(data)

            self.client.put_object(
                bucket,
                object_name,
                data_stream,
                length=len(data),
                content_type='text/plain; charset=utf-8'
            )
            return True
        except S3Error as e:
            print(f"❌ Error uploading to S3: {e}")
            return False

    def upload_file(self, file_path: str, bucket: str, object_name: str) -> bool:
        """
        Upload file to S3

        Args:
            file_path: Local file path
            bucket: Bucket name
            object_name: Object key/path

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.fput_object(bucket, object_name, file_path)
            return True
        except S3Error as e:
            print(f"❌ Error uploading file to S3: {e}")
            return False

    def get_presigned_url(self, bucket: str, object_name: str, expires: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for object

        Args:
            bucket: Bucket name
            object_name: Object key/path
            expires: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL or None if error
        """
        try:
            url = self.client.presigned_get_object(bucket, object_name, expires=expires)
            return url
        except S3Error as e:
            print(f"❌ Error generating presigned URL: {e}")
            return None

    def download_text(self, bucket: str, object_name: str) -> Optional[str]:
        """
        Download text content from S3

        Args:
            bucket: Bucket name
            object_name: Object key/path

        Returns:
            Text content or None if error
        """
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            return data.decode('utf-8')
        except S3Error as e:
            print(f"❌ Error downloading from S3: {e}")
            return None
        finally:
            response.close()
            response.release_conn()


# Singleton instance
_s3_client = None


def get_s3_client() -> S3Client:
    """Get S3 client singleton instance"""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client
