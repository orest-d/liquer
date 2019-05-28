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
        cache.store(state)
        assert cache.get("abc") == None

    def test_memory(self):
        state = State().with_data(123)
        state.query = "abc"
        cache = MemoryCache()
        cache.store(state)
        assert cache.get("abc").get() == 123

    def test_filecache(self):
        state = State().with_data(123)
        state.query = "abc"
        with tempfile.TemporaryDirectory() as cachepath:
            cache = FileCache(cachepath)
            cache.store(state)
            assert cache.get("abc").get() == 123

