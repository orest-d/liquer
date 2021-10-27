from os import makedirs
import os.path
import hashlib
import json
from liquer.state_types import state_types_registry
from liquer.state import State
from liquer.parser import all_splits, encode, decode
import logging
import traceback
import base64
import numpy as np

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

    if isinstance(
        cache, NoCache
    ):  # Just an optimization - to avoid looping over all query splits
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
    """Adds various cache combinator helpers"""

    def __add__(self, cache):
        return CacheCombine(self, cache)

    def if_contains(self, *attributes):
        "Cache if state contains all attributes"
        return CacheIfHasAttributes(self, *attributes)

    def if_not_contains(self, *attributes):
        "Cache if state contains none of the attributes"
        return CacheIfHasNotAttributes(self, *attributes)

    def if_attribute_equal(self, attribute, value):
        "Cache if state attribute is equal to value"
        return CacheAttributeCondition(self, attribute, value, True)

    def if_attribute_not_equal(self, attribute, value):
        "Cache if state attribute is not equal to value"
        return CacheAttributeCondition(self, attribute, value, False)


class CacheCombine(CacheMixin):
    def __init__(self, cache1, cache2):
        self.cache1 = cache1
        self.cache2 = cache2

    def clean(self):
        self.cache1.clean()
        self.cache2.clean()

    def get(self, key):
        value = self.cache1.get(key)
        if value is not None:
            return value
        else:
            return self.cache2.get(key)

    def get_metadata(self, key):
        value = self.cache1.get_metadata(key)
        if value is not None:
            return value
        else:
            return self.cache2.get_metadata(key)

    def store(self, state):
        self.remove(state.query)
        if self.cache1.store(state):
            return True
        else:
            return self.cache2.store(state)

    def store_metadata(self, metadata):
        if self.cache1.store_metadata(metadata):
            return True
        else:
            return self.cache2.store_metadata(metadata)

    def remove(self, key):
        return self.cache1.remove(key) and self.cache2.remove(key)

    def contains(self, key):
        if self.cache1.contains(key):
            return True
        else:
            return self.cache2.contains(key)

    def keys(self):
        for key in self.cache1.keys():
            yield key
        for key in self.cache2.keys():
            yield key

    def __str__(self):
        return f"{str(self.cache1)} + {str(self.cache2)}"

    def __repr__(self):
        return f"{repr(self.cache1)} + {repr(self.cache2)}"


class CacheIfHasAttributes(CacheMixin):
    def __init__(self, cache, *attributes):
        self.cache = cache
        self.attributes = attributes

    def clean(self):
        self.cache.clean()

    def get(self, key):
        return self.cache.get(key)

    def get_metadata(self, key):
        return self.cache.get_metadata(key)

    def store(self, state):
        self.remove(state.query)
        if all(
            state.metadata.get("attributes", {}).get(a, False) for a in self.attributes
        ):
            return self.cache.store(state)
        else:
            return False

    def store_metadata(self, metadata):
        if all(metadata.get("attributes", {}).get(a, False) for a in self.attributes):
            return self.cache.store_metadata(metadata)
        else:
            return False

    def remove(self, key):
        return self.cache.remove(key)

    def contains(self, key):
        return self.cache.contains(key)

    def keys(self):
        return self.cache.keys()

    def __str__(self):
        return f"({str(self.cache)} containing {', '.join(self.attributes)})"

    def __repr__(self):
        return f"CacheIfHasAttributes({repr(self.cache)}, {', '.join(map(repr,self.attributes))})"


class CacheIfHasNotAttributes(CacheMixin):
    def __init__(self, cache, *attributes):
        self.cache = cache
        self.attributes = attributes

    def clean(self):
        self.cache.clean()

    def get(self, key):
        return self.cache.get(key)

    def get_metadata(self, key):
        return self.cache.get_metadata(key)

    def store(self, state):
        self.remove(state.query)
        if any(
            state.metadata.get("attributes", {}).get(a, False) for a in self.attributes
        ):
            return False
        else:
            return self.cache.store(state)

    def store_metadata(self, metadata):
        if any(metadata.get("attributes", {}).get(a, False) for a in self.attributes):
            return False
        else:
            return self.cache.store_metadata(metadata)

    def remove(self, key):
        return self.cache.remove(key)

    def contains(self, key):
        return self.cache.contains(key)

    def keys(self):
        return self.cache.keys()

    def __str__(self):
        return f"({str(self.cache)} not containing {', '.join(self.attributes)})"

    def __repr__(self):
        return f"CacheIfHasNotAttributes({repr(self.cache)}, {', '.join(map(repr,self.attributes))})"


