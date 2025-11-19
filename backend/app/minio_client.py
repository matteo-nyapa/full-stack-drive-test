import io
import os

from fastapi import HTTPException, UploadFile
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "files")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,  # estamos en local
)


def ensure_bucket():
    """Create the bucket if it doesn't exist."""
    found = minio_client.bucket_exists(MINIO_BUCKET_NAME)
    if not found:
        minio_client.make_bucket(MINIO_BUCKET_NAME)


async def upload_to_minio(file: UploadFile, object_name: str) -> None:
    """Upload a file to MinIO."""
    ensure_bucket()
    data = await file.read()
    file_size = len(data)

    minio_client.put_object(
        MINIO_BUCKET_NAME,
        object_name,
        io.BytesIO(data),
        length=file_size,
        content_type=file.content_type,
    )


def download_from_minio(object_name: str):
    """Obtiene un archivo de MinIO."""
    ensure_bucket()
    try:
        return minio_client.get_object(MINIO_BUCKET_NAME, object_name)
    except S3Error:
        raise HTTPException(status_code=404, detail="File content not found")


def delete_from_minio(object_name: str) -> None:
    """Elimina un archivo del bucket."""
    ensure_bucket()
    try:
        minio_client.remove_object(MINIO_BUCKET_NAME, object_name)
    except S3Error:
        pass
