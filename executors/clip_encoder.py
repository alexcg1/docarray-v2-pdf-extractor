import os

import requests as rq
from docarray import DocArray
from docarray.utils.map import map_docs
from dotenv import load_dotenv
from jina import Executor, requests

from .helper import ImageChunk, PDFDocument, TextChunk

load_dotenv()

print(os.getenv('JINA_TOKEN'))


class CLIPEncoder(Executor):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)

    @requests
    def encode(self, docs: DocArray[PDFDocument], **kwargs):
        print('Encoding chunks')
        for doc in docs:
            doc.texts = DocArray[TextChunk](
                list(map_docs(doc.texts, clip_encode_chunk))
            )
            # for chunk in doc.texts:
            doc.tables = DocArray[TextChunk](
                list(map_docs(doc.tables, clip_encode_chunk))
            )
            doc.images = DocArray[ImageChunk](
                list(map_docs(doc.images, clip_encode_chunk))
            )


def clip_encode_doc(docs):
    url = 'https://evolving-lacewing-2d90dee9c4-http.wolf.jina.ai/post'

    for doc in docs:
        if isinstance(doc, TextChunk):
            data = {'text': doc.text}
        elif isinstance(doc, ImageChunk):
            data = {'url': doc.url}
        else:
            raise TypeError('Unsupported type')

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


def clip_encode_chunk(doc: TextChunk | ImageChunk):
    url = 'https://evolving-lacewing-2d90dee9c4-http.wolf.jina.ai/post'

    if isinstance(doc, TextChunk):
        data = {'text': doc.text}
    elif isinstance(doc, ImageChunk):
        data = {'url': doc.url}
    else:
        raise TypeError('Unsupported type')

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
    print(content)
    doc.embedding = content['data'][0]['embedding']

    return doc