class CacheAttributeCondition(CacheMixin):
    def __init__(self, cache, attribute, value, equals=True):
        self.cache = cache
        self.attribute = attribute
        self.value = value
        self.equals = equals

    def clean(self):
        self.cache.clean()

    def get(self, key):
        return self.cache.get(key)

    def get_metadata(self, key):
        return self.cache.get_metadata(key)

    def store(self, state):
        self.remove(state.query)
        state_attribute_value = state.metadata.get("attributes", {}).get(self.attribute)
        if self.equals:
            if state_attribute_value == self.value:
                return self.cache.store(state)
        else:
            if state_attribute_value != self.value:
                return self.cache.store(state)
        return False

    def store_metadata(self, metadata):
        state_attribute_value = metadata.get("attributes", {}).get(self.attribute)
        if self.equals:
            if state_attribute_value == self.value:
                return self.cache.store_metadata(metadata)
        else:
            if state_attribute_value != self.value:
                return self.cache.store_metadata(metadata)
        return False

    def remove(self, key):
        return self.cache.remove(key)

    def contains(self, key):
        return self.cache.contains(key)

    def keys(self):
        return self.cache.keys()

    def __str__(self):
        if self.equals:
            return f"({str(self.cache)} when {self.attribute}=={self.value})"
        else:
            return f"({str(self.cache)} when {self.attribute}!={self.value})"

    def __repr__(self):
        return f"CacheAttributeCondition({repr(self.cache)}, {repr(self.attribute)}, {repr(self.value)}, {self.equals})"


class CacheProxy:
    def __init__(self, cache, verbose=False):
        self.cache = cache
        self.verbose = verbose

    def clean(self):
        if self.verbose:
            print("(CacheProxy) clean()")
        self.cache.clean()

    def get(self, key):
        if self.verbose:
            print(f"(CacheProxy) get({key})")
        return self.cache.get(key)

    def get_metadata(self, key):
        if self.verbose:
            print(f"(CacheProxy) get_metadata({key})")
        return self.cache.get_metadata(key)

    def store(self, state):
        if self.verbose:
            print(f"(CacheProxy) store()")
        return self.cache.store(state)

    def store_metadata(self, metadata):
        if self.verbose:
            print(f"(CacheProxy) store_metadata()")
        return self.cache.store_metadata(metadata)

    def remove(self, key):
        if self.verbose:
            print(f"(CacheProxy) remove({key})")
        return self.cache.remove(key)

    def contains(self, key):
        if self.verbose:
            print(f"(CacheProxy) contains({key})")
        return self.cache.contains(key)

    def keys(self):
        if self.verbose:
            print(f"(CacheProxy) keys()")
        return list(self.cache.keys())

    def __str__(self):
        return f"CacheProxy of {str(self.cache)}"

    def __repr__(self):
        return f"CacheProxy({repr(self.cache)})"


