import pdfplumber
from docarray import BaseDoc, DocArray
from docarray.documents import ImageDoc, TextDoc
from docarray.typing import AnyUrl


class PDFDocument(BaseDoc):
    image_chunks: DocArray[ImageDoc] | None
    text_chunks: DocArray[TextDoc] | None
    path: AnyUrl | None
    title: str | None
    creation_date: str | None
    mod_date: str | None


class PDFExtractor:
    def add_chunks(docs: DocArray):
        for doc in docs:
            PDFExtractor._extract_text(doc)
            PDFExtractor._extract_metadata(doc)
            PDFExtractor._extract_images(doc)

    def _extract_metadata(doc: PDFDocument):
        with pdfplumber.open(doc.path) as pdf:
            doc.creation_date = pdf.metadata['CreationDate']
            doc.mod_date = pdf.metadata['ModDate']

    def _extract_text(doc: PDFDocument):
        text_chunks = DocArray()
        with pdfplumber.open(doc.path) as pdf:
            for page in pdf.pages:
                for page in pdf.pages:
                    text = page.extract_text()
                    text_doc = TextDoc(text=text)
                    text_chunks.append(text_doc)

        doc.text_chunks = text_chunks

    def _extract_images(doc: PDFDocument):
        image_chunks = DocArray()
        with pdfplumber.open(doc.path) as pdf:
            for p, page in enumerate(pdf.pages):
                for i, image in enumerate(page.images):
                    image_bbox = (
                        image['x0'],
                        page.height - image['y1'],
                        image['x1'],
                        page.height - image['y0'],
                    )
                    cropped_page = page.crop(image_bbox)
                    image_obj = cropped_page.to_image(resolution=200)
                    output_path = f'images/{p}-{i}.png'
                    image_obj.save(output_path)
                    image_doc = ImageDoc(
                        url=output_path,
                        tensor=None,
                        embedding=None,
                    )
                    image_doc.tensor = image_doc.url.load()
                    image_chunks.append(image_doc)

        doc.image_chunks = image_chunks


docs = DocArray([PDFDocument(path='rabbit.pdf')])

output = PDFExtractor.add_chunks(docs)

print(docs[0])
