"""Store is a flexible filesystem-like key-value store.
Stores support reading and writing of binary data and the associated metadata.
Data from the store can typically be accessed through the resource part of the query:

file/in/store.txt/-/some_command/another_command

This query is split to two parts by /-/, the first part is the resource query (file/in/store.txt),
and the second part is the standard query (some_command/another_command).
Query is interpreted as
- first read file/in/store.txt from store
- pass it as bytes to the query,
so it is equivalent to

another_command(some_command(store.get_bytes('file/in/store.txt')))

Stores can be combined and composed in various way (see e.g. mount function and method).
Various store types are supported: memory store (MemoryStore), local filesystem store (FileStore),
overlays and other. The FileSystemStore allows to mount ftp servers, zip and files via PyFilesystem2.

There is always a default main store, which can be obtained by get_store().
This is typically passed ty commands via context.store().

By convention, the folder "web" in the get_store() holds web interface and can be accessed via
/liquer/web url. 

"""
from os import makedirs, name, remove
from pathlib import Path
import json
from io import BytesIO
from liquer.constants import *
import liquer.util as util
import hashlib
from liquer.metadata import Metadata
import traceback


STORE = None
WEB_STORE = None


def get_store():
    """Get global Store
    If no store is specified, a default store is created as a MountPointStore with indexer.
    Note that This will run the global indexer whenever the data is written into the store.
    See the StoreMixin.with_indexer method and the liquer.indexer module.
    """
    global STORE
    if STORE is None:
        STORE = MountPointStore().with_indexer()
    return STORE


def set_store(store):
    "Set global Store"
    global STORE
    STORE = store


def get_web_store():
    """Web store is the store for the /web folder.
    The purpose of this folder is to be able to efficiently serve web content.

    The web store is special in several ways:
    - It must be a mount point store, since the LiQuer plugins (e.g. the liquer_gui)
      mount sub folders with web applications into it.
    - The content of the store is accessible through liquer/web (as well as via liquer/api/store/data).
    - If the key points to a directory when accessed over liquer/web, the key/index.html is served.
    """
    global WEB_STORE
    if WEB_STORE is None:
        WEB_STORE = MountPointStore()
        get_store().mount("web", WEB_STORE)
    return WEB_STORE


def mount(key, store=None):
    """Mount a sub-store into the global store under the key.
    If store argument is a string or Path, it is interpreted as a path and converted to a FileStore
    """
    if store is None:
        store = key
    if type(store) is str:
        store = FileStore(store)
    get_store().mount(key, store)


def mount_folder(key, path):
    get_store().mount(key, FileStore(path))


def web_mount(key, store=None):
    """Like mount, but mounts into the web store. (see get_web_store)"""
    if store is None:
        store = key
    if type(store) is str:
        store = FileStore(store)
    get_web_store().mount(key, store)


def web_mount_folder(key, path):
    web_mount(key, FileStore(path))


class StoreException(Exception):
    """General superclass for exceptions associated with a store"""
    def __init__(self, message, key=None, store=None):
        self.original_message = message
        if key is not None:
            k = key if store is None else store.to_root_key(key)
            message += f":\n  key: '{k}'"
        if store is not None:
            message += f"  store: {store}"

        super().__init__(message)
        self.key = key
        self.store = store


class KeyNotFoundStoreException(StoreException):
    def __init__(self, message="Key not found in store", key=None, store=None):
        super().__init__(message=message, key=key, store=store)


class KeyNotSupportedStoreException(StoreException):
    def __init__(self, message="Key not supported in store", key=None, store=None):
        super().__init__(message=message, key=key, store=store)


class KeyRouteNotFoundStoreException(StoreException):
    def __init__(self, message="Key route not found", key=None, store=None):
        super().__init__(message=message, key=key, store=store)


class ReadOnlyStoreException(StoreException):
    def __init__(self, message="Key is read only", key=None, store=None):
        super().__init__(message=message, key=key, store=store)


class StoreMixin:
    "Mixing adding extra functionality to stores."
    def with_overlay(self, overlay):
        """Create an overlay over the store.
        Overlay store will be consulted first, when the key is not supported or not found in the overlay,
        the request will be passed to the current store (self).
        Note: a.with_overlay(b) is the same as b.with_fallback(a). Both methods create an OverlayStore instance.
        """
        return OverlayStore(overlay, self)

    def with_fallback(self, fallback):
        """Create a fallback for the store.
        When the key is not supported or not found in the current store (self),
        request will be passed to fallback.
        Note: a.with_overlay(b) is the same as b.with_fallback(a). Both methods create an OverlayStore instance.
        """
        return OverlayStore(self, fallback)

    def mount(self, key, store):
        """Mount a store in a mount-point"""
        if isinstance(self, MountPointStore):
            return self.mount(key, store)
        else:
            return MountPointStore(self).mount(key, store)

    def read_only(self):
        """Create a read-only proxy for the store."""
        if isinstance(self, ReadOnlyStore):
            return self
        else:
            return ReadOnlyStore(self)

    def with_indexer(self):
        """Create a proxy store that will run indexer on each write."""
        if isinstance(self, IndexerStore):
            return self
        else:
            return IndexerStore(self)


def key_name(key):
    """Get name of the key - i.e. last component after slash.
    If key is None or empty, empty string is returned."""
    if key in ("", None):
        return ""
    return str(key.split("/")[-1])


def key_name_without_extension(key):
    """Get name without the fileextension of the key. If key is None or empty, None is returned."""
    if key in ("", None):
        return None
    v = key_name(key).split(".")
    if len(v) >= 2:
        return v[0]
    return None