class NoCache(CacheMixin):
    """Trivial cache object which does not cache any state"""

    def clean(self):
        pass

    def get(self, key):
        return None

    def get_metadata(self, key):
        return None

    def store(self, state):
        return False

    def store_metadata(self, state):
        return False

    def remove(self, key):
        return False

    def contains(self, key):
        return False

    def keys(self):
        return []

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

    def clean(self):
        self.storage = {}

    def get(self, key):
        state = self.storage.get(key)

        if state is None:
            return None
        else:
            if state.metadata.get("status") != "ready":
                return None
            return state.clone()

    def get_metadata(self, key):
        state = self.storage.get(key)
        if state is None:
            return None
        else:
            return dict(**state.metadata)

    def store(self, state):
        if state.is_error:
            return None
        state.metadata["status"] = "ready"
        self.storage[state.query] = state.clone()
        return True

    def store_metadata(self, metadata):
        key = metadata["query"]
        self.storage[key] = self.storage.get(key, State())
        self.storage[key].metadata = metadata

        return True

    def remove(self, key):
        if key in self.storage:
            del self.storage[key]
        return True

    def contains(self, key):
        return key in self.storage

    def keys(self):
        return self.storage.keys()

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

    def clean(self):
        import glob

        print(f"Clean {self}")
        for f in glob.glob(os.path.join(self.path, "*")):
            logging.debug(f"Removing cache file {f}")
            os.remove(f)

    def to_path(self, key, prefix="state_", extension="json"):
        "Construct file path from a key and optionally prefix and file extension."
        m = hashlib.md5()
        m.update(key.encode("utf-8"))
        digest = m.hexdigest()
        return os.path.join(self.path, f"{prefix}{digest}.{extension}")

    def encode(self, b):
        return b

    def decode(self, s):
        return s

    def encode_metadata(self, b):
        return self.encode(b.encode("utf-8"))

    def decode_metadata(self, s):
        s = self.decode(s)
        if isinstance(s, str):
            return s
        elif isinstance(s, bytes):
            return s.decode("utf-8")
        else:
            raise Exception(f"Unsupported type: {type(s)}")

    def get(self, key):
        metadata = self.get_metadata(key)
        if metadata is None:
            print(f"(FileCache) Metadata missing: {key}")
            return None
        if metadata.get("status") != "ready":
            print(f"(FileCache) Not ready {key}; ", metadata.get("status"))
            return None
        state = State()
        state.metadata = metadata

        t = state_types_registry().get(metadata["type_identifier"])
        path = self.to_path(key, prefix="data_", extension=t.default_extension())
        if os.path.exists(path):
            try:
                state.data = t.from_bytes(self.decode(open(path, "rb").read()))
                return state
            except:
                traceback.print_exc()
                logging.exception(f"Cache failed to recover {key}")
                return None

    def _load_metadata(self, state_path):
        if os.path.exists(state_path):
            try:
                return json.loads(self.decode_metadata(open(state_path, "rb").read()))
            except:
                traceback.print_exc()
                return None
        else:
            return None

    def get_metadata(self, key):
        return self._load_metadata(self.to_path(key))

    def remove(self, key):
        metadata = self.get_metadata(key)
        if metadata is None:
            return True
        if "type_identifier" in metadata:
            t = state_types_registry().get(metadata["type_identifier"])
            path = self.to_path(key, prefix="data_", extension=t.default_extension())
            if os.path.exists(path):
                os.remove(path)

        state_path = self.to_path(key)
        if os.path.exists(state_path):
            os.remove(state_path)

        return True

    def contains(self, key):
        state_path = self.to_path(key)
        if os.path.exists(state_path):
            state = State()
            metadata = self._load_metadata(state_path)
            if metadata is None:
                return False
            else:
                return metadata.get("query") == key
        else:
            return False
        return True

    #        t = state_types_registry().get(state.type_identifier)
    #        path = self.to_path(key, prefix="data_", extension=t.default_extension())
    #        if os.path.exists(path):
    #            return True
    #        else:
    #            return False

    def keys(self):
        import glob

        for f in glob.glob(os.path.join(self.path, "state_*.json")):
            metadata = self._load_metadata(f)
            if metadata is not None:
                yield metadata["query"]

    def store(self, state):
        if state.is_error:
            return None
        state.metadata["status"] = "ready"

        if not self.store_metadata(state.metadata):
            return False

        t = state_types_registry().get(state.type_identifier)
        path = self.to_path(
            state.query, prefix="data_", extension=t.default_extension()
        )
        with open(path, "wb") as f:
            try:
                b, mime = t.as_bytes(state.data)
                f.write(self.encode(b))
            except NotImplementedError:
                return False
        return True

    def store_metadata(self, metadata):
        try:
            with open(self.to_path(metadata["query"]), "wb") as f:
                f.write(self.encode_metadata(json.dumps(metadata)))
        except:
            logging.exception(f"Cache writing error: {metadata['query']}")
            return False
        return True

    def __str__(self):
        return f"File cache at {self.path}"

    def __repr__(self):
        return f"FileCache('{self.path}')"


