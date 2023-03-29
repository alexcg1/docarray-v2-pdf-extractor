import csv
import io
import tempfile
from pprint import pprint

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


class ImageChunk(ImageDoc):
    tags: dict = {}


class TextChunk(TextDoc):
    tags: dict = {}


class PDFExtractor:
    def add_chunks(docs: DocArray):
        # None of these map_docs lines do anything to the doc
        # map_docs(docs, PDFExtractor._extract_text)
        # map_docs(docs, PDFExtractor._extract_metadata, backend='thread')
        # map_docs(docs, PDFExtractor._extract_images)

        # This works tho
        for doc in docs:
            PDFExtractor._extract_text(doc)
            PDFExtractor._extract_tables(doc)
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
                for page_no, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    text_doc = TextDoc(
                        text=text,
                        tags={
                            'media_type': 'image',
                            'filename': 'doc.path',
                            'page_no': page_no,
                        },
                    )
                    doc.chunks.append(text_doc)

    def _extract_tables(doc: PDFDocument):
        with pdfplumber.open(doc.path) as pdf:
            for page in pdf.pages:
                for page_no, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table in tables:
                        # pprint(table)
                        output = io.StringIO()
                        writer = csv.writer(
                            output, quoting=csv.QUOTE_NONNUMERIC
                        )
                        writer.writerows(table)
                        csv_data = output.getvalue()
                        csv_doc = TextDoc(
                            text=csv_data,
                            tags={
                                'media_type': 'table',
                                'filename': 'doc.path',
                                'page_no': page_no,
                            },
                        )
                        doc.chunks.append(csv_doc)
                        # Do something with the CSV data, e.g. print it
                        # print(csv_data)
                    # text_doc = TextDoc(text=text)
                    # doc.chunks.append(text_doc)

    def _extract_images(doc: PDFDocument):
        with pdfplumber.open(doc.path) as pdf:
            for page_no, page in enumerate(pdf.pages):
                for image in page.images:
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
                        tags={
                            'media_type': 'image',
                            'filename': 'doc.path',
                            'page_no': page_no,
                        },
                    )
                    image_doc.tensor = image_doc.url.load()
                    doc.chunks.append(image_doc)


docs = DocArray([PDFDocument(path='rabbit.pdf')])

output = PDFExtractor.add_chunks(docs)

print(docs[0])
