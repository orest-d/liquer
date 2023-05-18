import json
from pathlib import Path
from whoosh.index import create_in
from whoosh.fields import *
from liquer import *
from liquer.web import key_link
from liquer.indexer import Indexer, register_indexer
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import Every

_schema = None
_ix = None


def init(dir="whoosh_index"):
    """Initialize the Whoosh search engine."""
    global _schema, _ix, _writer
    _schema = Schema(
        title=TEXT(stored=True),
        description=TEXT(stored=True),
        characteristics=TEXT(stored=True),
        key=ID(unique=True, stored=True),
        text_key=TEXT(stored=False),
    )
    _ix = create_in(dir, _schema)
    register_indexer(AddToWhooshIndex())


def get_writer():
    global _ix
    if _ix is None:
        init()
    return _ix.writer()


class AddToWhooshIndex(Indexer):
    HIGH_PRIORITY = 10
    NORMAL_PRIORITY = 100
    LOW_PRIORITY = 1000

    def identifier(self):
        return f"AddToWhooshIndex()"

    def __call__(self, key=None, query=None, data=None, metadata=None):
        if metadata is None or key is None:
            return metadata
        add(
            metadata.get("title", ""),
            metadata.get("description", ""),
            metadata.get("characteristics", ""),
            key=key,
        )
        return metadata


def add(title, description, characteristics, key, commit=True, writer=None):
    if writer is None:
        writer = get_writer()

    writer.update_document(
        title=title,
        description=description,
        characteristics=characteristics,
        key=key,
        text_key=key,
    )
    if commit:
        writer.commit()


@first_command(ns="whoosh")
def reindex_store(context=None):
    context = get_context(context)

    with get_writer() as writer:
        store = context.store()
        for key in store.keys():
            metadata = store.get_metadata(key)
            print(f"Adding {key} to index")
            add(
                title=metadata.get("title", ""),
                description=metadata.get("description", ""),
                characteristics=metadata.get("characteristics", ""),
                key=key,
                commit=False,
                writer=writer,
            )
        # writer.commit()


@first_command(ns="whoosh")
def search(query, limit=100, context=None):
    context = get_context(context)
    with _ix.searcher() as searcher:
        q = MultifieldParser(
            ["title", "description", "key", "text_key"], _schema
        ).parse(query)
        results = searcher.search(q)
        r = []
        for i, x in enumerate(results):
            r.append(
                dict(
                    key=x["key"],
                    title=x["title"],
                    description=x["description"],
                    link=key_link(x["key"], path_only=True),
                )
            )
            if i > limit:
                break
        return r


@first_command(ns="whoosh")
def search_json(query, limit=100, context=None):
    context = get_context(context)
    context.mimetype = "text/json"
    return json.dumps(search(query, limit, context=context))


@command(ns="whoosh")
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


@command(ns="whoosh")
def web(context=None):
    context = get_context(context)
    return (Path(__file__).parent / "lq_whoosh.html").read_text()
