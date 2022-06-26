#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer metadata.
"""
import pytest
from liquer.metadata import Metadata, StoreSyncMetadata
from liquer.tools import get_stored_metadata


class TestMetadata:
    def test_create(self):
        m = Metadata()
        assert "status" in m.as_dict()
    def test_get_stored_metadata(self):
        from liquer.store import set_store, MemoryStore
        from liquer.cache import set_cache, MemoryCache, NoCache
        store = MemoryStore()
        store.store_metadata("a/b",dict(test="stored value 1"))
        set_store(store)

        cache = MemoryCache()
        cache.store_metadata(dict(query="c/d", test="stored value 2"))
        set_cache(cache)
        assert get_stored_metadata("-R/a/b")["test"] == "stored value 1"
        assert get_stored_metadata("a/b") is None # this represents a query
        assert get_stored_metadata("c/d")["test"] == "stored value 2"

        set_store(None)
        set_cache(NoCache())

    def test_updated(self):
        class MyMetadata(Metadata):
            UPDATED=0
            def updated(self):
                self.UPDATED+=1
        m = MyMetadata()

        assert m.UPDATED == 0
        m.info("Hello")
        assert m.UPDATED == 2

    def test_storing(self):
        import liquer.store as st
        store = st.MemoryStore()
        m = StoreSyncMetadata(store, "a/b")
        assert store.get_metadata("a/b")["key"] == "a/b"
        assert "Hello" not in [x["message"] for x in store.get_metadata("a/b")["log"]]
        m.info("Hello")
        assert "Hello" in [x["message"] for x in store.get_metadata("a/b")["log"]]



