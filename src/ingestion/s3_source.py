from pathlib import Path

import boto3


class S3Source:

    def __init__(
        self,
        workspace_root: str = "/tmp/ingestion",
    ):
        self.s3_client = boto3.client("s3")
        self.workspace_root = Path(workspace_root)

    def download_document(
        self,
        bucket_name: str,
        object_key: str,
        job_id: str,
    ) -> Path:

        job_directory = self.workspace_root / job_id

        job_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = Path(object_key).name

        local_file_path = (
            job_directory / filename
        )

        self.s3_client.download_file(
            Bucket=bucket_name,
            Key=object_key,
            Filename=str(local_file_path),
        )

        return local_file_path
