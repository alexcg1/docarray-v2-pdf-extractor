import csv
import io
import os
import tempfile
from pprint import pprint

import pdfplumber
import requests as rq
from docarray import BaseDoc, DocArray
from docarray.documents import ImageDoc, TextDoc
from docarray.typing import AnyUrl
from dotenv import load_dotenv
from jina import Executor, requests

load_dotenv()


class ImageChunk(ImageDoc):
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


class PDFExtractorExecutor(Executor):
    def __init__(
        self,
        content_types: list = ['text', 'table', 'image', 'metadata'],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.content_types = content_types

    @requests(on='/print')
    def print_docs(self, docs: DocArray[PDFDocument], **kwargs):
        print('DEBUG: print doc inside Executor')
        print(docs[0])

    @requests(on='/extract')
    def add_chunks(self, docs: DocArray[PDFDocument], **kwargs):
        for doc in docs:
            if 'text' in self.content_types:
                self._extract_text(doc)
            if 'table' in self.content_types:
                self._extract_tables(doc)
            if 'image' in self.content_types:
                self._extract_images(doc)
            if 'metadata' in self.content_types:
                self._extract_metadata(doc)

    def _extract_metadata(self, doc: PDFDocument):
        print('Extracting metadata')
        with pdfplumber.open(doc.path) as pdf:
            doc.creation_date = pdf.metadata.get('CreationDate', None)
            doc.mod_date = pdf.metadata.get('ModDate', None)
            doc.title = pdf.metadata.get('Title', 'Untitled')

        return doc

    def _extract_text(self, doc: PDFDocument, **kwargs):
        print('Extracting text')
        with pdfplumber.open(doc.path) as pdf:
            for page in pdf.pages:
                for page_no, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    text_chunk = TextChunk(
                        text=text,
                        tags={
                            'media_type': 'text',
                            'filename': str(doc.path),
                            'page_no': page_no,
                            'parent_id': doc.id,
                        },
                    )
                    doc.texts.append(text_chunk)

    def _extract_tables(self, doc: PDFDocument):
        print('Extracting tables')
        with pdfplumber.open(doc.path) as pdf:
            for page in pdf.pages:
                for page_no, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    for table in tables:
                        output = io.StringIO()
                        writer = csv.writer(
                            output, quoting=csv.QUOTE_NONNUMERIC
                        )
                        writer.writerows(table)
                        csv_data = output.getvalue()
                        csv_doc = TextChunk(
                            text=csv_data,
                            tags={
                                'media_type': 'table',
                                'filename': str(doc.path),
                                'page_no': page_no,
                                'parent_id': doc.id,
                            },
                        )
                        doc.tables.append(csv_doc)

    def _extract_images(self, doc: PDFDocument):
        print('Extracting images')
        with pdfplumber.open(doc.path) as pdf:
            for page_no, page in enumerate(pdf.pages, start=1):
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

                    image_doc = ImageChunk(
                        url=output_path,
                        tensor=None,
                        embedding=None,
                        tags={
                            'media_type': 'image',
                            'filename': str(doc.path),
                            'page_no': page_no,
                            'parent_id': doc.id,
                        },
                    )
                    image_doc.tensor = image_doc.url.load()
                    doc.images.append(image_doc)


class CLIPEncoder(Executor):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)

    @requests
    def encode(self, docs: DocArray[PDFDocument], **kwargs):
        for doc in docs:
            for chunk in doc.texts:
                self._clip_encode(chunk)
            for chunk in doc.tables:
                self._clip_encode(chunk)
            # for chunk in doc.images:
            # self._clip_encode(chunk)

    def _clip_encode(self, doc: PDFDocument):
        url = 'https://evolving-lacewing-2d90dee9c4-http.wolf.jina.ai/post'
        if type(doc) == 'ImageChunk':
            data = 'foo'   # rewrite to get url
        else:
            data = {'text': doc.text}

        payload = {
            'data': [data],
            'execEndpoint': '/',
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': os.getenv('JINA_TOKEN'),
        }

        response = rq.post(url, json=payload, headers=headers)

        content = response.json()
        doc.embedding = content['data'][0]['embedding']
