import os

import boto3

from opensearchpy import (
    OpenSearch,
    RequestsHttpConnection,
    AWSV4SignerAuth,
)


class OpenSearchWriter:

    def __init__(self):

        self.region = os.getenv(
            "AWS_REGION",
            "us-east-1",
        )

        self.host = os.environ[
            "OPENSEARCH_HOST"
        ]

        self.index_name = os.getenv(
            "OPENSEARCH_INDEX_NAME",
            "rag-pages-v1",
        )

        self.embedding_dimension = int(
            os.getenv(
                "COHERE_EMBED_DIMENSION",
                "1536",
            )
        )

        # Use "es" for Amazon OpenSearch Service.
        # Use "aoss" for OpenSearch Serverless.
        self.service = os.getenv(
            "OPENSEARCH_SERVICE",
            "es",
        )

        credentials = (
            boto3.Session()
            .get_credentials()
        )

        auth = AWSV4SignerAuth(
            credentials,
            self.region,
            self.service,
        )

        self.client = OpenSearch(
            hosts=[
                {
                    "host": self.host,
                    "port": 443,
                }
            ],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_maxsize=20,
        )

    def create_index_if_needed(self):

        if self.client.indices.exists(
            index=self.index_name
        ):
            return

        index_body = {
            "settings": {
                "index": {
                    "knn": True
                }
            },

            "mappings": {
                "properties": {

                    "document_id": {
                        "type": "keyword"
                    },

                    "page_number": {
                        "type": "integer"
                    },

                    "source_pdf_uri": {
                        "type": "keyword"
                    },

                    "page_image_uri": {
                        "type": "keyword"
                    },

                    "embedding_model": {
                        "type": "keyword"
                    },

                    "embedding_dimension": {
                        "type": "integer"
                    },

                    "embedding": {
                        "type": "knn_vector",
                        "dimension":
                            self.embedding_dimension,

                        "method": {
                            "name": "hnsw",
                            "engine": "faiss",
                            "space_type":
                                "cosinesimil",
                        },
                    },
                }
            },
        }

        self.client.indices.create(
            index=self.index_name,
            body=index_body,
        )

    def index_page(
        self,
        document_id: str,
        page_number: int,
        source_pdf_uri: str,
        page_image_uri: str,
        embedding: list[float],
        embedding_model: str,
    ):

        page_record = {
            "document_id":
                document_id,

            "page_number":
                page_number,

            "source_pdf_uri":
                source_pdf_uri,

            "page_image_uri":
                page_image_uri,

            "embedding_model":
                embedding_model,

            "embedding_dimension":
                len(embedding),

            "embedding":
                embedding,
        }

        page_id = (
            f"{document_id}"
            f"-page-{page_number:04d}"
        )

        response = self.client.index(
            index=self.index_name,
            id=page_id,
            body=page_record,
            refresh=False,
        )

        return response
