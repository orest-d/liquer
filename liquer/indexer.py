"""Indexer is a callable or an Indexer object that can 'visit' data and metadata (mainly) in the event of creation.
Indexers can be used for multiple purposes:

- To extend and/or customize the metadata generation. This is essential e.g to specify analytical tools usable for 
- To index data and/or metadata e.g. in a search engine.

It must return valid metadata. As a minimum, indexer should return the metadata that it gets as a parameter.
"""

from enum import Enum
from liquer.template import expand_simple
from liquer.web import key_query_parameters


class Indexer(object):
    """Indexer superclass"""

    def __call__(self, key=None, query=None, data=None, metadata=None):
        return metadata

    def identifier(self):
        """This should return an identifier uniquely identifying the indexer among all the indexers"""
        return self.__class__.__name__

    def metadata_item_equalts(self, key, value):
        return MetadataItemEquals(self, key, value)

class IndexerProxy(Indexer):
    """Proxy to another indexer"""

    def __init__(self, indexer):
        self.indexer = indexer

    def __call__(self, key=None, query=None, data=None, metadata=None):
        return self.indexer(key=key, query=query, data=data, metadata=metadata)

    def identifier(self):
        return "%s(%s)" % (self.__class__.__name__, self.indexer.identifier())


class FilterIndexer(IndexerProxy):
    """Indexer filter superclass - calls the indexer only when the condition is met."""

    def __call__(self, key=None, query=None, data=None, metadata=None):
        if self.condition(key=key, query=query, data=data, metadata=metadata):
            return self.indexer(key=key, query=query, data=data, metadata=metadata)
        else:
            return metadata

    def condition(self, key=None, query=None, data=None, metadata=None):
        return True


class MetadataItemEquals(FilterIndexer):
    def __init__(self, indexer, key, value):
        self.indexer = indexer
        self.key = key
        self.value = value

    def condition(self, key=None, query=None, data=None, metadata=None):
        return metadata.get(self.key) == self.value

    def identifier(self):
        return f"[{self.key}=={self.value}]({self.indexer.identifier()})"


class NullIndexer(Indexer):
    """Empty indexer, does nothing."""

    def __call__(self, key=None, query=None, data=None, metadata=None):
        return metadata


class IndexerRegistry(Indexer):
    """Registry of indexers.
    IndexerRegistry is an Indexer.
    """

    def __init__(self):
        self.indexers = {}
        self.identifiers = []

    def register(self, indexer, identifier=None):
        """Register an indexer"""
        if identifier is None:
            if isinstance(indexer, Indexer):
                identifier = indexer.identifier()
            else:
                identifier = indexer.__name__
        self.indexers[identifier] = indexer
        self.identifiers = [x for x in self.identifiers if x != identifier] + [
            identifier
        ]

    def __call__(self, key=None, query=None, data=None, metadata=None):
        for i in self.identifiers:
            metadata = self.indexers[i](
                key=key, query=query, data=data, metadata=metadata
            )
        return metadata


_indexer_registry = None


def indexer_registry():
    """Returns the global indexer registry (singleton)"""
    global _indexer_registry
    if _indexer_registry is None:
        _indexer_registry = IndexerRegistry()
    return _indexer_registry


def reset_index_registry():
    global _indexer_registry
    _indexer_registry = IndexerRegistry()
    return _indexer_registry


def init_indexer_registry():
    """Provides basic initialization of the indexer registry.
    This is a convenience function to set up some basic indexer functionality.
    """
    r = indexer_registry()
    r.register(AssureTools())


def register_indexer(indexer):
    """Function to register an indexer."""
    indexer_registry().register(indexer)


def index(key=None, query=None, data=None, metadata=None):
    indexer_registry()(key=key, query=query, data=data, metadata=metadata)


class ToolEmbedding(Enum):
    DEFAULT = "iframe"
    IFRAME = "iframe"  # Show inside an iframe
    GUI = "gui"  # Let the GUI display it - i.e. supported directly by GUI. Should be identical to link
    LINK = "link"  # Follow the link - replaces the content in the current tab
    TAB = "tab"  # Open in a new tab
    WINDOW = "window"  # Open in a new window

class AssureTools(Indexer):
    """Assure existence of the tools section in the metadata"""
    def identifier(self):
        return "assure_tools"
    def __call__(self, key=None, query=None, data=None, metadata=None):
        if metadata is None:
            metadata = dict(tools={})
        tools = metadata.get("tools", [])
        metadata["tools"] = tools

        return metadata

class AddTool(Indexer):
    HIGH_PRIORITY = 10
    NORMAL_PRIORITY = 100
    LOW_PRIORITY = 1000

    def __init__(
        self, link, menu="View", embedding=ToolEmbedding.DEFAULT, priority=None
    ):
        self.link = link
        self.menu = menu
        self.embedding = embedding
        self.priority = priority or self.NORMAL_PRIORITY

    def __call__(self, key=None, query=None, data=None, metadata=None):
        if metadata is None:
            metadata = dict(tools={})
        variables = key_query_parameters(key=key, query=query)
        link = expand_simple(self.link, variables=variables)
        tools = metadata.get("tools", [])
        tools.append(
            dict(
                link=link,
                menu=self.menu,
                embedding=self.embedding.value,
                priority=self.priority,
            )
        )
        tools = [
            x[1] for x in sorted((x.get("priority", self.LOW_PRIORITY)) for x in tools)
        ]
        cleaned_tools = []
        links = []
        for x in sorted_tools:
            if "link" in x and x["link"] not in links:
                links.append(x["link"])
                cleaned_tools.append(x)
        metadata["tools"] = cleaned_tools

        return metadata
