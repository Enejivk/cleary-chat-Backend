import boto3
from uuid import uuid4
from app.setting import current_config


AWS_REGION = current_config.AWS_REGION
S3_BUCKET_NAME = current_config.S3_BUCKET_NAME

s3 = boto3.client("s3", region_name=AWS_REGION)

def upload_file_to_s3(file_obj, filename: str, content_type: str, user_id: str) -> str:
    unique_filename = f"{user_id}/{uuid4()}_{filename}"

    s3.upload_fileobj(
        Fileobj=file_obj,
        Bucket=S3_BUCKET_NAME,
        Key=unique_filename,
        ExtraArgs={
            "ContentType": content_type,
            "ACL": "public-read"
        }
    )

    file_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
    return file_url

def delete_file_from_s3(file_url: str) -> None:
    key = file_url.split(f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/")[-1]
    try:
        s3.delete_object(Bucket=S3_BUCKET_NAME, Key=key)
    except Exception as e:
        print(f"Error deleting file from S3: {e}")
        raise e

def delete_user_files_from_s3(user_id: str) -> None:
    paginator = s3.get_paginator('list_objects_v2')
    response_iterator = paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=f"{user_id}/")

    for response in response_iterator:
        if 'Contents' in response:
            for obj in response['Contents']:
                s3.delete_object(Bucket=S3_BUCKET_NAME, Key=obj['Key'])