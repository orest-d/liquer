from os import makedirs, name, remove
from pathlib import Path
import json
from io import BytesIO
from liquer.constants import *
import liquer.util as util

STORE = None
WEB_STORE = None

def get_store():
    global STORE
    if STORE is None:
        STORE = MountPointStore()
    return STORE


def set_store(store):
    global STORE
    STORE = store

def get_web_store():
    global WEB_STORE
    if WEB_STORE is None:
        WEB_STORE = MountPointStore()
        get_store().mount("web", WEB_STORE)
    return WEB_STORE

def mount(key, store):
    get_store().mount(key, store)

def web_mount(key, store):
    get_web_store().mount(key, store)

def web_mount_folder(key, path):
    web_mount(key, FileStore(path))

class StoreException(Exception):
    def __init__(self, message, key=None, store=None):
        self.original_message = message
        if key is not None:
            message += f":\n  key: {key}"
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


class StoreMixin:
    def with_overlay(self, overlay):
        return OverlayStore(overlay, self)

    def with_fallback(self, fallback):
        return OverlayStore(self, fallback)

    def mount(self, key, store):
        return MountPointStore(self).mount(key, store)

class Store(StoreMixin):
    def parent_key(self, key):
        if key == "":
            return None
        return "/".join(key.split("/")[:-1])

    def key_name(self, key):
        if key in ("", None):
            return ""
        return str(key.split("/")[-1])

    def default_metadata(self, key, is_dir=False):
        if key is None:
            key = ""

        return dict(
            key=key,
            fileinfo=dict(name=self.key_name(key), is_dir=is_dir, filesystem_path=None),
        )

    def finalize_metadata(self, metadata, key, is_dir=False, data=None):
        if key is None:
            key = ""
        metadata["key"] = key
        metadata["updated"]=util.now()
        if data is not None:
            metadata["created"]=metadata["updated"]
        metadata["fileinfo"] = metadata.get("fileinfo", {})
        metadata["fileinfo"]["name"] = self.key_name(key)
        metadata["fileinfo"]["is_dir"] = is_dir
        metadata["fileinfo"]["filesystem_path"] = metadata["fileinfo"].get(
            "filesystem_path"
        )
        if data is not None:
            metadata["fileinfo"]["size"] = len(data)

        if "mimetype" not in metadata:
            v = self.key_name(key).split(".")
            mimetype = mimetype_from_extension(v[-1]) if len(v)>1 else "application/octet-stream"
            metadata["mimetype"]=mimetype
                
        return metadata

    def get_bytes(self, key):
        raise KeyNotFoundStoreException(key=key, store=self)

    def get_metadata(self, key):
        raise KeyNotFoundStoreException(key=key, store=self)

    def store(self, key, data, metadata):
        raise KeyNotSupportedStoreException(key=key, store=self)

    def store_metadata(self, key, metadata):
        raise KeyNotSupportedStoreException(key=key, store=self)

    def remove(self, key):
        raise KeyNotFoundStoreException(key=key, store=self)

    def removedir(self, key):
        raise KeyNotFoundStoreException(key=key, store=self)

    def contains(self, key):
        return key == ""

    def is_dir(self, key):
        return key == ""

    def keys(self):
        return []

    def listdir(self, key):
        return []

    def makedir(self, key):
        raise KeyNotSupportedStoreException(key=key, store=self)

    def openbin(self, key, mode="r", buffering=-1):
        raise KeyNotSupportedStoreException(key=key, store=self)

    def is_supported(self, key):
        return False

    def on_data_changed(self, key):
        pass

    def on_metadata_changed(self, key):
        pass

    def on_removed(self, key):
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

    def finalize_metadata(self, metadata, key, is_dir=False, data=None):
        metadata = super().finalize_metadata(
            metadata, key=key, is_dir=is_dir, data=data
        )
        metadata["fileinfo"]["filesystem_path"] = str(self.path_for_key(key))
        return metadata

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
        return open(self.path_for_key(key), "rb").read()

    def get_metadata(self, key):
        p = self.path_for_key(key)
        metadata = self.default_metadata(key, p.is_dir())

        if p.is_dir():
            return self.finalize_metadata(metadata, key=key, is_dir=True)
        else:
            if self.path_for_key(key).exists():
                if self.metadata_path_for_key(key).exists():
                    metadata.update(
                        json.loads(open(self.metadata_path_for_key(key)).read())
                    )
            else:
                if self.metadata_path_for_key(key).exists():
                    metadata.update(
                        json.loads(open(self.metadata_path_for_key(key)).read())
                    )
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
        return self.path_for_key(key).exists()

    def is_dir(self, key):
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
            return sorted(set(k.split("/")[0] for k in self.keys() if k.split("/")[0]!=""))
        if self.is_dir(key):
            return [self.key_name(k) for k in self.keys() if self.parent_key(k) == key]

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
    """Proxy to another store - can be used as a basis to override certain behaviour
    """

    def __init__(self, store):
        self._store = store

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
        self._store.keys()

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
        raise KeyNotSupportedStoreException(key=key, store=self)

    def finalize_metadata(self, metadata, key, is_dir=False, data=None):
        metadata = super().finalize_metadata(
            metadata, key=key, is_dir=is_dir, data=data
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
        metadata=self.route_to(key).get_metadata(key)
        metadata["key"]=key
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

    def translate_key(self, key, inverse=False):
        return key

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
        metadata=self.substore.get_metadata(self.translate_key(key))
        metadata["key"]= key
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
        self.routing_table = [] if routing_table is None else routing_table

    def umount(self, umount_key):
        self.routing_table = [(key, store) for key, store in self.routing_table if key!=umount_key]
        return self

    def mount(self, key, store):
        self.umount(key)
        self.routing_table.append((key, PrefixStore(store, prefix=key)))
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
        store = self.route_to(key)
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
                    metadata.update(
                        json.loads(self.fs.readtext(self.metadata_path_for_key(key)))
                    )
            else:
                if self.fs.exists(self.metadata_path_for_key(key)):
                    metadata.update(
                        json.loads(self.fs.readtext(self.metadata_path_for_key(key)))
                    )
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
        return self.fs.exists(self.path_for_key(key))

    def is_dir(self, key):
        return self.fs.isdir(self.path_for_key(key))

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
                self.key_name(d)
                for d in self.fs.listdir(self.path_for_key(key))
                if self.key_name(d) != self.METADATA
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
