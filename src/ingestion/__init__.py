"""Document-ingestion components.

The package exposes its primary classes here so callers can import them
directly from ``ingestion`` instead of knowing each module's location.
"""

from .cohere_embedder import CohereEmbedder
from .opensearch_writer import OpenSearchWriter
from .page_renderer import PageRenderer
from .page_store import PageStore
from .s3_source import S3Source

__all__ = [
    "CohereEmbedder",
    "OpenSearchWriter",
    "PageRenderer",
    "PageStore",
    "S3Source",
]
