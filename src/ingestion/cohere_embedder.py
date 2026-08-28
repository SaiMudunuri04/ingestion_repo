import os
import json
import base64

import boto3


class CohereEmbedder:

    def __init__(self):

        self.region = os.getenv(
            "AWS_REGION",
            "us-east-1",
        )

        self.model_id = os.getenv(
            "COHERE_EMBED_MODEL_ID",
            "cohere.embed-v4:0",
        )

        self.output_dimension = int(
            os.getenv(
                "COHERE_EMBED_DIMENSION",
                "1536",
            )
        )

        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
        )

    def embed_page(
        self,
        page_bytes: bytes,
    ) -> list[float]:

        image_base64 = base64.b64encode(
            page_bytes
        ).decode("utf-8")

        image_data_uri = (
            f"data:image/png;base64,{image_base64}"
        )

        request_body = {
            "input_type": "search_document",

            "images": [
                image_data_uri
            ],

            "embedding_types": [
                "float"
            ],

            "output_dimension": self.output_dimension,
        }

        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(
            response["body"].read()
        )

        embedding = response_body[
            "embeddings"
        ][0]

        return embedding
