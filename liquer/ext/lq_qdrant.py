"""
A minimalistic support for use of the qdrant vector database
as a liquer indexer.

By default, the embeddings are done inside the qdrant database via the fastembed library.
The model is using the defaults of the qdrant/fastembed library.

To use this extension, you need the following dependencies:
- fastembed
- qdrant-client - install with pip install qdrant-client[fastembed]

"""
import json
from pathlib import Path

import fastembed
import fastembed.text
import fastembed.text.text_embedding
from liquer import *
from liquer.web import key_link
from liquer.indexer import Indexer, register_indexer
from qdrant_client import QdrantClient
from fastembed import TextEmbedding
from typing import List
import hashlib

EMBEDDING_MODEL_NAME="BAAI/bge-small-en-v1.5"
COLLECTION_NAME="store_descriptions"
QDRANT_PATH="qdrand"

QDRANT_CLIENT=None

def get_client(path=None) -> QdrantClient:
    import qdrant_client.local.qdrant_local as ql
    global QDRANT_CLIENT
    if path is None:
        path = QDRANT_PATH
    if QDRANT_CLIENT is None:
        QDRANT_CLIENT = QdrantClient(path=path)
    return QDRANT_CLIENT

@first_command(ns="qdrant")
def embedding_model_name():
    """Get the name of the embedding model used by the qdrant database."""
    return get_client().embedding_model_name

@first_command(ns="qdrant")
def get_fastembed_vector_size():
    """Get the fastembed vector parameters used by the qdrant database."""
    p=get_client().get_fastembed_vector_params().values().next()
    return dict(
        size=p.size,
        distance=p.distance
    )

def init(path=None):
    """Initialize the Qdrant database."""
    client = get_client(path)
    client.get_fastembed_vector_params
    register_indexer(AddToQdrantIndex())

#    client.create_collection(
#        collection_name=COLLECTION_NAME,
#        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
#    )

def key2hash(key):
    return hashlib.md5(str(key).encode("utf-8")).hexdigest()

class AddToQdrantIndex(Indexer):
    HIGH_PRIORITY = 10
    NORMAL_PRIORITY = 100
    LOW_PRIORITY = 1000

    def identifier(self):
        return f"AddToQdrantIndex()"

    def __call__(self, key=None, query=None, data=None, metadata=None):
        if metadata is None or key is None:
            return metadata
        add(
            title=metadata.get("title", ""),
            description=metadata.get("description", ""),
            characteristics=metadata.get("characteristics", {}).get("description",""),
            key=key,
            type_identifier=metadata.get("type_identifier", ""),
        )
        return metadata


def add(title, description, characteristics, key, type_identifier, client=None):
    if client is None:
        client = get_client()

    if title in (None,""):
        title=str(key)
    client.add(
        collection_name=COLLECTION_NAME,
        ids=[key2hash(key)],        
        metadata=[dict(
            title=title,
            description=description,
            characteristics=characteristics,
            key=key,
            type_identifier=type_identifier
        )],
        documents=[description]
    )


def store_content_batch_generator(context, batch_size=16):
    store = context.store()
    batch=[]
    for key in store.keys():
        metadata = store.get_metadata(key)
        print(f"Adding {key} to index")
        description=metadata.get("description", "")
        title=metadata.get("title", "")
        if len(description)>0 or len(title)>0:
            if len(title):
                text=f"{title}\n\n{description}"
            else:
                text=description

            batch.append(dict(
                title=title,
                description=description,
                characteristics=metadata.get("characteristics", ""),
                key=key,
                type_identifier=metadata.get("type_identifier", ""),
                text=text
            ))
        if len(batch)>=batch_size:
            yield batch
            batch=[]

    if len(batch)>0:
        yield batch

@first_command(ns="qdrant")
def reindex_store(context=None):
    context = get_context(context)

    embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)

    client = get_client()
    for batch in store_content_batch_generator(context):
        documents = [x["text"] for x in batch]
        ids=[key2hash(x["key"]) for x in batch]
        client.add(
            collection_name=COLLECTION_NAME,            
            ids=ids,
            metadata=batch,
            documents=documents
        )

@first_command(ns="qdrant")
def search(query, limit=100, context=None):
    context = get_context(context)
    client = get_client()
    response = client.query(
        collection_name=COLLECTION_NAME,
        query_text=query,
        limit=limit
    )
    results=[]
    for r in response:
        results.append(dict(
            key=r.metadata["key"],
            title=r.metadata["title"],
            description=r.metadata["description"],
            characteristics=r.metadata["characteristics"],
            score=r.score))

    return results
 
@first_command(ns="qdrant")
def search_json(query, limit=100, context=None):
    context = get_context(context)
    context.mimetype = "text/json"
    return json.dumps(search(query, limit, context=context))


@command(ns="qdrant")
def to_html(search_result, context=None):
    context = get_context(context)
    text = """
<html>
  <body>
    <table>
    """
    for r in search_result:
        link = key_link(r["key"], path_only=True)
        text += f"""
      <tr>
        <td><a href="{link}">{r['key']}</a></td>
        <td><a href="{link}">{r['title']}</a></td>
        <td>{r['description']}</td>
      </tr>
        """
    text += """
    </table>
    </body>
</html>
    """
    return text


@command(ns="qdrant")
def web(context=None):
    context = get_context(context)
    return (Path(__file__).parent / "lq_qdrant.html").read_text()
