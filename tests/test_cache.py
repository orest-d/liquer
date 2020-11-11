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

        cache.clean()
        assert not cache.contains("abc")
        assert cache.get("abc") == None


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

        cache.clean()
        assert not cache.contains("abc")
        assert cache.get("abc") == None


    def test_sqlite(self):
        state = State().with_data(123)
        state.query = "abc"
        cache = SQLCache.from_sqlite()
        assert not cache.contains("abc")
        cache.store(state)

        assert cache.contains("abc")
        assert cache.get("abc").get() == 123

        assert not cache.contains("xyz")
        assert cache.get("xyz") == None

        cache.clean()
        assert not cache.contains("abc")
        assert cache.get("abc") == None

    def test_sqlite_string(self):
        state = State().with_data(123)
        state.query = "abc"
        cache = SQLStringCache.from_sqlite()
        assert not cache.contains("abc")
        cache.store(state)

        assert cache.contains("abc")
        assert cache.get("abc").get() == 123

        assert not cache.contains("xyz")
        assert cache.get("xyz") == None

        cache.clean()
        assert not cache.contains("abc")
        assert cache.get("abc") == None


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

            cache.clean()
            assert not cache.contains("abc")
            assert cache.get("abc") == None

    def test_xorfilecache(self):
        state = State().with_data(123)
        state.query = "abc"
        with tempfile.TemporaryDirectory() as cachepath:
            cache = XORFileCache(cachepath, b"**")
            assert not cache.contains("abc")
            cache.store(state)

            assert cache.contains("abc")
            assert cache.get("abc").get() == 123

            assert not cache.contains("xyz")
            assert cache.get("xyz") == None

            cache.clean()
            assert not cache.contains("abc")
            assert cache.get("abc") == None

    def test_cached_part(self):
        cache = MemoryCache()
        state, remainder = cached_part("abc", cache)
        assert remainder == "abc"
        assert state.get() == None

        state = State().with_data(123)
        state.query = "abc"
        cache.store(state)
        state, remainder = cached_part("abc", cache)
        assert remainder == ""
        assert state.get() == 123

        state, remainder = cached_part("/abc/def", cache)
        assert remainder == "def"
        assert state.get() == 123

    def test_cached_part_nocache(self):
        cache = NoCache()
        state, remainder = cached_part("abc", cache)
        assert remainder == "abc"
        assert state.get() == None

        state = State().with_data(123)
        state.query = "abc"
        cache.store(state)
        state, remainder = cached_part("/abc/", cache)
        assert remainder == "abc"
        assert state.get() == None

        state, remainder = cached_part("/abc/def/", cache)
        assert remainder == "abc/def"
        assert state.get() == None

    def test_cache_rules(self):
        from liquer import evaluate, first_command
        cache1 = MemoryCache()
        cache2 = MemoryCache()
        cache3 = MemoryCache()

        set_cache(cache1.if_contains("abc") + cache2.if_not_contains("xyz") + cache3)
        @first_command(abc=True)
        def command1():
            return "C1"

        @first_command(xyz=True)
        def command2():
            return "C2"

        @first_command
        def command3():
            return "C3"

        evaluate("command1")
        evaluate("command2")
        evaluate("command3")

        assert "command1" in cache1.storage
        assert "command1" not in cache2.storage
        assert "command1" not in cache3.storage
        assert cache1.storage["command1"].get() == "C1"

        assert "command2" not in cache1.storage
        assert "command2" not in cache2.storage
        assert "command2" in cache3.storage
        assert cache3.storage["command2"].get() == "C2"

        assert "command3" not in cache1.storage
        assert "command3" in cache2.storage
        assert "command3" not in cache3.storage
        assert cache2.storage["command3"].get() == "C3"

        set_cache(None)
 
    def test_cache_attribute_equality_rules(self):
        from liquer import evaluate, first_command
        cache1 = MemoryCache()
        cache2 = MemoryCache()
        cache3 = MemoryCache()

        set_cache(cache1.if_attribute_equal("abc",123) + cache2.if_attribute_not_equal("xyz",456) + cache3)
        @first_command(abc=123)
        def command1a():
            return "C1"

        @first_command(xyz=456)
        def command2a():
            return "C2"

        @first_command
        def command3a():
            return "C3"

        evaluate("command1a")
        evaluate("command2a")
        evaluate("command3a")

        assert "command1a" in cache1.storage
        assert "command1a" not in cache2.storage
        assert "command1a" not in cache3.storage
        assert cache1.storage["command1a"].get() == "C1"

        assert "command2a" not in cache1.storage
        assert "command2a" not in cache2.storage
        assert "command2a" in cache3.storage
        assert cache3.storage["command2a"].get() == "C2"

        assert "command3a" not in cache1.storage
        assert "command3a" in cache2.storage
        assert "command3a" not in cache3.storage
        assert cache2.storage["command3a"].get() == "C3"

        set_cache(None)
