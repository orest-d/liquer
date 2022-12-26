#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer datafusion support.
"""
import pandas as pd
from liquer.commands import command, first_command
from liquer.query import evaluate, evaluate_and_save
from liquer.parser import encode_token
from liquer.recipes import RecipeSpecStore
from liquer.store import set_store
from liquer.constants import Status
import os.path
import inspect
import importlib
from tempfile import TemporaryDirectory
from pathlib import Path
import datafusion as daf


class TestDatafusion:
    @classmethod
    def setup_class(cls):
        from liquer.commands import reset_command_registry
        import liquer.ext.basic
        import liquer.ext.meta
        import liquer.ext.lq_pandas  # register pandas commands and state type
        import liquer.ext.lq_datafusion  # register pandas commands and state type

        reset_command_registry()  # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.lq_pandas)
        importlib.reload(liquer.ext.lq_datafusion)
        importlib.reload(liquer.ext.basic)
        importlib.reload(liquer.ext.meta)

    @classmethod
    def teardown_class(cls):
        from liquer.commands import reset_command_registry

        reset_command_registry()

    def test_from(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        df = evaluate(f"df_from-{filename}").get()
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1, 3]
        assert list(df.b) == [2, 4]

    def test_work_with_parquet(self):
        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)/"test.parquet"
            evaluate_and_save(f"df_from-{filename}/test.parquet", target_directory=tmpdir)
            @first_command(volatile=True, cache=False)
            def datafusion_context():
                ctx = daf.SessionContext()
                ctx.register_parquet("a",str(path))
                return ctx
            @command
            def process(ctx):
                return ctx.sql("SELECT a, b, a+b AS c FROM a")
            evaluate_and_save(f"datafusion_context/process/result.parquet", target_directory=tmpdir)        

            df = evaluate(f"datafusion_context/process/datafusion_to_pandas").get()
            assert "a" in df.columns
            assert "b" in df.columns
            assert "c" in df.columns
            assert list(df.a) == [1, 3]
            assert list(df.b) == [2, 4]
            assert list(df.c) == [3, 7]

    def test_sql_recipe(self):
        import liquer.store as st

        @first_command
        def hello():
            return pd.DataFrame(dict(a=[1,2],b=[3,4]))
        @command
        def c(df):
            return ",".join(str(x) for x in df.c)

        substore = st.MemoryStore()
        substore.store(
            "recipes.yaml",
            """
RECIPES:
  - filename: hello.parquet
    type: parquet_sql
    register:
    - hello/hello.parquet
    sql: SELECT a,b,a+b AS c FROM hello
  - hello.parquet/-/dr-dataframe-parquet/c/c.txt
""",
            {},
        )
        store = RecipeSpecStore(substore)
        set_store(store)
        assert "hello.parquet" in store.keys()
        assert "c.txt" in store.keys()

        assert store.get_bytes("c.txt") == b"4,6"
        assert store.get_metadata("hello.parquet")["status"] == Status.READY.value
        assert store.get_metadata("hello.parquet")["dependencies"]["recipe"]["version"] == "md5:c065cb611597fc0e953e5ad72a769db8"

    def test_sql_error(self):
        import liquer.store as st

        @first_command
        def hello1():
            return pd.DataFrame(dict(a=[1,2],b=[3,4]))
        @command
        def c1(df):
            return ",".join(str(x) for x in df.c)

        substore = st.MemoryStore()
        substore.store(
            "recipes.yaml",
            """
RECIPES:
  - filename: hello.parquet
    type: parquet_sql
    register:
    - hello1/hello.parquet
    sql: SELECT xxx,b,a+b AS c FROM hello
  - hello.parquet/-/dr-dataframe-parquet/c1/c.txt
""",
            {},
        )
        store = RecipeSpecStore(substore)
        set_store(store)
        assert "hello.parquet" in store.keys()
        assert "c.txt" in store.keys()

        try:
            store.get_bytes("c.txt")
        except:
            pass
        assert store.get_metadata("hello.parquet")["status"] == Status.ERROR.value
        assert store.get_metadata("hello.parquet")["recipes_key"] == "recipes.yaml"
        assert store.get_metadata("hello.parquet")["has_recipe"] == True
        assert store.get_metadata("hello.parquet")["recipes_directory"] == ""
        assert store.get_metadata("hello.parquet")["recipe_name"] == "recipes.yaml/-Ryaml/RECIPES/0#hello.parquet"
