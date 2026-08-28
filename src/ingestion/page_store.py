import boto3


class PageStore:

    def __init__(self):
        self.s3_client = boto3.client("s3")

    def save_page(
        self,
        page_bytes: bytes,
        bucket_name: str,
        document_id: str,
        page_number: int,
    ) -> str:

        object_key = (
            f"processed/pages/"
            f"{document_id}/"
            f"page-{page_number:04d}.png"
        )

        self.s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=page_bytes,
            ContentType="image/png",
        )

        return f"s3://{bucket_name}/{object_key}"
