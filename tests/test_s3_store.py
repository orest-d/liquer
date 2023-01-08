import pytest
from liquer.store import *
from liquer.s3_store import *


class TestStore:
    @pytest.fixture
    def store(self):
        store = S3Store(bucket_name="liquertest")
        for s3key in store.object_keys():
            print(f"Delete S3 object {s3key} (data)")
            store.s3_resource.Object(bucket_name=store.bucket_name, key=s3key).delete()
        for s3key in store.metadata_object_keys():
            print(f"Delete S3 object {s3key} (metadata)")
            store.s3_resource.Object(bucket_name=store.bucket_name, key=s3key).delete()
        return store

    def test_file_store_creation(self, store):
        assert list(store.keys()) == []
        assert store.contains("x") is False

    def test_file_store_basic(self, store):
        assert list(store.keys()) == []
        assert store.contains("a") is False
        assert store.contains("a/b") is False
        store.store("a/b", b"test", dict(x="xx"))
        assert store.contains("a") is True
        assert store.contains("a/b") is True
        assert store.is_dir("a") is True
        assert store.is_dir("a/b") is False
        assert store.get_bytes("a/b") == b"test"
        assert store.get_metadata("a/b")["x"] == "xx"
        assert store.get_metadata("a")["fileinfo"]["is_dir"] == True
        assert store.get_metadata("a/b")["fileinfo"]["is_dir"] == False
        assert sorted(store.keys()) == ["a", "a/b"]
        assert store.listdir("a") == ["b"]
        assert store.listdir("") == ["a"]
        store.remove("a/b")
        assert store.contains("a/b") is False
        assert store.listdir("a") == []
        store.removedir("a")
        assert store.contains("a") is False
        assert list(store.keys()) == []
        assert store.listdir("") == []
        store.sync()

    def test_parent_key(self, store):
        assert store.parent_key("") == None
        assert store.parent_key("a") == ""
        assert store.parent_key("a/b") == "a"

    def test_read_only(self, store):
        assert list(store.keys()) == []
        store.store("a/b", b"test", dict(x="xx"))
        ro = store.read_only()
        assert ro.contains("a") is True
        assert ro.contains("a/b") is True

        assert ro.is_dir("a") is True
        assert ro.is_dir("a/b") is False
        assert ro.get_bytes("a/b") == b"test"
        assert ro.get_metadata("a/b")["x"] == "xx"
        assert ro.get_metadata("a")["fileinfo"]["is_dir"] == True
        assert ro.get_metadata("a/b")["fileinfo"]["is_dir"] == False
        assert sorted(ro.keys()) == ["a", "a/b"]
        assert ro.listdir("a") == ["b"]
        assert ro.listdir("") == ["a"]
        with pytest.raises(ReadOnlyStoreException):
            ro.remove("a/b")
        with pytest.raises(ReadOnlyStoreException):
            ro.removedir("a")
        with pytest.raises(ReadOnlyStoreException):
            ro.store("a/c", b"test", dict(x="xx"))
        with pytest.raises(ReadOnlyStoreException):
            ro.store_metadata("a/d", dict(x="xx"))

    def test_to_root_key(self, store):
        memory_store = MemoryStore()
        s = store.mount("x", memory_store)
        assert memory_store.to_root_key("y") == "x/y"

    def test_root_store(self, store):
        memory_store = MemoryStore()
        s = store.mount("x", memory_store)
        assert memory_store.to_root_key("y") == "x/y"
        memory_store.root_store().store(memory_store.to_root_key("y"), b"test1", {})
        assert s.get_bytes("x/y") == b"test1"
        assert memory_store.get_bytes("y") == b"test1"
