#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer metadata.
"""
import pytest
from liquer.metadata import Metadata, get_stored_metadata


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