def key_extension(key):
    """Get fileextension of the key. If key is None or empty, None is returned."""
    if key in ("", None):
        return None
    v = key_name(key).split(".")
    if len(v) >= 2:
        return v[-1]
    return None


def join_key(key, name):
    """Join key and name into a new key. If key is None or empty, name is returned."""
    if key in ("", None):
        return name
    else:
        if key.endswith("/"):
            return f"{key}{name}"
        else:
            return f"{key}/{name}"


def parent_key(key):
    """Parent of the key (i.e. key without the last component)"""
    if key == "":
        return None
    return "/".join(key.split("/")[:-1])


class Store(StoreMixin):
    parent_store = None
    MD5_CHECKSUM = True

    def parent_key(self, key):
        "For backwards compatibility only; use parent_key function"
        return parent_key(key)

    def key_name(self, key):
        "For backwards compatibility only; use key_name function"
        return key_name(key)

    def join_key(self, key, name):
        "For backwards compatibility only; use join_key function"
        return join_key(key, name)

    def default_metadata(self, key, is_dir=False):
        if key is None:
            key = ""

        return dict(
            key=key,
            fileinfo=dict(name=key_name(key), is_dir=is_dir, filesystem_path=None),
        )

    def finalize_metadata(self, metadata, key, is_dir=False, data=None, update=False):
        if data is not None:
            if type(data) != bytes:
                print(f"WARNING: Non-binary data for '{key}': type is {type(data)}")
        if key is None:
            key = ""
        metadata["key"] = key
        update = update or data is not None
        if update:
            metadata["updated"] = util.now()
        if data is not None:
            metadata["created"] = metadata["updated"]
        metadata["fileinfo"] = metadata.get("fileinfo", {})
        metadata["fileinfo"]["name"] = key_name(key)
        metadata["fileinfo"]["is_dir"] = is_dir
        metadata["fileinfo"]["filesystem_path"] = metadata["fileinfo"].get(
            "filesystem_path"
        )

        if data is not None:
            metadata["fileinfo"]["size"] = len(data)
            if self.MD5_CHECKSUM and type(data) == bytes:
                metadata["fileinfo"]["md5"] = hashlib.md5(data).hexdigest()

        if metadata.get("mimetype") is None:
            mimetype = mimetype_from_extension(key_extension(key))
            metadata["mimetype"] = mimetype

        if metadata.get("type_identifier") is None:
            type_identifier = type_identifier_from_extension(key_extension(key))
            metadata["type_identifier"] = type_identifier

        return Metadata(metadata).as_dict()

    def get_bytes(self, key):
        """Get data as bytes"""
        raise KeyNotFoundStoreException(key=key, store=self)

    def get_metadata(self, key):
        """Get metadata"""
        raise KeyNotFoundStoreException(key=key, store=self)

    def store(self, key, data, metadata):
        """Store data and metadata."""
        raise KeyNotSupportedStoreException(key=key, store=self)

    def store_metadata(self, key, metadata):
        """Store metadata only."""
        raise KeyNotSupportedStoreException(key=key, store=self)

    def remove(self, key):
        """Remove data and metadata associated with the key."""
        raise KeyNotFoundStoreException(key=key, store=self)

    def removedir(self, key):
        """Remove directory.
        The key must be a directory.
        It depends on the underlying store whether the directory must be empty.
        """
        raise KeyNotFoundStoreException(key=key, store=self)

    def contains(self, key):
        """Returns true if store contains the key."""
        return key == ""

    def is_dir(self, key):
        """Returns true if key is a directory."""
        return key == ""

    def keys(self):
        """List or iterator of all keys"""
        return []

    def listdir(self, key):
        """Return names inside a directory specified by key.
        To get a key, names need to be joined with the key (key/name).
        Complete keys can be obtained with the listdir_keys method.
        """
        return []

    def listdir_keys(self, key):
        """Return keys inside a directory specified by key."""
        if key in ("", None):
            return self.listdir(key)
        else:
            return [self.join_key(key, k) for k in self.listdir(key)]

    def makedir(self, key):
        "Make a directory"
        raise KeyNotSupportedStoreException(key=key, store=self)

    def openbin(self, key, mode="r", buffering=-1):
        """Return a file handle.
        This is not necessarily always well supported, but it is required to support PyFilesystem2."""
        raise KeyNotSupportedStoreException(key=key, store=self)

    def is_supported(self, key):
        """Returns true when this store supports the supplied key.
        This allows layering Stores, e.g. by with_overlay, with_fallback
        and store selectively certain data (keys) in certain stores.
        """
        return False

    def on_data_changed(self, key):
        """Event handler called when the data is changed."""
        pass

    def on_metadata_changed(self, key):
        """Event handler called when the metadata is changed."""
        pass

    def on_removed(self, key):
        """Event handler called when the data or directory is removed."""
        pass

    def to_root_key(self, key):
        """Convert local store key to a key in a root store.
        This is can be used e.g. to convert a key valid in a mounted (child) store to
        a key of a root store.
        The to_root_key(key) in the root_store() should point to the same object as key in self.
        """
        if self.parent_store is None:
            return key
        return self.parent_store.to_root_key(key)

    def root_store(self):
        """Get the root store.
        Root store is the highest level store in the store system.
        The to_root_key(key) in the root_store() should point to the same object as key in self.
        """
        if self.parent_store is None:
            return self
        return self.parent_store.root_store()

    def sync(self):
        pass

    def __str__(self):
        return f"Empty store"

    def __repr__(self):
        return f"Store()"


