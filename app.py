from docarray import DocArray
from jina import Deployment

from executor import PDFDocument, PDFExtractorExecutor

docs = DocArray[PDFDocument]([PDFDocument(path='rabbit.pdf')])

content_types = ['text', 'image', 'table', 'metadata']

dep = Deployment(
    uses=PDFExtractorExecutor,
    uses_with={'content_types': content_types},
)

with dep:
    output = dep.post(
        inputs=docs, on='/extract', return_type=DocArray[PDFDocument]
    )

print(output[0])
