from docarray import BaseDoc, DocArray
from docarray.documents import ImageDoc, TextDoc
from docarray.typing import AnyUrl


class ImageChunk(ImageDoc):
    ocr_caption: str = ''
    tags: dict = {}


class TextChunk(TextDoc):
    tags: dict = {}


class PDFDocument(BaseDoc):
    texts: DocArray[TextChunk] = DocArray()
    tables: DocArray[TextChunk] = DocArray()
    images: DocArray[ImageChunk] = DocArray()
    path: AnyUrl | None
    title: str | None
    creation_date: str | None
    mod_date: str | None
