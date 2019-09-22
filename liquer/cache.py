from os import makedirs
import os.path
import hashlib
import json
from liquer.state_types import state_types_registry
from liquer.state import State
from liquer.parser import all_splits, encode, decode
import logging

"""
Cache defines a mechanism for caching state for a query (or a subquery).
Since there is a one-to-one correspondence between a query and a state (more precisely state data),
cache can work as a simple key-value store, using state.query as a key.
Cache object must define three methods:
- get - for retrieving state from a key (query); get returns None if the state cannot be recovered
- store - for storing the state; should return True if the cache handled the storing 
- contains - for checking the availability of a state associated with a key (query)

A global cache is configured by set_cache and available via get_cache.
From a given query, cached_part function tries to recover as much as possible from cache,
while returning (besides the recovered state) the query remainder that needs to be evaluated. 
"""
_cache = None


def get_cache():
    """Get global cache object"""
    global _cache
    if _cache is None:
        _cache = NoCache()
    return _cache


def set_cache(cache):
    """Set global cache object"""
    global _cache
    _cache = cache


def cached_part(query, cache=None):
    """Get cached part of the query.
    Use either supplied cache object or global cache object (default).
    In the process, query is into two parts: the beginning of the query
    and the remainder. Function tries to find longest possible beginning of the query
    which is cached, then returns the cached state and the remainder of the query.
    (query == state.query + "/" + remainder)
    """
    if cache is None:
        cache = get_cache()

    if isinstance(cache, NoCache):  # Just an optimization - to avoid looping over all query splits
        return State(), encode(decode(query))

    for key, remainder in all_splits(query):
        if key == "":
            return State(), remainder
        if cache.contains(key):
            state = cache.get(key)
            if state is None:
                continue
            return state, remainder

    # Should never get here, but this is a sensible default:
    return State(), encode(decode(query))

class CacheMixin:
    def __add__(self, cache):
        return CacheCombine(self,cache)
    def if_contains(self,*attributes):
        return CacheIfHasAttributes(self,*attributes)
    def if_not_contains(self,*attributes):
        return CacheIfHasNotAttributes(self,*attributes)

class CacheCombine(CacheMixin):
    def __init__(self,cache1, cache2):
        self.cache1 = cache1
        self.cache2 = cache2

    def get(self, key):
        value = self.cache1.get(key)
        if value is not None:
            return value
        else:
            return self.cache2.get(key)

    def store(self, state):
        if self.cache1.store(state):
            return True
        else:
            return self.cache2.store(state)

    def contains(self, key):
        if self.cache1.contains(key):
            return True
        else:
            return self.cache2.contains(key)

    def __str__(self):
        return f"{str(self.cache1)} + {str(self.cache2)}"
        
    def __repr__(self):
        return f"{repr(self.cache1)} + {repr(self.cache2)}"

class CacheIfHasAttributes(CacheMixin):
    def __init__(self,cache, *attributes):
        self.cache = cache
        self.attributes = attributes

    def get(self, key):
        return self.cache.get(key)

    def store(self, state):
        if all(state.attributes.get(a, False) for a in self.attributes):
            return self.cache.store(state)
        else:
            return False

    def contains(self, key):
        return self.cache.contains(key)

    def __str__(self):
        return f"({str(self.cache)} containing {', '.join(self.attributes)})"
        
    def __repr__(self):
        return f"CacheIfHasAttributes({repr(self.cache1)}, {', '.join(map(repr,self.attributes))})"

class CacheIfHasNotAttributes(CacheMixin):
    def __init__(self,cache, *attributes):
        self.cache = cache
        self.attributes = attributes

    def get(self, key):
        return self.cache.get(key)

    def store(self, state):
        if any(state.attributes.get(a, False) for a in self.attributes):
            return False
        else:
            return self.cache.store(state)

    def contains(self, key):
        return self.cache.contains(key)

    def __str__(self):
        return f"({str(self.cache)} not containing {', '.join(self.attributes)})"
        
    def __repr__(self):
        return f"CacheIfHasNotAttributes({repr(self.cache1)}, {', '.join(map(repr,self.attributes))})"


class NoCache(CacheMixin):
    """Trivial cache object which does not cache any state"""
    def get(self, key):
        return None

    def store(self, state):
        return False

    def contains(self, key):
        return False

    def __str__(self):
        return "No cache"

    def __repr__(self):
        return "NoCache()"


class MemoryCache(CacheMixin):
    """Simple cache which stores all the states in a dictionary.
    Note that continuous heavy use of the system with MemoryCache
    may lead to filling the memory, therefore this is not ideal
    for long running services. 
    """
    def __init__(self):
        self.storage = {}

    def get(self, key):
        state = self.storage.get(key)
        if state is None:
            return None
        else:
            return state.clone()

    def store(self, state):
        self.storage[state.query] = state.clone()
        return True

    def contains(self, key):
        return key in self.storage

    def __str__(self):
        return "Memory cache"
        
    def __repr__(self):
        return "MemoryCache()"


class FileCache(CacheMixin):
    """Simple file cache which stores all the states in files
    in a specified directory of a local filesystem.
    Two files are created: one for the state metadata and the other one with
    serialized version of the state data.
    
    Note that no mechanism for maintaining freshness or constraining file size
    is provided. This may lead to filling the space on the filesystem,
    therefore this is not ideal for long running public web-services.
    """
    def __init__(self, path):
        self.path = path
        try:
            makedirs(path)
        except FileExistsError:
            pass

    def to_path(self, key, prefix="state_", extension="json"):
        "Construct file path from a key and optionally prefix and file extension."
        m = hashlib.md5()
        m.update(key.encode('utf-8'))
        digest = m.hexdigest()
        return os.path.join(self.path, f"{prefix}{digest}.{extension}")

    def get(self, key):
        state_path = self.to_path(key)
        if os.path.exists(state_path):
            state = State()
            state = state.from_dict(json.loads(open(state_path).read()))
        else:
            return None
        t = state_types_registry().get(state.type_identifier)
        path = self.to_path(key, prefix="data_",
                            extension=t.default_extension())
        if os.path.exists(path):
            try:
                state.data = t.from_bytes(open(path, "rb").read())
                return state
            except:
                logging.exception(f"Cache failed to recover {key}")
                return None

    def contains(self, key):
        state_path = self.to_path(key)
        if os.path.exists(state_path):
            state = State()
            state = state.from_dict(json.loads(open(state_path).read()))
        else:
            return False
        t = state_types_registry().get(state.type_identifier)
        path = self.to_path(key, prefix="data_",
                            extension=t.default_extension())
        if os.path.exists(path):
            return True
        else:
            return False

    def store(self, state):
        try:
            with open(self.to_path(state.query), "w") as f:
                f.write(json.dumps(state.as_dict()))
        except:
            logging.exception(f"Cache writing error: {state.query}")
            return False
            
        t = state_types_registry().get(state.type_identifier)
        path = self.to_path(state.query, prefix="data_",
                            extension=t.default_extension())
        with open(path, "wb") as f:
            try:
                b, mime = t.as_bytes(state.data)
                f.write(b)
            except NotImplementedError:
                return False
        return True

    def __str__(self):
        return f"File cache at {self.path}"
        
    def __repr__(self):
        return f"FileCache('{self.path}')"
