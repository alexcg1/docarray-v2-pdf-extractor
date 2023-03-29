import tempfile

import pdfplumber
from docarray import BaseDoc, DocArray
from docarray.documents import ImageDoc, TextDoc
from docarray.typing import AnyUrl
from docarray.utils.map import map_docs


class PDFDocument(BaseDoc):
    chunks: DocArray = DocArray()
    path: AnyUrl | None
    title: str | None
    creation_date: str | None
    mod_date: str | None


class PDFExtractor:
    def add_chunks(docs: DocArray):
        # None of these map_docs lines do anything to the doc
        map_docs(docs, PDFExtractor._extract_text)
        map_docs(docs, PDFExtractor._extract_metadata, backend='thread')
        map_docs(docs, PDFExtractor._extract_images)

        # This works tho
        for doc in docs:
            PDFExtractor._extract_text(doc)
            PDFExtractor._extract_images(doc)
            PDFExtractor._extract_metadata(doc)

    def _extract_metadata(doc: PDFDocument):
        with pdfplumber.open(doc.path) as pdf:
            doc.creation_date = pdf.metadata['CreationDate']
            doc.mod_date = pdf.metadata['ModDate']
            if 'Title' in pdf.metadata.keys():
                doc.title = pdf.metadata['Title']
            else:
                doc.title = 'Untitled'

        return doc

    def _extract_text(doc: PDFDocument):
        with pdfplumber.open(doc.path) as pdf:
            for page in pdf.pages:
                for page in pdf.pages:
                    text = page.extract_text()
                    text_doc = TextDoc(text=text)
                    doc.chunks.append(text_doc)

        return doc

    def _extract_images(doc: PDFDocument):
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

                    temp_file = tempfile.NamedTemporaryFile(
                        prefix='my_temp_file_'
                    )

                    with temp_file:
                        output_path = f'{temp_file.name}.png'
                        image_obj.save(output_path)
                    # temp_file.close()

                    image_doc = ImageDoc(
                        url=output_path,
                        tensor=None,
                        embedding=None,
                    )
                    image_doc.tensor = image_doc.url.load()
                    doc.chunks.append(image_doc)


docs = DocArray([PDFDocument(path='rabbit.pdf')])

output = PDFExtractor.add_chunks(docs)

print(docs[0])
