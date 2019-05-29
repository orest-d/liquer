#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer State object.
'''
import pytest
from liquer.cache import *
from liquer.state import State
import tempfile


class TestCache:
    def test_nocache(self):
        state = State().with_data(123)
        state.query = "abc"
        cache = NoCache()
        assert not cache.contains("abc")
        cache.store(state)

        assert not cache.contains("abc")
        assert cache.get("abc") == None

        assert not cache.contains("xyz")
        assert cache.get("xyz") == None

    def test_memory(self):
        state = State().with_data(123)
        state.query = "abc"
        cache = MemoryCache()
        assert not cache.contains("abc")
        cache.store(state)

        assert cache.contains("abc")
        assert cache.get("abc").get() == 123

        assert not cache.contains("xyz")
        assert cache.get("xyz") == None

    def test_filecache(self):
        state = State().with_data(123)
        state.query = "abc"
        with tempfile.TemporaryDirectory() as cachepath:
            cache = FileCache(cachepath)
            assert not cache.contains("abc")
            cache.store(state)

            assert cache.contains("abc")
            assert cache.get("abc").get() == 123

            assert not cache.contains("xyz")
            assert cache.get("xyz") == None