class FileStore(Store):
    METADATA = "__metadata__"

    def __init__(self, path):
        if isinstance(path, Path):
            self.path = path
        else:
            self.path = Path(path)

    def finalize_metadata(self, metadata, key, is_dir=False, data=None, update=False):
        metadata = super().finalize_metadata(
            metadata, key=key, is_dir=is_dir, data=data, update=update
        )
        metadata["fileinfo"]["filesystem_path"] = str(self.path_for_key(key).resolve())
        return Metadata(metadata).as_dict()

    def path_for_key(self, key):
        if key in (None, ""):
            return self.path
        p = self.path / key
        assert p.name != self.METADATA
        return p

    def metadata_path_for_key(self, key):
        p = self.path / key
        assert p.name != self.METADATA
        return p.parent / self.METADATA / (p.name + ".json")

    def get_bytes(self, key):
        if not self.path_for_key(key).exists():
            raise KeyNotFoundStoreException(key=key, store=self)
        with open(self.path_for_key(key), "rb") as f:
            b = f.read()
        return b

    def get_metadata(self, key):
        p = self.path_for_key(key)
        metadata = self.default_metadata(key, p.is_dir())

        if p.is_dir():
            return self.finalize_metadata(metadata, key=key, is_dir=True)
        else:
            if self.path_for_key(key).exists():
                if self.metadata_path_for_key(key).exists():
                    with open(self.metadata_path_for_key(key)) as f:
                        try:
                            metadata.update(json.loads(f.read()))
                        except:
                            traceback.print_exc()
                            print(f"Removing {key} due to corrupted metadata (a)")
                            self.remove(key)
                            raise KeyNotFoundStoreException(key=key, store=self)
                else:
                    m = Metadata()
                    m.status = Status.EXTERNAL
                    return self.finalize_metadata(m.as_dict(), key=key)

            else:
                if self.metadata_path_for_key(key).exists():
                    with open(self.metadata_path_for_key(key)) as f:
                        try:
                            metadata.update(json.loads(f.read()))
                        except:
                            traceback.print_exc()
                            print(f"Removing {key} due to corrupted metadata (b)")
                            self.remove(key)
                            raise KeyNotFoundStoreException(key=key, store=self)

                else:
                    raise KeyNotFoundStoreException(key=key, store=self)
        return self.finalize_metadata(metadata, key=key, is_dir=False)

    def store(self, key, data, metadata):
        self.path_for_key(key).parent.mkdir(parents=True, exist_ok=True)
        self.path_for_key(key).write_bytes(data)
        self.store_metadata(
            key, self.finalize_metadata(metadata, key=key, is_dir=False, data=data)
        )
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        self.metadata_path_for_key(key).parent.mkdir(parents=True, exist_ok=True)
        metadata = self.finalize_metadata(
            metadata, key=key, is_dir=self.is_dir(key), update=True
        )
        with open(self.metadata_path_for_key(key), "w") as f:
            json.dump(metadata, f)
        self.on_metadata_changed(key)

    def remove(self, key):
        try:
            self.path_for_key(key).unlink()
        except FileNotFoundError:
            pass
        try:
            self.metadata_path_for_key(key).unlink()
        except FileNotFoundError:
            pass

        self.on_removed(key)

    def removedir(self, key):
        (self.path_for_key(key) / self.METADATA).rmdir()
        self.path_for_key(key).rmdir()
        self.on_removed(key)

    def contains(self, key):
        if key in ("", None):
            return True
        return self.path_for_key(key).exists()

    def is_dir(self, key):
        if key in ("", None):
            return True
        return self.path_for_key(key).is_dir()

    def keys(self, parent=None):
        d = self.listdir(parent)
        if d is None:
            return []
        else:
            for k in d:
                key = k if parent is None else parent + "/" + k
                yield key
                for kk in self.keys(key):
                    yield kk

    def listdir(self, key):
        if self.is_dir(key):
            return [
                d.name
                for d in self.path_for_key(key).iterdir()
                if d.name != self.METADATA
            ]

    def makedir(self, key):
        self.path_for_key(key).mkdir(parents=True, exist_ok=True)
        (self.path_for_key(key) / self.METADATA).mkdir(parents=True, exist_ok=True)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="rb", buffering=-1):
        mode = dict(r="rb", w="wb").get(mode, mode)
        return open(self.path_for_key(key), mode)

    def is_supported(self, key):
        return True

    def __str__(self):
        return f"File store at {self.path}"

    def __repr__(self):
        return f"FileStore('{self.path}')"