class StoreCache(CacheMixin):
    """Simple cache similar to FileCache, but using a store module instead of a local filesystem."""

    def __init__(self, store, path, flat=False):
        self.storage = store
        self.path = path
        if not self.storage.is_dir(path):
            self.storage.makedir(path)
        self.flat = flat

    def clean(self):
        import glob

        print(f"Clean {self}")
        path = "" if self.path in (None, "") else self.path + "/"
        for key in self.storage.keys():
            if not self.storage.is_dir(key) and key.startswith(path):
                logging.debug(f"Removing cache file {key}")
                self.storage.remove(key)
        for _, key in sorted((-len(k.split("/")), k) for k in self.storage.keys()):
            if self.storage.is_dir(key) and key.startswith(path):
                try:
                    logging.debug(f"Removing cache dir {key}")
                    self.storage.removedir(key)
                except:
                    logging.debug(f"Failed to remove cache dir {key}")

    def to_path(self, key, prefix="0state_"):
        "Construct file path from a key and optionally prefix and file extension."
        if self.flat:
            m = hashlib.md5()
            m.update(key.encode("utf-8"))
            digest = m.hexdigest()
            path = f"{self.path}/{prefix}{digest}.data"
        else:
            path = f"{self.path}/{key}/{prefix}.data"
        if path.startswith("/"):
            path = path[1:]
        return path

    def encode(self, b):
        return b

    def decode(self, s):
        return s

    def encode_metadata(self, b):
        return self.encode(b.encode("utf-8"))

    def decode_metadata(self, s):
        s = self.decode(s)
        if isinstance(s, str):
            return s
        elif isinstance(s, bytes):
            return s.decode("utf-8")
        else:
            raise Exception(f"Unsupported type: {type(s)}")

    def get(self, key):
        print(f"GET {key}")
        metadata = self.get_metadata(key)
        print(f"  METADATA {metadata}")
        if metadata is None:
            print(f"(StoreCache) Metadata missing: {key}")
            return None
        if metadata.get("status") != "ready":
            print(f"(StoreCache) Not ready {key}; ", metadata.get("status"))
            return None
        state = State()
        state.metadata = metadata

        t = state_types_registry().get(metadata["type_identifier"])
        path = self.to_path(key)
        if self.storage.contains(path):
            try:
                state.data = t.from_bytes(self.decode(self.storage.get_bytes(path)))
                return state
            except:
                traceback.print_exc()
                logging.exception(f"Cache failed to recover {key}")
                return None

    def _load_metadata(self, state_path):
        if self.storage.contains(state_path) and not self.storage.is_dir(state_path):
            return self.storage.get_metadata(state_path)

    def get_metadata(self, key):
        return self._load_metadata(self.to_path(key))

    def remove(self, key):
        try:
            self.storage.remove(self.to_path(key))
            return True
        except:
            traceback.print_exc()
            return False

    def contains(self, key):
        state_path = self.to_path(key)
        return self.storage.contains(state_path)

    def keys(self):
        path = self.path + "/"
        for key in self.storage.keys():
            if self.path in ("", None) or key.startswith(path):
                if not self.storage.is_dir(key):
                    metadata = self.storage.get_metadata(key)
                    if "query" in metadata:
                        yield metadata["query"]

    def store(self, state):
        if state.is_error:
            return None
        state.metadata["status"] = "ready"

        t = state_types_registry().get(state.type_identifier)
        path = self.to_path(state.query)
        if self.storage.is_supported(path):
            try:
                b, mime = t.as_bytes(state.data)
                metadata = dict(**state.metadata)
                metadata["mimetype"] = mime
                self.storage.store(path, b, metadata)
                return True
            except:
                return False
        return False

    def store_metadata(self, metadata):
        try:
            key = self.to_path(metadata["query"])
            if self.storage.is_supported(key):
                self.storage.store_metadata(key, metadata)
                return True
        except:
            logging.exception(f"Cache metadata storing error: {metadata['query']}")
            return False
        return False

    def __str__(self):
        return f"Store cache at {self.path} based on {self.storage}"

    def __repr__(self):
        return f"FileCache({repr(self.storage)}, {repr(self.path)}, flat={self.flat})"


class XORFileCache(FileCache):
    def __init__(self, path, code):
        super().__init__(path)
        self.code = np.frombuffer(code, dtype=np.uint8)

    def code_of_length(self, n):
        if n <= len(self.code):
            return self.code[:n]
        else:
            return np.tile(self.code, int(n / len(self.code)) + 1)[:n]

    def encode(self, b):
        ba = np.frombuffer(b, dtype=np.uint8)
        return (ba ^ self.code_of_length(len(b))).tobytes()

    def decode(self, s):
        return self.encode(s)


class FernetFileCache(FileCache):
    def __init__(self, path, fernet_key):
        from cryptography.fernet import Fernet

        super().__init__(path)
        self.fernet = Fernet(fernet_key)

    def encode(self, b):
        return self.fernet.encrypt(b)

    def decode(self, s):
        return self.fernet.decrypt(s)


