#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer State object.
"""
import pytest
from liquer.query import *
from liquer.commands import (
    command,
    first_command,
    reset_command_registry,
    ArgumentParserException,
)
from liquer.store import KeyNotFoundStoreException, set_store

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
        assert list(find_queries_in_template("abc", "(", ")")) == [("abc", None)]
        assert list(find_queries_in_template("abc(def)ghi", "(", ")")) == [
            ("abc", "def"),
            ("ghi", None),
        ]
        assert list(find_queries_in_template("abc(def)", "(", ")")) == [
            ("abc", "def"),
            ("", None),
        ]
        assert list(find_queries_in_template("abc(def", "(", ")")) == [
            ("abc(def", None)
        ]
        assert list(find_queries_in_template("abc(de)(fg)hi)", "(", ")")) == [
            ("abc", "de"),
            ("", "fg"),
            ("hi)", None),
        ]
        assert list(find_queries_in_template("abc(de)x(fg)hi)", "(", ")")) == [
            ("abc", "de"),
            ("x", "fg"),
            ("hi)", None),
        ]
        assert list(find_queries_in_template("abc((de))x((fg))hi))", "((", "))")) == [
            ("abc", "de"),
            ("x", "fg"),
            ("hi))", None),
        ]
        assert list(find_queries_in_template("abc$de$x$fg$hi$", "$", "$")) == [
            ("abc", "de"),
            ("x", "fg"),
            ("hi$", None),
        ]

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
            return context.evaluate("a").get() * 10

        state = evaluate("b")
        assert state.get() == 1230
        assert state.metadata["direct_subqueries"][0]["query"] == "a"

    def test_link(self):
        reset_command_registry()

        @first_command
        def value(x):
            return int(x)

        @command
        def add(x, y):
            return int(x) + int(y)

        assert evaluate("value-1/add-2").get() == 3
        assert evaluate("value-1/add-~X~/value-2~E").get() == 3
        assert evaluate("value-1/add-~X~add-2~E").get() == 4

    def test_resource_link(self, tmpdir):
        import liquer.store as st

        reset_command_registry()
        st.set_store(st.MemoryStore())
        store = st.get_store()
        store.store("a/b", b"hello", {})

        @command
        def world(data):
            return data.decode("utf-8") + " world"

        @first_command
        def value(x):
            return f"<{x}>"

        assert evaluate("a/b/-/world").get() == "hello world"
        assert evaluate("-R/a/b/-/world").get() == "hello world"
        assert evaluate("value-~X~-R/a/b/-/world~E").get() == "<hello world>"

    def test_link_error(self):
        reset_command_registry()

        @first_command
        def make_error():
            raise Exception("Error in make_error")

        @command
        def concat(x, y=1):
            return str(x) + str(y)

        assert evaluate("concat-2/concat-3").get() == "None23"
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

    def test_meta_store(self):
        import liquer.store as st

        reset_command_registry()
        st.set_store(st.MemoryStore())
        store = st.get_store()
        store.store("a/b", b"hello", {"x": 123})

        @command
        def world(data):
            return data.decode("utf-8") + " world"

        @command
        def get_x(metadata):
            return metadata.get("x")

        assert evaluate("-R/a/b/-/world").get() == "hello world"
        assert evaluate("-R-meta/a/b/-/get_x").get() == 123
        print(evaluate("-R-meta/a/b").get())
        assert evaluate("-R-meta/a/b").get()["key"] == "a/b"

    def test_error_message1(self):
        import traceback
        import liquer.store as st

        reset_command_registry()
        st.set_store(st.MemoryStore())
        store = st.get_store()
        store.store("a/b", b"hello", {})

        @command
        def world(data):
            return data.decode("utf-8") + " world"

        assert evaluate("a/b/-/world").get() == "hello world"
        try:
            evaluate("a/b/-/undefined").get()
            assert False
        except Exception as e:
            assert e.query == "a/b/-/undefined"
            assert e.position.offset == 6

    def test_error_message2(self):
        import traceback
        import liquer.store as st

        reset_command_registry()
        st.set_store(st.MemoryStore())
        store = st.get_store()
        store.store("a/b", b"hello", {})

        @command
        def world(data):
            return data.decode("utf-8") + " world"

        @command
        def error(data):
            raise Exception("Error")

        assert evaluate("a/b/-/world").get() == "hello world"
        try:
            evaluate("a/b/-/error").get()
            assert False
        except Exception as e:
            assert e.query == "a/b/-/error"
            assert e.position.offset == 6

    def test_error_message3(self):
        import traceback
        import liquer.store as st

        reset_command_registry()
        st.set_store(st.MemoryStore())
        store = st.get_store()
        store.store("a/b", b"hello", {})

        @command
        def world(data):
            return data.decode("utf-8") + " world"

        @command
        def expected(data, arg):
            return f"{data} {arg}"

        assert evaluate("a/b/-/world/expected-x").get() == "hello world x"
        try:
            evaluate("a/b/-/expected").get()
            assert False
        except Exception as e:
            traceback.print_exc()
            assert e.query == "a/b/-/expected"
            assert e.position.offset == 6
        try:
            evaluate("a/b/-/expected-x-y").get()
            assert False
        except Exception as e:
            assert e.query == "a/b/-/expected-x-y"
            assert e.position.offset == 6

    def test_store_evaluate_and_save(self, tmpdir):
        import liquer.store as st

        reset_command_registry()
        st.set_store(st.MemoryStore())
        store = st.get_store()
        store.store("a/b", b"hello", {})

        @command
        def world(data):
            return data.decode("utf-8") + " world"

        evaluate_and_save(
            "a/b/-/world/hello.txt",
            target_directory=str(tmpdir),
            target_resource_directory="results",
        )
        assert store.get_bytes("results/hello.txt") == b"hello world"
        assert open(tmpdir / "hello.txt", "rb").read() == b"hello world"

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

    def test_recipe_store(self):
        import liquer.store as st
        import liquer.recipes as r
        from liquer.cache import MemoryCache, set_cache, get_cache

        reset_command_registry()
        set_cache(None)

        @first_command
        def hello():
            return "Hello"

        store = r.RecipeStore(st.MemoryStore())
        store.mount_recipe("my/hello.txt", "hello")
        assert store.contains("my/hello.txt")
        assert store.get_bytes("my/hello.txt") == b"Hello"

    def test_recipe_spec_store(self):
        import liquer.store as st
        import liquer.recipes as r
        from liquer.cache import MemoryCache, set_cache, get_cache

        reset_command_registry()
        set_cache(None)

        @first_command
        def hello():
            return "Hello"

        store = r.RecipeSpecStore(st.MemoryStore())
        store.store(
            "results/recipes.yaml",
            b"""
        subdir:
            - hello/hello.txt
        """,
            {},
        )
        assert "results/subdir/hello.txt" in store.recipes()
        assert store.contains("results")
        assert store.contains("results/subdir")
        assert store.contains("results/subdir/hello.txt")
        assert store.is_dir("results")
        assert store.is_dir("results/subdir")
        assert not store.is_dir("results/subdir/hello.txt")
        assert store.get_bytes("results/subdir/hello.txt") == b"Hello"

    def test_recipe_error_in_query_metadata(self):
        import liquer.store as st
        import liquer.recipes as r
        from liquer.cache import MemoryCache, set_cache, get_cache

        reset_command_registry()
        set_cache(None)

        @first_command
        def hello():
            raise Exception("Hello error")
        @command
        def world(x):
            return str(x)+"world"


        store = r.RecipeSpecStore(st.MemoryStore())
        set_store(store)
        store.store(
            "results/recipes.yaml",
            b"""
        subdir:
            - hello/hello.txt
        """,
            {},
        )
        assert "results/subdir/hello.txt" in store.recipes()
        try:
            assert store.get_bytes("results/subdir/hello.txt")
        except KeyNotFoundStoreException:
            pass
        assert store.get_metadata("results/subdir/hello.txt")["is_error"]
        assert store.get_metadata("results/subdir/hello.txt")["log"][-1]["message"]=="Hello error"
        child_messages = [x["message"] for x in evaluate("results/subdir/hello.txt/-/world/hello.txt").metadata["child_log"]]
        print(child_messages)
        assert "Hello error" in child_messages
        set_store(None)
        reset_command_registry()

    def test_sync(self):
        import liquer.store as st
        import liquer.recipes as r
        from liquer.cache import MemoryCache, set_cache, get_cache

        reset_command_registry()
        set_cache(None)

        @first_command
        def hello():
            return "Hello"

        memory=st.MemoryStore()
        store = r.RecipeSpecStore(memory)
        store.store(
            "results/recipes.yaml",
            b"""
        subdir:
            - hello/hello.txt
        """,
            {},
        )
        assert store.contains("results/subdir/hello.txt")
        assert not store.contains("results/subdir/hello2.txt")
        assert store.is_dir("results")
        assert store.is_dir("results/subdir")
        assert store.get_bytes("results/subdir/hello.txt") == b"Hello"

        memory.store(
            "results/recipes.yaml",
            b"""
        subdir:
            - hello/hello2.txt
        """,
            {},
        )
        assert not store.contains("results/subdir/hello2.txt")
        store.sync()
        assert store.contains("results/subdir/hello2.txt")
        assert store.get_bytes("results/subdir/hello2.txt") == b"Hello"
        reset_command_registry()
