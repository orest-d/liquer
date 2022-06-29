"""Indexer is a callable or an Indexer object that can 'visit' data and metadata (mainly) in the event of creation.
Indexers can be used for multiple purposes:

- To extend and/or customize the metadata generation. This is essential e.g to specify analytical tools usable for 
- To index data and/or metadata e.g. in a search engine.

It must return valid metadata. As a minimum, indexer should return the metadata that it gets as a parameter.
"""

class Indexer(object):
    def __call__(self, key=None, query=None, data=None, metadata=None):
        return metadata
    def identifier(self):
        """This should return an identifier uniquely identifying the indexer among """
        return self.__class__.__name__

class IndexerRegistry(Indexer):
    """Registry of indexers.
    IndexerRegistry is an Indexer.
    """
    def __init__(self):
        self.indexers = {}
        self.identifiers=[]
 
    def register(self, indexer, identifier=None):
        """Register an indexer"""
        if identifier is None:
            if isinstance(indexer, Indexer):
                identifier=indexer.identifier()
            else:
                identifier=indexer.__name__
        self.indexers[identifier]=indexer
        self.identifiers = [x for x in self.identifiers if x!=identifier] + [identifier]
 
    def __call__(self, key=None, query=None, data=None, metadata=None):
        for i in self.identifiers:
            metadata = self.indexers[i](key=key, query=query, data=data, metadata=metadata)
        return metadata

_indexer_registry = None


def indexer_registry():
    """Returns the global indexer registry (singleton)"""
    global _indexer_registry
    if _indexer_registry is None:
        _indexer_registry = IndexerRegistry()
    return _indexer_registry

def init_indexer_registry():
    """Provides basic initialization of the indexer registry.
    This is a convenience function to set up some basic indexer functionality.
    """
    r = indexer_registry()
    r.register(BasicToolIndexer())

def register_indexer(indexer):
    """Function to register an indexer.
    """
    indexer_registry().register(indexer)

def index(key=None, query=None, data=None, metadata=None):
    indexer_registry()(key=key, query=query, data=data, metadata=metadata)


class BasicToolIndexer(Indexer):
    def __call__(self, key=None, query=None, data=None, metadata=None):
        if metadata is None:
            metadata=dict(tools={})
        if "tools" not in metadata:
            metadata["tools"] = {}
        return metadata
