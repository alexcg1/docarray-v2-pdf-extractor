import os
import pickle

from docarray import DocArray
from docarray.utils.find import find
from jina import Flow

from executor import (CLIPEncoder, PDFDocument, PDFExtractor, TextChunk,
                      clip_encode_chunk)

if os.path.isfile('index.p'):
    print('Using previously-saved index')
    with open('index.p', 'rb') as file:
        index = pickle.load(file)

else:
    docs = DocArray[PDFDocument]([PDFDocument(path='rabbit.pdf')])

    content_types = ['text', 'image', 'table', 'metadata']

    flow = (
        Flow()
        .add(
            uses=PDFExtractor,
            uses_with={'content_types': content_types},
            name='extractor',
        )
        .add(uses=CLIPEncoder, name='encoder')
    )

    with flow:
        index = flow.post(
            inputs=docs,
            on='/extract',
            return_type=DocArray[PDFDocument],
            show_progress=True,
        )

    with open('index.p', 'wb') as file:
        pickle.dump(index, file)

# set up query doc
search_query = input('What do you want to search for? > ')
query_doc = TextChunk(text=search_query)
clip_encode_chunk(query_doc)

# get results
top_matches, scores = find(
    index=index[0].texts,
    query=query_doc,
    embedding_field='embedding',
    metric='cosine_sim',
)

# display results
print(top_matches[0].text)
