from os import makedirs
import os.path
import hashlib
import json
from liquer.state_types import state_types_registry
from liquer.state import State
from liquer.parser import all_splits, encode, decode

"""
Cache defines a mechanism for caching state for a query (or a subquery).
Since there is a one-to-one correspondence between a query and a state (more precisely state data),
cache can work as a simple key-value store, using state.query as a key.
Cache object must define three methods:
- get - for retrieving state from a key (query); get returns None if the state cannot be recovered
- store - for storing the state
- contains - for checking the availability of a state associated with a key (query)

A global cache is configured by set_cache and available via get_cache.
From a given query, cached_part function tries to recover as much as possible from cache,
while returning (besides the recovered state) the query remainder that needs to be evaluated. 
"""
_cache = None


def get_cache():
    global _cache
    if _cache is None:
        _cache = NoCache()
    return _cache


def set_cache(cache):
    global _cache
    _cache = cache


def cached_part(query, cache=None):
    if cache is None:
        cache = get_cache()

    if isinstance(cache, NoCache):  # Just an optimization - to avoid looping over all query splits
        return State(), encode(decode(query))

    for key, remainder in all_splits(query):
        if key == "":
            return State(), remainder
        if cache.contains(key):
            return cache.get(key), remainder

    # Should never get here, but this is a sensible default:
    return State(), encode(decode(query))


class NoCache:
    def get(self, key):
        return None

    def store(self, state):
        return None

    def contains(self, key):
        return False


class MemoryCache:
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

    def contains(self, key):
        return key in self.storage


class FileCache:
    def __init__(self, path):
        self.path = path
        try:
            makedirs(path)
        except FileExistsError:
            pass

    def to_path(self, key, prefix="state_", extension="json"):
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
            state.data = t.from_bytes(open(path, "rb").read())
            return state

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
        with open(self.to_path(state.query), "w") as f:
            f.write(json.dumps(state.as_dict()))
        t = state_types_registry().get(state.type_identifier)
        path = self.to_path(state.query, prefix="data_",
                            extension=t.default_extension())
        with open(path, "wb") as f:
            b, mime = t.as_bytes(state.data)
            f.write(b)
