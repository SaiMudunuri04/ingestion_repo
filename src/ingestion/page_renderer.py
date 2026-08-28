from pathlib import Path
from typing import Iterator

import fitz  # PyMuPDF


class PageRenderer:

    def __init__(self, zoom: float = 2.0):
        self.zoom = zoom

    def render_pages(
        self,
        pdf_path: Path,
    ) -> Iterator[tuple[int, bytes]]:

        document = fitz.open(str(pdf_path))

        try:
            matrix = fitz.Matrix(
                self.zoom,
                self.zoom,
            )

            for page_index in range(document.page_count):

                page = document.load_page(page_index)

                pixmap = page.get_pixmap(
                    matrix=matrix,
                    alpha=False,
                )

                page_image_bytes = pixmap.tobytes(
                    "png"
                )

                page_number = page_index + 1

                yield (
                    page_number,
                    page_image_bytes,
                )

        finally:
            document.close()
