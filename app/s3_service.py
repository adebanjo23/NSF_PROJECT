import boto3
from botocore.exceptions import ClientError
from typing import Optional
from app.config import settings


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        self.bucket_name = settings.s3_bucket_name

    def upload_file(self, file_obj, object_key: str) -> bool:
        try:
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, object_key)
            return True
        except ClientError:
            return False

    def download_file(self, object_key: str) -> Optional[bytes]:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=object_key)
            return response['Body'].read()
        except ClientError:
            return None

    def delete_file(self, object_key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False

    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> Optional[str]:
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return response
        except ClientError:
            return None


s3_service = S3Service()