import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any
from app.config import settings

def generate_presigned_post(s3_key: str, file_type: str) -> Dict[str, Any]:
    """
    Generate a presigned S3 POST URL to upload a file directly.
    If AWS credentials are not configured, returns mock URL details for local development.
    """
    # Check if AWS credentials are configured
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            response = s3_client.generate_presigned_post(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key,
                Fields={"Content-Type": file_type},
                Conditions=[
                    {"Content-Type": file_type},
                    ["content-length-range", 1, 10485760] # max 10MB
                ],
                ExpiresIn=3600
            )
            return {
                "upload_url": response["url"],
                "fields": response["fields"],
                "is_mock": False
            }
        except ClientError as e:
            # Fall back to mock if client initialization fails
            pass

    # Mock S3 presigned URL configuration for local testing
    mock_url = f"/api/v1/uploads/mock-s3-upload"
    return {
        "upload_url": mock_url,
        "fields": {
            "key": s3_key,
            "Content-Type": file_type
        },
        "is_mock": True
    }

def store_uploaded_file(file_obj, s3_key: str):
    """
    Stores an uploaded file directly from the backend to either S3 or local mock storage.
    """
    import os
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        file_obj.file.seek(0)
        s3_client.upload_fileobj(
            file_obj.file,
            settings.AWS_S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": file_obj.content_type}
        )
        return
            
    # Mock storage fallback
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
    dest_path = os.path.join(base_dir, s3_key)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    file_obj.file.seek(0)
    with open(dest_path, "wb") as f:
        f.write(file_obj.file.read())

def move_s3_object(bucket: str, old_key: str, new_key: str):
    """
    Moves an S3 object from old_key to new_key, working for both AWS S3 and local mock.
    """
    import os
    import shutil
    import logging
    logger = logging.getLogger(__name__)

    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            # Copy to new destination
            copy_source = {'Bucket': bucket, 'Key': old_key}
            s3_client.copy_object(CopySource=copy_source, Bucket=bucket, Key=new_key)
            # Delete old object
            s3_client.delete_object(Bucket=bucket, Key=old_key)
            logger.info(f"S3 object moved from {old_key} to {new_key}")
            return
        except Exception as e:
            logger.error(f"Failed to move S3 object: {e}")
            raise e

    # Mock storage fallback
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
    old_path = os.path.join(base_dir, old_key)
    new_path = os.path.join(base_dir, new_key)

    if os.path.exists(old_path):
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.move(old_path, new_path)
        logger.info(f"Local mock file moved from {old_key} to {new_key}")
        
        # Cleanup old directory if it's empty
        old_dir = os.path.dirname(old_path)
        try:
            if not os.listdir(old_dir):
                os.rmdir(old_dir)
        except OSError:
            pass
    else:
        logger.warning(f"Mock file not found for moving: {old_path}")
        raise FileNotFoundError(f"Source file {old_path} not found")