class MemoryStore(Store):
    def __init__(self):
        self.directories = set()
        self.data = {}
        self.metadata = {}

    def get_bytes(self, key):
        if key not in self.data:
            raise KeyNotFoundStoreException(key=key, store=self)
        return self.data[key]

    def get_metadata(self, key):
        if key in self.metadata:
            metadata = self.metadata[key]
        else:
            if not self.is_dir(key):
                raise KeyNotFoundStoreException(key=key, store=self)

            metadata = self.default_metadata(key, is_dir=True)

        return self.finalize_metadata(metadata, key=key, is_dir=self.is_dir(key))

    def store(self, key, data, metadata):
        self.makedir(self.parent_key(key))
        self.data[key] = data
        self.metadata[key] = self.finalize_metadata(
            metadata, key=key, is_dir=False, data=data
        )
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        metadata = self.finalize_metadata(
            metadata, key=key, is_dir=self.is_dir(key), update=True
        )
        self.metadata[key] = metadata
        self.on_metadata_changed(key)

    def remove(self, key):
        try:
            self.directories.remove(key)
        except KeyError:
            pass
        try:
            del self.data[key]
        except KeyError:
            pass
        try:
            del self.metadata[key]
        except KeyError:
            pass
        self.on_removed(key)

    def removedir(self, key):
        if len(self.listdir(key)) == 0:
            try:
                self.directories.remove(key)
            except KeyError:
                pass
        self.on_removed(key)

    def contains(self, key):
        if key in ("", None):
            return True

        return key in self.directories or key in self.data or key in self.metadata

    def is_dir(self, key):
        if key in (None, ""):
            return True
        return key in self.directories

    def keys(self):
        k = set()
        k.update(self.directories)
        k.update(self.data.keys())
        k.update(self.metadata.keys())
        return sorted(k)

    def listdir(self, key):
        if key in ("", None):
            return sorted(
                set(k.split("/")[0] for k in self.keys() if k.split("/")[0] != "")
            )
        if self.is_dir(key):
            return [key_name(k) for k in self.keys() if self.parent_key(k) == key]

    def makedir(self, key):
        while key not in (None, ""):
            self.directories.add(key)
            key = self.parent_key(key)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="r", buffering=-1):
        mode = dict(r="rb", w="wb").get(mode, mode)
        if mode == "rb":
            return BytesIO(self.data[key])
        raise Exception("openbin not supported for write yet")

    def is_supported(self, key):
        return True

    def __str__(self):
        return f"Memory store"

    def __repr__(self):
        return f"MemoryStore()"


class ProxyStore(Store):
    """Proxy to another store - can be used as a basis to override certain behaviour"""

    def __init__(self, store):
        self._store = store
        self._store.parent_store = self

    def sync(self):
        self._store.sync()

    def get_bytes(self, key):
        return self._store.get_bytes(key)

    def get_metadata(self, key):
        return self._store.get_metadata(key)

    def store(self, key, data, metadata):
        self._store.store(key, data, metadata)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        self._store.store_metadata(key, metadata)
        self.on_metadata_changed(key)

    def remove(self, key):
        self._store.remove(key)
        self.on_removed(key)

    def removedir(self, key):
        self._store.remove(key)
        self.on_removed(key)

    def contains(self, key):
        return self._store.contains(key)

    def is_dir(self, key):
        return self._store.is_dir(key)

    def keys(self):
        return self._store.keys()

    def listdir(self, key):
        return self._store.listdir(key)

    def makedir(self, key):
        self._store.makedir(key)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="r", buffering=-1):
        return self._store.openbin(key, mode, buffering)

    def is_supported(self, key):
        return self._store.is_supported(key)

    def __str__(self):
        return f"proxy of {self._store}"

    def __repr__(self):
        return f"ProxyStore({repr(self._store)})"


class IndexerStore(ProxyStore):
    """Indexer proxy to another store - this will call indexer on storing."""

    def store(self, key, data, metadata):
        from liquer.indexer import index

        metadata = self._store.finalize_metadata(metadata, key=key, is_dir=False, data=data)
        metadata = index(key=self.to_root_key(key), query=metadata.get("query"), data=data, metadata=metadata)
        self._store.store(key, data, metadata)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def mount(self, key, store):
        """Mount a store in a mount-point"""
        r = self._store.mount(key, store)
        self.sync()
        return r

    def __str__(self):
        return f"Indexing {self._store}"

    def __repr__(self):
        return f"IndexerStore({repr(self._store)})"

class ReadOnlyStore(ProxyStore):
    """Read only proxy to a store"""

    def store(self, key, data, metadata):
        raise ReadOnlyStoreException(key=key, store=self)

    def store_metadata(self, key, metadata):
        raise ReadOnlyStoreException(key=key, store=self)

    def remove(self, key):
        raise ReadOnlyStoreException(key=key, store=self)

    def removedir(self, key):
        raise ReadOnlyStoreException(key=key, store=self)

    def makedir(self, key):
        raise ReadOnlyStoreException(key=key, store=self)

    def __str__(self):
        return f"read only proxy of {self._store}"

    def __repr__(self):
        return f"ReadOnlyStore({repr(self._store)})"


