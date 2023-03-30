from docarray import BaseDoc, DocArray
from docarray.documents import ImageDoc, TextDoc
from docarray.typing import AnyUrl
from docarray.utils.map import map_docs
from jina import Deployment, Executor, requests


class TextChunk(TextDoc):
    tags: dict = {}


class PDFDocument(BaseDoc):
    texts: DocArray[TextChunk] = DocArray()
    path: AnyUrl | None


class Extractor(Executor):
    def __init__(
        self,
        content_types: list = ['text', 'table', 'image', 'metadata'],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.content_types = content_types

    @requests(on='/extract')
    def add_chunks(self, docs: DocArray[PDFDocument], **kwargs):
        for doc in docs:
            self._extract_text(doc)

    def _extract_text(self, doc: PDFDocument, **kwargs):
        for _ in range(0, 90):
            doc.texts.append(TextChunk(text='foo'))


dep = Deployment(
    uses=Extractor,
    uses_with={'content_types': ['text']},
)

docs = DocArray([PDFDocument(path='foo.png')])
print(f'input: {docs[0]}')

with dep:
    output = dep.post(inputs=docs, on='/extract')   # this works fine

    print(f'output: {output[0]}')
