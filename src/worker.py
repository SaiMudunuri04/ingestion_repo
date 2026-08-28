import json
import os
import shutil
from hashlib import sha256
from uuid import uuid4

import boto3

from ingestion import (
    CohereEmbedder,
    OpenSearchWriter,
    PageRenderer,
    PageStore,
    S3Source,
)


class IngestionWorker:

    def __init__(self):

        self.queue_url = os.environ["INGESTION_QUEUE_URL"]

        self.processed_bucket = os.environ[
            "PROCESSED_BUCKET_NAME"
        ]

        self.sqs_client = boto3.client("sqs")

        self.s3_source = S3Source()
        self.page_renderer = PageRenderer()
        self.page_store = PageStore()
        self.embedder = CohereEmbedder()
        self.opensearch_writer = OpenSearchWriter()

    def run(self):

        self.opensearch_writer.create_index_if_needed()

        while True:

            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
            )

            messages = response.get("Messages", [])

            if not messages:
                continue

            message = messages[0]

            receipt_handle = message["ReceiptHandle"]

            try:
                self.process_message(
                    message_body=message["Body"]
                )

                # Delete only after the complete document succeeds
                self.sqs_client.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle,
                )

            except Exception as error:

                print(
                    f"Ingestion failed: {error}"
                )

                # Do NOT delete the message.
                # SQS can make it visible again for retry.

    def process_message(
        self,
        message_body: str,
    ):

        event = json.loads(message_body)

        bucket_name = (
            event["detail"]["bucket"]["name"]
        )

        object_key = (
            event["detail"]["object"]["key"]
        )

        object_etag = (
            event["detail"]["object"]
            .get("etag", "")
        )

        job_id = str(uuid4())

        document_id = self.create_document_id(
            bucket_name=bucket_name,
            object_key=object_key,
            object_etag=object_etag,
        )

        source_pdf_uri = (
            f"s3://{bucket_name}/{object_key}"
        )

        pdf_path = None

        try:

            # STEP 1
            # Download original PDF to temporary scratch storage
            pdf_path = self.s3_source.download_document(
                bucket_name=bucket_name,
                object_key=object_key,
                job_id=job_id,
            )

            # STEP 2
            # Render one page at a time
            for (
                page_number,
                page_bytes,
            ) in self.page_renderer.render_pages(
                pdf_path
            ):

                # STEP 3
                # Persist rendered page in S3
                page_image_uri = (
                    self.page_store.save_page(
                        page_bytes=page_bytes,
                        bucket_name=self.processed_bucket,
                        document_id=document_id,
                        page_number=page_number,
                    )
                )

                # STEP 4
                # Generate Cohere multimodal embedding
                embedding = (
                    self.embedder.embed_page(
                        page_bytes=page_bytes
                    )
                )

                # STEP 5
                # Store vector + associated page metadata
                self.opensearch_writer.index_page(
                    document_id=document_id,
                    page_number=page_number,
                    source_pdf_uri=source_pdf_uri,
                    page_image_uri=page_image_uri,
                    embedding=embedding,
                    embedding_model=self.embedder.model_id,
                )

        finally:

            # STEP 6
            # Always remove temporary job workspace
            if pdf_path is not None:

                job_directory = pdf_path.parent

                shutil.rmtree(
                    job_directory,
                    ignore_errors=True,
                )

    @staticmethod
    def create_document_id(
        bucket_name: str,
        object_key: str,
        object_etag: str,
    ) -> str:

        value = (
            f"{bucket_name}:"
            f"{object_key}:"
            f"{object_etag}"
        )

        return sha256(
            value.encode("utf-8")
        ).hexdigest()


if __name__ == "__main__":

    worker = IngestionWorker()

    worker.run()