class OverlayStore(Store):
    """Overlay store combines two stores: overlay and fallback.
    Overlay is used as a primary store for reading and writing.
    The fallback is used only for reading if key is not found in the overlay store (and is not removed).
    Thus the fallback store is never modified.
    """

    def __init__(self, overlay, fallback):
        self.overlay = overlay
        self.fallback = fallback
        self.removed = set()

    def sync(self):
        self.overlay.sync()
        self.fallback.sync()

    def get_bytes(self, key):
        if key not in self.removed:
            if self.overlay.contains(key):
                return self.overlay.get_bytes(key)
            else:
                return self.fallback.get_bytes(key)

    def get_metadata(self, key):
        if key not in self.removed:
            if self.overlay.contains(key):
                return self.overlay.get_metadata(key)
            else:
                return self.fallback.get_metadata(key)
        raise KeyNotFoundStoreException(key=key, store=self)

    def store(self, key, data, metadata):
        try:
            self.removed.remove(key)
        except KeyError:
            pass
        self.overlay.store(key, data, metadata)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        try:
            self.removed.remove(key)
        except KeyError:
            pass
        self.overlay.store_metadata(key, metadata)
        self.on_metadata_changed(key)

    def remove(self, key):
        if key not in self.removed:
            if self.overlay.contains(key):
                self.overlay.remove(key)
            if self.fallback.contains(key):
                self.removed.add(key)
        self.on_removed(key)

    def removedir(self, key):
        if self.contains(key):
            if len(self.listdir(key)) == 0:
                if self.overlay.contains(key):
                    self.overlay.remove(key)
                else:
                    self.removed.add(key)
        self.on_removed(key)

    def contains(self, key):
        if key in self.removed:
            return False
        else:
            return self.overlay.contains(key) or self.fallback.contains(key)

    def is_dir(self, key):
        if key in self.removed:
            return False
        else:
            if self.overlay.contains(key):
                return self.overlay.is_dir(key)
            else:
                return self.fallback.is_dir(key)

    def keys(self):
        return sorted(
            set(self.overlay.keys())
            .union(self.fallback.keys())
            .difference(self.removed)
        )

    def listdir(self, key):
        if key.endswith("/"):
            key = key[:-1]
        ld = self.overlay.listdir(key)
        d = set() if ld is None else set(ld)
        ld = self.fallback.listdir(key)
        d = d if ld is None else d.union(ld)
        return [x for x in sorted(d) if key + "/" + x not in self.removed]

    def makedir(self, key):
        if key in self.removed:
            self.removed.remove(key)
        self.overlay.makedir(key)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="r", buffering=-1):
        mode = dict(r="rb", w="wb").get(mode, mode)
        if mode == "rb":
            if self.overlay.contains(key):
                return self.overlay.openbin(key, mode, buffering)
            elif self.fallback.contains(key):
                return self.fallback.openbin(key, mode, buffering)
        elif mode == "wb":
            return self.overlay.openbin(key, mode, buffering)

    def is_supported(self, key):
        return self.overlay.is_supported(key) or self.fallback.is_supported(key())

    def __str__(self):
        return f"Overlay of ({self.overlay}) over ({self.fallback})"

    def __repr__(self):
        return f"OverlayStore({repr(self.overlay)},{repr(self.fallback)})"


class RoutingStore(Store):
    def route_to(self, key):
        raise KeyRouteNotFoundStoreException(key=key, store=self)

    def finalize_metadata(self, metadata, key, is_dir=False, data=None, update=False):
        metadata = super().finalize_metadata(
            metadata, key=key, is_dir=is_dir, data=data, update=update
        )
        return metadata

    def is_supported(self, key):
        try:
            store = self.route_to(key)
            if store is None:
                return False
            return store.is_supported(key)
        except KeyNotSupportedStoreException:
            return False

    def get_bytes(self, key):
        return self.route_to(key).get_bytes(key)

    def get_metadata(self, key):
        metadata = self.route_to(key).get_metadata(key)
        metadata["key"] = key
        return metadata

    def store(self, key, data, metadata):
        self.route_to(key).store(key, data, metadata)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        self.route_to(key).store_metadata(key, metadata)
        self.on_metadata_changed(key)

    def remove(self, key):
        self.route_to(key).remove(key)
        self.on_removed(key)

    def removedir(self, key):
        self.route_to(key).removedir(key)
        self.on_removed(key)

    def contains(self, key):
        return self.route_to(key).contains(key)

    def is_dir(self, key):
        return self.route_to(key).is_dir(key)

    def keys(self):
        raise NotImplementedError

    def listdir(self, key):
        return self.route_to(key).listdir(key)

    def makedir(self, key):
        self.route_to(key).makedir(key)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="r", buffering=-1):
        return self.route_to(key).openbin(key, mode=mode, buffering=buffering)

    def __str__(self):
        return f"Abstract routing store"

    def __repr__(self):
        return f"RoutingStore()"


class KeyTranslatingStore(Store):
    def __init__(self, store):
        self.substore = store
        self.substore.parent_store = self

    def sync(self):
        self.substore.sync()

    def translate_key(self, key, inverse=False):
        return key

    def to_root_key(self, key):
        """Convert local store key to a key in a root store.
        This is can be used e.g. to convert a key valid in a mounted (child) store to
        a key of a root store.
        """
        key = self.translate_key(key, inverse=True)
        if self.parent_store is None:
            return key
        return self.parent_store.to_root_key(key)

    def is_supported(self, key):
        try:
            tkey = self.translate_key(key)
            if tkey is None:
                return False
            return self.substore.is_supported(tkey)
        except KeyNotSupportedStoreException:
            return False

    def get_bytes(self, key):
        return self.substore.get_bytes(self.translate_key(key))

    def get_metadata(self, key):
        tkey = self.translate_key(key)
        metadata = self.substore.get_metadata(tkey)
        metadata["key"] = key
        if "recipes_key" in metadata:
            metadata["recipes_key"] = self.translate_key(
                metadata["recipes_key"], inverse=True
            )
        return metadata

    def store(self, key, data, metadata):
        self.substore.store(self.translate_key(key), data, metadata)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        self.substore.store_metadata(self.translate_key(key), metadata)
        self.on_metadata_changed(key)

    def remove(self, key):
        self.substore.remove(self.translate_key(key))
        self.on_removed(key)

    def removedir(self, key):
        self.substore.removedir(self.translate_key(key))
        self.on_removed(key)

    def contains(self, key):
        return self.substore.contains(self.translate_key(key))

    def is_dir(self, key):
        return self.substore.is_dir(self.translate_key(key))

    def keys(self):
        for key in self.substore.keys():
            yield self.translate_key(key, inverse=True)

    def listdir(self, key):
        return self.substore.listdir(self.translate_key(key))

    def makedir(self, key):
        self.substore.makedir(self.translate_key(key))
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="r", buffering=-1):
        return self.substore.openbin(
            self.translate_key(key), mode=mode, buffering=buffering
        )

    def __str__(self):
        return f"Key translating store on ({self.substore})"

    def __repr__(self):
        return f"KeyTranslatingStore({repr(self.substore)})"


