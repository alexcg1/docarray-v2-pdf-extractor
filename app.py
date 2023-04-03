from docarray import DocArray
from jina import Deployment, Flow

from executor import CLIPEncoder, PDFDocument, PDFExtractorExecutor

docs = DocArray[PDFDocument]([PDFDocument(path='rabbit.pdf')])

content_types = ['text', 'image', 'table', 'metadata']
content_types = ['text']

flow = (
    Flow()
    .add(
        uses=PDFExtractorExecutor,
        uses_with={'content_types': content_types},
        name='extractor',
    )
    .add(uses=CLIPEncoder, name='encoder')
)

# dep = Deployment(
# uses=PDFExtractorExecutor,
# uses_with={'content_types': content_types},
# )

with flow:
    output = flow.post(
        inputs=docs, on='/extract', return_type=DocArray[PDFDocument]
    )

print(output[0])
print(output[0].texts[0])
