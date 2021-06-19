#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer State object.
'''
import pytest
from liquer.query import *
from liquer.commands import command, first_command, reset_command_registry, ArgumentParserException


class TestQuery:
    def test_evaluate(self):
        @first_command
        def abc():
            return 123
        assert evaluate("abc").get() == 123

    def test_parse_error(self):
        @first_command
        def intpar(x=0):
            return 123
        with pytest.raises(Exception):
            evaluate("intpar-abc").get()

    def test_evaluate_with_context(self):
        @first_command
        def cc(context=None, x=123):
            return f"{context.raw_query}:{x}"
        assert evaluate("cc").get() == "cc:123"

    def test_cache_control(self):
        from liquer.cache import MemoryCache, set_cache, get_cache
        @first_command
        def cached(context):
            context.enable_cache()
            return 123

        @command
        def cache_off(x, context):
            context.disable_cache()
            return 234

        set_cache(MemoryCache())

        assert evaluate("cached").get() == 123
        assert evaluate("cache_off").get() == 234
        assert get_cache().contains("cached")
        assert not get_cache().contains("cache_off")
        set_cache(None)
        reset_command_registry()

    def test_find_queries_in_template(self):
        assert list(find_queries_in_template("", "(", ")")) == [("", None)]
        assert list(find_queries_in_template(
            "abc", "(", ")")) == [("abc", None)]
        assert list(find_queries_in_template(
            "abc(def)ghi", "(", ")")) == [("abc","def"),("ghi",None)]
        assert list(find_queries_in_template(
            "abc(def)", "(", ")")) == [("abc","def"),("",None)]
        assert list(find_queries_in_template("abc(def", "(", ")")) == [("abc(def", None)]
        assert list(find_queries_in_template(
            "abc(de)(fg)hi)", "(", ")")) == [("abc","de"), ("","fg"), ("hi)",None)]
        assert list(find_queries_in_template(
            "abc(de)x(fg)hi)", "(", ")")) == [("abc","de"), ("x","fg"), ("hi)",None)]
        assert list(find_queries_in_template(
            "abc((de))x((fg))hi))", "((", "))")) == [("abc","de"), ("x","fg"), ("hi))",None)]
        assert list(find_queries_in_template(
            "abc$de$x$fg$hi$", "$", "$")) == [("abc","de"), ("x","fg"), ("hi$",None)]
 
    def test_evaluate_template(self):
        @first_command
        def who():
            return "world"
        assert evaluate_template("Hello, $who$!") == "Hello, world!"
 
    def test_subquery(self):
        reset_command_registry()

        @first_command
        def a():
            return 123

        @first_command
        def b(context):
            return context.evaluate("a").get()*10

        state = evaluate("b") 
        assert state.get()==1230
        assert state.metadata["direct_subqueries"][0]["query"]=="a"

    def test_link(self):
        reset_command_registry()

        @first_command
        def value(x):
            return int(x)

        @command
        def add(x,y):
            return int(x)+int(y)

        assert evaluate("value-1/add-2").get()==3 
        assert evaluate("value-1/add-~X~/value-2~E").get()==3 
        assert evaluate("value-1/add-~X~add-2~E").get()==4 

    def test_link_error(self):
        reset_command_registry()

        @first_command
        def make_error():
            raise Exception("Error in make_error")

        @command
        def concat(x,y=1):
            return str(x)+str(y)

        assert evaluate("concat-2/concat-3").get()=="None23"
        with pytest.raises(Exception):
            assert evaluate("concat-4/concat-~X~concat-5/make_error~E").get()

    def test_store(self):
        import liquer.store as st 
        reset_command_registry()
        st.set_store(st.MemoryStore())
        store = st.get_store()
        store.store("a/b", b"hello", {})
        @command
        def world(data):
            return data.decode("utf-8") + " world"
        assert evaluate("a/b/-/world").get() == "hello world"

    def test_store_evaluate_and_save(self, tmpdir):
        import liquer.store as st 
        reset_command_registry()
        st.set_store(st.MemoryStore())
        store = st.get_store()
        store.store("a/b", b"hello", {})
        @command
        def world(data):
            return data.decode("utf-8") + " world"
        evaluate_and_save("a/b/-/world/hello.txt", target_directory=str(tmpdir), target_resource_directory="results")
        assert store.get_bytes("results/hello.txt") == b"hello world"
        assert open(tmpdir/"hello.txt","rb").read() == b"hello world"

    def test_store_evaluate_and_save1(self):
        import liquer.store as st 
        reset_command_registry()
        st.set_store(st.MemoryStore())
        store = st.get_store()
        store.store("a/b", b"hello", {})
        @command
        def world(data):
            return data.decode("utf-8") + " world"
        evaluate_and_save("a/b/-/world/hello.txt", target_resource_directory="results")
        assert store.get_bytes("results/hello.txt") == b"hello world"