class PrefixStore(KeyTranslatingStore):
    def __init__(self, store, prefix):
        self.substore = store
        self.prefix = prefix
        self.substore.parent_store = self

    def translate_key(self, key, inverse=False):
        prefix = self.prefix + "/"
        if inverse:
            if key in (None, ""):
                return self.prefix
            else:
                return prefix + key
        else:
            if key == self.prefix:
                return ""
            else:
                if key.startswith(prefix):
                    return key[len(prefix) :]
                else:
                    raise KeyNotSupportedStoreException

    def contains(self, key):
        if key == self.prefix:
            return True
        return self.substore.contains(self.translate_key(key))

    def is_dir(self, key):
        if key == self.prefix:
            return True
        return self.substore.is_dir(self.translate_key(key))

    def __str__(self):
        return f"Prefixed store {self.prefix} on ({self.substore})"

    def __repr__(self):
        return f"PrefixStore({repr(self.substore)}, prefix={repr(self.prefix)})"


class MountPointStore(RoutingStore):
    def __init__(self, default_store=None, routing_table=None):
        self.default_store = default_store
        if default_store is not None:
            self.default_store.parent_store = self
        self.routing_table = [] if routing_table is None else routing_table

    def sync(self):
        for key, store in self.routing_table:
            store.sync()
        if self.default_store is not None:
            self.default_store.sync()

    def umount(self, umount_key):
        for key, store in self.routing_table:
            if key == umount_key:
                store.parent_store = None
        self.routing_table = [
            (key, store) for key, store in self.routing_table if key != umount_key
        ]
        return self

    def mount(self, key, store):
        self.umount(key)
        prefix_store = PrefixStore(store, prefix=key)
        prefix_store.parent_store = self
        self.routing_table.append((key, prefix_store))
        self.sync()
        return self

    def route_to(self, key):
        for prefix, store in reversed(self.routing_table):
            if key == prefix:
                return store
            if not prefix.endswith("/"):
                prefix += "/"
            if key.startswith(prefix):
                if store.is_supported(key):
                    return store
        if self.default_store is not None:
            return self.default_store
        raise KeyRouteNotFoundStoreException(key=key, store=self)

    def get_metadata(self, key):
        try:
            metadata = self.route_to(key).get_metadata(key)
            metadata["key"] = key

            return metadata
        except KeyRouteNotFoundStoreException:
            if self.is_dir(key):
                return self.finalize_metadata({}, key, is_dir=True)
        raise KeyNotFoundStoreException(key=key, store=self)

    def is_dir(self, key):
        if key == "":
            return True
        try:
            return self.route_to(key).is_dir(key)
        except KeyRouteNotFoundStoreException:
            for route, _ in reversed(self.routing_table):
                if route == key or route.startswith(key + "/"):
                    return self.finalize_metadata({}, key, is_dir=True)
        return False

    def keys(self):
        prefixes = []
        for prefix, store in reversed(self.routing_table):
            yield prefix
            if not prefix.endswith("/"):
                prefix += "/"
            for key in store.keys():
                if any(key.startswith(p) for p in prefixes):
                    continue
                if key.startswith(prefix):
                    yield key
            prefixes.append(prefix)
        if self.default_store is not None:
            for key in self.default_store.keys():
                if any(key.startswith(p) for p in prefixes):
                    continue
                yield key

    def listdir(self, key):
        try:
            store = self.route_to(key)
        except KeyRouteNotFoundStoreException:
            store = None

        if store is None:
            d = set()
        else:
            d = set(store.listdir(key) or [])
        key_split = key.split("/")
        if len(key_split) == 1 and key_split[0] == "":
            key_split = []
        key_depth = len(key_split)
        for prefix, _ in self.routing_table:
            if prefix.startswith(key + "/") or key in (None, ""):
                v = prefix.split("/")
                d.add(v[key_depth])
        if self.default_store is not None:
            for prefix in self.default_store.keys():
                if prefix.startswith(key + "/") or key in (None, ""):
                    v = prefix.split("/")
                    d.add(v[key_depth])

        return sorted(d)

    def removedir(self, key):
        for k, store in self.routing_table:
            if k == key:
                raise StoreException(
                    f"Can't remove {key} because it is a mount point of {repr(store)}",
                    key=key,
                    store=self,
                )

        return self.route_to(key).removedir(key)

    def __str__(self):
        return f"Mount point store routed by {self.routing_table} with default store {self.default_store}"

    def __repr__(self):
        return f"MountPointStore({repr(self.default_store)}, routing_table={repr(self.routing_table)})"


