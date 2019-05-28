from os import makedirs
import os.path
import hashlib
import json
from liquer.state_types import state_types_registry
from liquer.state import State

_cache = None


def cache():
    global _cache
    if _cache is None:
        _cache = NoCache()
    return _cache


def set_cache(cache):
    global _cache
    _cache = cache


class NoCache:
    def get(self, key):
        return None

    def store(self, state):
        return None


class MemoryCache:
    def __init__(self):
        self.storage = {}

    def get(self, key):
        return self.storage.get(key).clone()

    def store(self, state):
        self.storage[state.query] = state.clone()


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

    def store(self, state):
        with open(self.to_path(state.query), "w") as f:
            f.write(json.dumps(state.as_dict()))
        t = state_types_registry().get(state.type_identifier)
        path = self.to_path(state.query, prefix="data_",
                            extension=t.default_extension())
        with open(path, "wb") as f:
            b, mime = t.as_bytes(state.data)
            f.write(b)
