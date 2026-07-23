from io import BytesIO

from minio import Minio

from knowledge_isle_api.core.config import settings


class PrivateObjectStorage:
    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(settings.minio_bucket):
            self.client.make_bucket(settings.minio_bucket)

    def put(self, object_key: str, content: bytes, content_type: str) -> None:
        self.ensure_bucket()
        self.client.put_object(
            settings.minio_bucket,
            object_key,
            BytesIO(content),
            length=len(content),
            content_type=content_type,
        )

    def get(self, object_key: str) -> bytes:
        response = self.client.get_object(settings.minio_bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


storage = PrivateObjectStorage()