class FileSystemStore(Store):
    """A store that uses the [PyFilesystem2](https://docs.pyfilesystem.org/en/latest/) as a backend.

    Though it seems to be working fine in Linux, some issues were found in Windows.
    This seems to not work reliable due to different implementations of PyFilesystem2.
    Notably, listdir() sometimes returns list of recurently items in the subdirectories.
    
    Consider using FSSpecStore based on [fsspec](https://filesystem-spec.readthedocs.io/en/latest/),
    which should have a better support.
    """
    METADATA = "__metadata__"

    def __init__(self, fs, path=""):
        if isinstance(path, Path):
            self.path = path
        else:
            self.path = Path(path)
        self.fs = fs

    def path_for_key(self, key):
        if key in (None, ""):
            return str(self.path)
        p = self.path / key
        assert p.name != self.METADATA
        return str(p)

    def metadata_path_for_key(self, key):
        p = self.path / key
        assert p.name != self.METADATA
        return str(p.parent / self.METADATA / (p.name + ".json"))

    def metadata_dir_path_for_key(self, key):
        p = self.path / key
        assert p.name != self.METADATA
        return str(p.parent / self.METADATA)

    def get_bytes(self, key):
        if not self.fs.exists(self.path_for_key(key)):
            raise KeyNotFoundStoreException(
                f"Can't find {self.path_for_key(key)} in filesystem {self.fs}",
                key=key,
                store=self,
            )
        return self.fs.readbytes(self.path_for_key(key))

    def get_metadata(self, key):
        p = self.path_for_key(key)
        isdir = self.fs.isdir(p)
        metadata = self.default_metadata(key, isdir)
        if isdir:
            return self.finalize_metadata(metadata, key, is_dir=True)
        else:
            if self.fs.exists(self.path_for_key(key)):
                if self.fs.exists(self.metadata_path_for_key(key)):
                    try:
                        metadata.update(
                            json.loads(
                                self.fs.readtext(self.metadata_path_for_key(key))
                            )
                        )
                    except:
                        traceback.print_exc()
                        print(f"Removing {key} due to corrupted metadata (c)")
                        self.remove(key)
                        raise KeyNotFoundStoreException(key=key, store=self)

            else:
                if self.fs.exists(self.metadata_path_for_key(key)):
                    try:
                        metadata.update(
                            json.loads(
                                self.fs.readtext(self.metadata_path_for_key(key))
                            )
                        )
                    except:
                        traceback.print_exc()
                        print(f"Removing {key} due to corrupted metadata (d)")
                        self.remove(key)
                        raise KeyNotFoundStoreException(key=key, store=self)
                else:
                    raise KeyNotFoundStoreException(key=key, store=self)
            return self.finalize_metadata(metadata, key, is_dir=False)

    def store(self, key, data, metadata):
        self.fs.makedirs(self.path_for_key(self.parent_key(key)))
        self.fs.writebytes(self.path_for_key(key), data)
        assert self.fs.exists(self.path_for_key(key))
        self.store_metadata(
            key, self.finalize_metadata(metadata, key=key, is_dir=False, data=data)
        )
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        parent = self.metadata_dir_path_for_key(key)
        metadata = self.finalize_metadata(
            metadata, key=key, is_dir=self.is_dir(key), update=True
        )
        self.fs.makedirs(parent)
        with self.fs.open(self.metadata_path_for_key(key), "w") as f:
            json.dump(metadata, f)
        self.on_metadata_changed(key)

    def remove(self, key):
        if not self.contains(key):
            raise KeyNotFoundStoreException(key=key, store=self)
        if self.is_dir(key):
            raise KeyNotFoundStoreException(
                message=f"Can't remove a directory {key}; use removedir",
                key=key,
                store=self,
            )
        try:
            self.fs.remove(self.path_for_key(key))
        except:
            pass
        try:
            self.fs.remove(self.metadata_path_for_key(key))
        except:
            pass
        self.on_removed(key)

    def removedir(self, key):
        metadir = self.path_for_key(key) + "/" + self.METADATA
        try:
            self.fs.removedir(metadir)
        except:
            pass
        self.fs.removedir(self.path_for_key(key))
        self.on_removed(key)

    def contains(self, key):
        if key in ("", None):
            return True

        return self.fs.exists(self.path_for_key(key))

    def is_dir(self, key):
        if key in ("", None):
            return True
        return self.fs.isdir(self.path_for_key(key))

    def keys(self, parent=None):
        if parent is not None and key_name(parent) == self.METADATA:
            raise Exception(f"Invalid key {parent}")
        d = self.listdir(parent)
        if d is None:
            return []
        else:
            for k in d:
                k=k.replace("\\","/")
                if key_name(k) == self.METADATA:
                    continue
                key=join_key(parent, k)
                for kk in self.keys(key):
                    yield kk

    def listdir(self, key):
        if self.is_dir(key):
            listdir = [d.replace('\\','/') for d in self.fs.listdir(self.path_for_key(key)) if d is not None]
            if any("/" in d for d in listdir):
                print(f"WARNING - listdir on {repr(self)} not working properly")

            return [
                key_name(d)
                for d in listdir
                if key_name(d) != self.METADATA
                and f"/{self.METADATA}/" not in d
            ]

    def makedir(self, key):
        self.fs.makedir(self.path_for_key(key), recreate=True)
        self.fs.makedir(self.path_for_key(key) + "/" + self.METADATA, recreate=True)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="rb", buffering=-1):
        return self.fs.openbin(self.path_for_key(key), mode=mode, buffering=buffering)

    def is_supported(self, key):
        return True

    def __str__(self):
        return f"Filesystem {self.fs} store at {self.path}"

    def __repr__(self):
        return f"FileSystemStore({repr(self.fs)}, {repr(self.path)})"


