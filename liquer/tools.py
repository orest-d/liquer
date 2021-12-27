from liquer.parser import *
from liquer.store import get_store, KeyNotFoundStoreException, set_store
from liquer.cache import get_cache

def get_stored_metadata(query):
    """Get metadata for a query - if it is stored in cache or a store.    
    """
    if not isinstance(query,Query):
        query = parse(query)
    if query.is_resource_query():
        rq = query.resource_query()
        header = rq.header
        key = rq.path()
        try:
            return get_store().get_metadata(key)
        except KeyNotFoundStoreException:
            return None
    else:
        return get_cache().get_metadata(str(query))