class SQLCache(CacheMixin):
    """Store cache in a SQL database.
    Tested with sqlite3.
    For databases without BLOB support (e.g. Hive) use SQLStringCache.
    """

    def __init__(
        self,
        connection=None,
        table="liquer_cache",
        metadata_type="TEXT",
        state_data_type="BLOB",
        delete_before_insert=False,
        store_metadata_enabled=True,
    ):
        self.connection = connection
        self.table = table
        self.metadata_type = metadata_type
        self.state_data_type = state_data_type
        self.delete_before_insert = delete_before_insert
        self._available_keys = None
        self.store_metadata_enabled = store_metadata_enabled
        self.init()

    def init(self):
        try:
            query = f"""CREATE TABLE {self.table} (
                query         VARCHAR(2000),
                metadata      {self.metadata_type},
                state_data    {self.state_data_type}
            )
            """
            print(query)
            logging.debug(f"CACHE TABLE: {query}")
            c = self.connection.cursor()
            c.execute(query)
        except:
            traceback.print_exc()

    @classmethod
    def from_sqlite(cls, path=":memory:", table="liquer_cache"):
        import sqlite3

        connection = sqlite3.connect(path)
        return cls(connection=connection, table=table, delete_before_insert=True)

    @property
    def available_keys(self):
        if self._available_keys is None:
            c = self.connection.cursor()
            c.execute(
                f"""
            SELECT
              query
            FROM {self.table}
            """
            )

            try:
                self._available_keys = [x[0] for x in c.fetchall()]
            except:
                traceback.print_exc()
                print("SQL available_keys failed")
                return None
        return self._available_keys

    def clean(self):
        c = self.connection.cursor()
        c.execute(f"""DROP TABLE {self.table}""")
        self._available_keys = []
        self.init()
        self.connection.commit()

    def encode(self, b):
        return b

    def decode(self, s):
        return s

    def get(self, key):
        c = self.connection.cursor()
        c.execute(
            f"""
        SELECT
          metadata,
          state_data
        FROM {self.table}
        WHERE query=?
        """,
            [key],
        )

        try:
            metadata, data = c.fetchone()
            metadata = json.loads(metadata)
            if metadata.get("status") != "ready":
                return None
        except:
            return None
        try:
            state = State()
            state = state.from_dict(metadata)

            t = state_types_registry().get(state.type_identifier)
            state.data = t.from_bytes(self.decode(data))
            return state
        except:
            logging.exception(f"Cache failed to recover {key}")
            return None

    def get_metadata(self, key):
        c = self.connection.cursor()
        c.execute(
            f"""
        SELECT
          metadata
        FROM {self.table}
        WHERE query=?
        """,
            [key],
        )

        try:
            (metadata,) = c.fetchone()
        except:
            return None
        try:
            return json.loads(metadata)
        except:
            logging.exception(f"Cache failed to recover metadata {key}")
            return None

    def contains(self, key):
        return key in self.available_keys

    def keys(self):
        return self.available_keys

    def store(self, state):
        if state.is_error:
            return None
        state.metadata["status"] = "ready"

        key = state.query
        metadata = json.dumps(state.as_dict())

        t = state_types_registry().get(state.type_identifier)
        try:
            b, mime = t.as_bytes(state.data)
        except NotImplementedError:
            return False
        self._available_keys = None
        if self.delete_before_insert:
            self.connection.execute(f"DELETE FROM {self.table} WHERE query=?", [key])
        self.connection.execute(
            f"INSERT INTO {self.table} (query, metadata, state_data) VALUES (?, ?, ?)",
            [key, metadata, self.encode(b)],
        )
        self.connection.commit()
        return True

    def store_metadata(self, metadata):
        if self.store_metadata_enabled:
            key = metadata["query"]
            metadata = json.dumps(metadata)

            self._available_keys = None
            if self.delete_before_insert:
                self.connection.execute(
                    f"DELETE FROM {self.table} WHERE query=?", [key]
                )
            self.connection.execute(
                f"INSERT INTO {self.table} (query, metadata, state_data) VALUES (?, ?, ?)",
                [key, metadata, None],
            )
            self.connection.commit()
            return True
        else:
            return False

    def remove(self, key):
        self.connection.execute(f"DELETE FROM {self.table} WHERE query=?", [key])
        self.connection.commit()
        return True

    def __str__(self):
        return f"SQL cache {self.table}"

    def __repr__(self):
        return f"SQLCache(table='{self.table}')"


class SQLStringCache(SQLCache):
    """Store cache in a SQL database.
    Data are encoded into string before storing in the database.
    This is suitable for databases without BLOB support (e.g. Hive).
    By default base64 encoding is used.
    To change the encoding override encode and decode methods.
    """

    def __init__(
        self,
        connection=None,
        table="liquer_cache",
        text_type="STRING",
        delete_before_insert=False,
    ):
        super().__init__(
            connection=connection,
            table=table,
            metadata_type=text_type,
            state_data_type=text_type,
            delete_before_insert=delete_before_insert,
        )

    @classmethod
    def from_sqlite(cls, path=":memory:", table="liquer_cache"):
        import sqlite3

        connection = sqlite3.connect(path)
        return cls(connection=connection, table=table, text_type="TEXT")

    def encode(self, b):
        return base64.b64encode(b)

    def decode(self, s):
        return base64.b64decode(s)

    def __str__(self):
        return f"SQL string cache {self.table}"

    def __repr__(self):
        return f"SQLStringCache(table='{self.table}')"
