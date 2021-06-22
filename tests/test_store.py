import pytest
from liquer.store import *

class TestStore:
    @pytest.fixture
    def store(self, tmpdir):
        store = FileStore(tmpdir)
        assert str(tmpdir) in str(store)
        return store

    def test_file_store_creation(self, store):
        assert list(store.keys()) == []
        assert store.contains("x") is False

    def test_file_store_basic(self, store):
        assert list(store.keys()) == []
        assert store.contains("a") is False
        assert store.contains("a/b") is False
        store.store("a/b",b"test",dict(x="xx"))
        assert store.contains("a") is True
        assert store.contains("a/b") is True
        assert store.is_dir("a") is True
        assert store.is_dir("a/b") is False
        assert store.get_bytes("a/b") == b"test"
        assert store.get_metadata("a/b")["x"] == "xx"
        assert store.get_metadata("a")["fileinfo"]["is_dir"] == True
        assert sorted(store.keys()) == ["a","a/b"]
        assert store.listdir("a") == ["b"]
        assert store.listdir("") == ["a"]
        store.remove("a/b")
        assert store.contains("a/b") is False
        assert store.listdir("a") == []
        store.removedir("a")
        assert store.contains("a") is False
        assert list(store.keys()) == []
        assert store.listdir("") == []

    def test_parent_key(self, store):
        assert store.parent_key("") == None
        assert store.parent_key("a") == ""
        assert store.parent_key("a/b") == "a"

class TestMemoryStore(TestStore):
    @pytest.fixture
    def store(self, tmpdir):
        return MemoryStore()

class TestOverlayStore(TestStore):
    @pytest.fixture
    def store(self, tmpdir):
        return OverlayStore(MemoryStore(),MemoryStore())

class TestFileSystemStore(TestStore):
    @pytest.fixture
    def store(self, tmpdir):
        import fs
        return FileSystemStore(fs.open_fs('mem://'))

class TestMountPointStore:
    def test_file_store_creation(self):
        store = MountPointStore(MemoryStore())
        assert list(store.keys()) == []
        store.mount("a",MemoryStore())
        assert list(store.keys()) == ["a"]
        assert store.contains("x") is False

    def test_file_store_basic(self):
        store = MountPointStore(MemoryStore())
        assert list(store.keys()) == []
        assert store.contains("a") is False
        store.mount("a",MemoryStore())
        assert list(store.keys()) == ["a"]
        assert store.contains("a") is True
        assert store.contains("a/b") is False
        store.store("a/b",b"test",dict(x="xx"))
        assert store.contains("a") is True
        assert store.contains("a/b") is True
        assert store.is_dir("a") is True
        assert store.is_dir("a/b") is False
        assert store.get_bytes("a/b") == b"test"
        assert store.get_metadata("a/b")["x"] == "xx"
        assert store.get_metadata("a")["fileinfo"]["is_dir"] == True
        assert sorted(store.keys()) == ["a","a/b"]
        assert store.listdir("a") == ["b"]
        assert store.listdir("") == ["a"]
        store.remove("a/b")
        assert store.contains("a/b") is False
        assert store.listdir("a") == []
        with pytest.raises(StoreException):
            store.removedir("a")
        assert store.contains("a") is True
        assert list(store.keys()) == ["a"]
        assert store.listdir("") == ["a"]
