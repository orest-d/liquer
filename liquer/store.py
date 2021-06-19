from os import makedirs, name, remove
from pathlib import Path
import json
from io import BytesIO

STORE=None
def get_store():
    global STORE
    if STORE is None:
        STORE = Store()
    return STORE

def set_store(store):
    global STORE
    STORE = store

   
class Store:
    def parent_key(self, key):
        if key == "":
            return None
        return "/".join(key.split("/")[:-1])

    def key_name(self, key):
        return key.split("/")[-1]

    def get_bytes(self, key):
        return None

    def get_metadata(self, key):
        return None

    def store(self, key, data, metadata):
        pass

    def store_metadata(self, key, metadata):
        pass

    def remove(self, key):
        pass

    def removedir(self, key):
        pass

    def contains(self, key):
        return False

    def is_dir(self, key):
        return key == ""

    def keys(self):
        return []

    def listdir(self, key):
        return []

    def makedir(self, key):
        pass

    def openbin(self, key, mode="r", buffering=-1):
        return None

    def __str__(self):
        return f"Empty store"

    def __repr__(self):
        return f"Store()"

class FileStore(Store):
    METADATA = "__metadata__"
    def __init__(self, path):
        if isinstance(path,Path):
            self.path = path
        else:
            self.path = Path(path)
    
    def path_for_key(self, key):
        if key in (None,""):
            return self.path
        p = self.path / key
        assert p.name != self.METADATA            
        return p

    def metadata_path_for_key(self, key):
        p = self.path / key
        assert p.name != self.METADATA
        return p.parent / self.METADATA / p.name

    def get_bytes(self, key):
        return open(self.path_for_key(key), "rb").read()

    def get_metadata(self, key):
        p = self.path_for_key(key)
        if p.is_dir():
            return dict(key=key, fileinfo=dict(name=p.name, is_dir=True))
        else:
            metadata = json.loads(open(self.metadata_path_for_key(key)).read())
            metadata["key"] = key
            metadata["fileinfo"]=dict(name=Path(p.name, is_dir = False))
            return metadata

    def store(self, key, data, metadata):
        self.path_for_key(key).parent.mkdir(parents=True, exist_ok=True)
        self.path_for_key(key).write_bytes(data)
        self.store_metadata(key, metadata)

    def store_metadata(self, key, metadata):
        self.metadata_path_for_key(key).parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_path_for_key(key), "w") as f:
            json.dump(metadata, f)

    def remove(self, key):
        self.path_for_key(key).unlink(missing_ok=True)
        self.metadata_path_for_key(key).unlink(missing_ok=True)

    def removedir(self, key):
        (self.path_for_key(key) / self.METADATA).rmdir()
        self.path_for_key(key).rmdir()

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
            return [d.name for d in self.path_for_key(key).iterdir() if d.name != self.METADATA]
            
    def makedir(self, key):
        self.path_for_key(key).mkdir(parents=True, exist_ok=True)
        (self.path_for_key(key) / self.METADATA).mkdir(parents=True, exist_ok=True)

    def openbin(self, key, mode="rb", buffering=-1):
        mode = dict(r="rb", w="wb").get(mode, mode)

        return open(self.path_for_key(key), mode)

    def __str__(self):
        return f"File store at {self.path}"

    def __repr__(self):
        return f"FileStore('self.path')"


class MemoryStore(Store):
    def __init__(self):
        self.directories = set()
        self.data = {}
        self.metadata = {}
    
    def get_bytes(self, key):
        return self.data[key]

    def get_metadata(self, key):
        if self.is_dir(key):
            if key in ("",None):
                return dict(key="", fileinfo=dict(name="", is_dir=True))
            else:
                return dict(key=key, fileinfo=dict(name="/".split(key)[-1], is_dir=True))
        else:
            return self.metadata[key]

    def store(self, key, data, metadata):
        self.makedir(self.parent_key(key))
        self.data[key]=data
        self.metadata[key]=metadata

    def store_metadata(self, key, metadata):
        self.metadata[key]=metadata

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

    def removedir(self, key):
        if len(self.listdir(key))==0:
            try:
                self.directories.remove(key)
            except KeyError:
                pass

    def contains(self, key):
        return key in self.directories or key in self.data or key in self.metadata

    def is_dir(self, key):
        return key in self.directories

    def keys(self):
        k = set()
        k.update(self.directories)
        k.update(self.data.keys())
        k.update(self.metadata.keys())
        return sorted(k)

    def listdir(self, key):
        if key in ("",None):
            return sorted(set(k.split("/")[0] for k in self.keys()))
        if self.is_dir(key):
            return [self.key_name(k) for k in self.keys() if self.parent_key(k)==key]
            
    def makedir(self, key):
        while key not in (None, ""):
            self.directories.add(key)
            key = self.parent_key(key)

    def openbin(self, key, mode="r", buffering=-1):
        mode = dict(r="rb", w="wb").get(mode, mode)
        if mode == "rb":
            return BytesIO(self.data[key])
        raise Exception("openbin not supported for write yet")

    def __str__(self):
        return f"Memory store"

    def __repr__(self):
        return f"MemoryStore()"