class FSSpecStore(Store):
    """A store that uses the [fsspec](https://filesystem-spec.readthedocs.io/en/latest/) as a backend.
    """
    METADATA = "__metadata__"

    def __init__(self, fs, prefix:str=""):
        """Create a new FSSpecStore out of a fsspec filesystem.
        prefix needs to be provided to form a valid fsspec url when concatenating with the key (via a slash).        
        When key is "", the prefix is returned as is.
        """
        self.prefix = prefix
        self.fs = fs

    def path_for_key(self, key):
        """Convert key to a fsspec url."""
        if key in("",None):
            return self.prefix
        assert key_name(key) != self.METADATA and ("/" + self.METADATA + "/") not in key
        if key in (None, ""):
            return self.prefix
        p = self.prefix + "/" + key
        return str(p)

    def metadata_path_for_key(self, key):
        """Convert key to a fsspec url pointing to the metadata of the key."""
        return self.metadata_dir_path_for_key(key) + "/" + key_name(key) + ".json"

    def metadata_dir_path_for_key(self, key):
        if key in("",None):
            return self.prefix+"/"+self.METADATA
        assert key_name(key) != self.METADATA and ("/" + self.METADATA + "/") not in key
        p = self.path_for_key(parent_key(key))
        return p + "/" + self.METADATA

    def get_bytes(self, key):
        if not self.fs.exists(self.path_for_key(key)):
            raise KeyNotFoundStoreException(
                f"Can't find {self.path_for_key(key)} in filesystem {self.fs}",
                key=key,
                store=self,
            )
        return self.fs.read_bytes(self.path_for_key(key))

    def get_metadata(self, key):
        p = self.path_for_key(key)
        isdir = self.fs.isdir(p)
        metadata = self.default_metadata(key, isdir)
        if isdir:
            return self.finalize_metadata(metadata, key, is_dir=True)
        else:
            if self.fs.exists(self.path_for_key(key)):
                if self.fs.exists(self.metadata_path_for_key(key)):
                    try:
                        metadata.update(
                            json.loads(
                                self.fs.read_text(self.metadata_path_for_key(key))
                            )
                        )
                    except:
                        traceback.print_exc()
                        print(f"Removing {key} due to corrupted metadata (c)")
                        self.remove(key)
                        raise KeyNotFoundStoreException(key=key, store=self)

            else:
                if self.fs.exists(self.metadata_path_for_key(key)):
                    try:
                        metadata.update(
                            json.loads(
                                self.fs.read_text(self.metadata_path_for_key(key))
                            )
                        )
                    except:
                        traceback.print_exc()
                        print(f"Removing {key} due to corrupted metadata (d)")
                        self.remove(key)
                        raise KeyNotFoundStoreException(key=key, store=self)
                else:
                    raise KeyNotFoundStoreException(key=key, store=self)
            return self.finalize_metadata(metadata, key, is_dir=False)

    def store(self, key, data, metadata):
        self.fs.makedirs(self.path_for_key(self.parent_key(key)))
        self.fs.write_bytes(self.path_for_key(key), data)
        assert self.fs.exists(self.path_for_key(key))
        self.store_metadata(
            key, self.finalize_metadata(metadata, key=key, is_dir=False, data=data)
        )
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        parent = self.metadata_dir_path_for_key(key)
        metadata = self.finalize_metadata(
            metadata, key=key, is_dir=self.is_dir(key), update=True
        )
        self.fs.makedirs(parent)
        with self.fs.open(self.metadata_path_for_key(key), "w") as f:
            json.dump(metadata, f)
        self.on_metadata_changed(key)

    def remove(self, key):
        if not self.contains(key):
            raise KeyNotFoundStoreException(key=key, store=self)
        if self.is_dir(key):
            raise KeyNotFoundStoreException(
                message=f"Can't remove a directory {key}; use removedir",
                key=key,
                store=self,
            )
        try:
            self.fs.rm(self.path_for_key(key))
        except:
            pass
        try:
            self.fs.rm(self.metadata_path_for_key(key))
        except:
            pass
        self.on_removed(key)

    def removedir(self, key):
        metadir = self.path_for_key(key) + "/" + self.METADATA
        try:
            self.fs.rmdir(metadir)
        except:
            pass
        self.fs.rmdir(self.path_for_key(key))
        self.on_removed(key)

    def contains(self, key):
        if key in ("", None):
            return True

        return self.fs.exists(self.path_for_key(key))

    def is_dir(self, key):
        if key in ("", None):
            return True
        return self.fs.isdir(self.path_for_key(key))

    def keys(self, parent=None):
        if parent is not None and key_name(parent) == self.METADATA:
            raise ValueError(f"Invalid key {parent}")
        d = self.listdir(parent)
        if d is None:
            return []
        else:
            for k in d:
                if key_name(k) == self.METADATA:
                    continue                
                key = join_key(parent, k)
                yield key
                for kk in self.keys(key):
                    yield kk

    def listdir(self, key):
        if key is None:
            key = ""
        if self.is_dir(key):
            listdir = self.fs.listdir(self.path_for_key(key), detail=False)
            names=set()
            for d in listdir:
                print("  - ",d)
                if d.startswith("/"):
                    d = d[len(key)+1:]
                if d.startswith("/"):
                    d = d[1:]
                if key_name(d) != self.METADATA and f"/{self.METADATA}/" not in d and len(d) > 0:
                    print("    name: ",d.split("/")[0])
                    names.add(d.split("/")[0])
            return sorted(list(names))

    def makedir(self, key):
        self.fs.mkdir(self.path_for_key(key), recreate=True)
        self.fs.mkdir(self.path_for_key(key) + "/" + self.METADATA, recreate=True)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="rb", buffering=-1):
        return self.fs.open(self.path_for_key(key), mode=mode, buffering=buffering)

    def is_supported(self, key):
        return True

    def __str__(self):
        return f"fsspec {self.fs} store at {self.prefix}"

    def __repr__(self):
        return f"FSSpecStore({repr(self.fs)}, {repr(self.prefix)})"
