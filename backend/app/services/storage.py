import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from app.core.config import settings


def _get_client():
    kwargs = dict(
        region_name=settings.STORAGE_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )
    if settings.STORAGE_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.STORAGE_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


def generate_presigned_upload_url(storage_key: str, content_type: str, expires_in: int = 3600) -> str:
    if not settings.AWS_ACCESS_KEY_ID:
        # 预览模式: 直接走后端的本地上传端点(同源,前端 axios PUT 能正常工作)
        return f"/api/v1/uploads/local/{storage_key}"
    client = _get_client()
    url = client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.STORAGE_BUCKET, "Key": storage_key, "ContentType": content_type},
        ExpiresIn=expires_in,
    )
    return url


def generate_presigned_download_url(storage_key: str, expires_in: int = 3600) -> str:
    client = _get_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.STORAGE_BUCKET, "Key": storage_key},
        ExpiresIn=expires_in,
    )
    return url


def get_public_url(storage_key: str) -> str:
    # 如果 storage_key 本身就是完整 URL(provider 直接返回的外部 CDN 链接),直接用
    if storage_key.startswith(("http://", "https://", "data:")):
        return storage_key
    if settings.CDN_BASE_URL:
        return f"{settings.CDN_BASE_URL.rstrip('/')}/{storage_key}"
    if not settings.AWS_ACCESS_KEY_ID:
        # Preview mode: return a deterministic placeholder image URL
        seed = abs(hash(storage_key)) % 100000
        return f"https://picsum.photos/seed/{seed}/1024/1365"
    return generate_presigned_download_url(storage_key)
