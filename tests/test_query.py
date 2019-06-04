#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer State object.
'''
import pytest
from liquer.query import *
from liquer.commands import command, first_command, reset_command_registry


class TestQuery:
    def test_evaluate(self):
        @first_command
        def abc():
            return 123
        assert evaluate("abc").get() == 123

    def test_cache_control(self):
        from liquer.cache import MemoryCache, set_cache, get_cache
        @command
        def cached(state):
            return state.with_caching(True).with_data(123)

        @command
        def cache_off(state):
            return state.with_caching(False).with_data(234)

        set_cache(MemoryCache())

        assert evaluate("cached").get() == 123
        assert evaluate("cache_off").get() == 234
        assert get_cache().contains("cached")
        assert not get_cache().contains("cache_off")
        set_cache(None)
        reset_command_registry()
