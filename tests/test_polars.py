#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer polars support.
"""
import pandas as pd
import polars as pl
from liquer import *
from liquer.query import evaluate, evaluate_and_save
from liquer.parser import encode_token
from liquer.cache import set_cache, FileCache
import os.path
import inspect
import tempfile
from tempfile import TemporaryDirectory
from liquer.state import set_var
from liquer.store import set_store, MemoryStore
import importlib


class TestPolars:
    @classmethod
    def setup_class(cls):
        from liquer.commands import reset_command_registry
        import liquer.ext.lq_pandas  # register pandas commands and state type
        import liquer.ext.lq_polars  # register pandas commands and state type

        reset_command_registry()  # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.lq_pandas)
        importlib.reload(liquer.ext.lq_polars)

    @classmethod
    def teardown_class(cls):
        from liquer.commands import reset_command_registry

        reset_command_registry()

    def test_from(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        df = evaluate(f"df_from-{filename}/polars_df").get()
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.select('a').to_numpy().flatten()) == [1, 3]
        assert list(df.select('b').to_numpy().flatten()) == [2, 4]

    def test_save_parquet(self):
        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        evaluate_and_save(f"df_from-{filename}/polars_df/test.parquet", target_directory=".")

    def test_work_context(self):
        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        with TemporaryDirectory() as tmpdir:
            @first_command(volatile=True, cache=False)
            def sql_context():
                ctx = pl.SQLContext(df = pl.DataFrame({"a":[1,3], "b":[2,4]}))
                return ctx
            @command
            def process(ctx):
                return ctx.execute("SELECT a, b, a+b AS c FROM df")
            evaluate_and_save(f"sql_context/ctx.csv", target_directory=tmpdir)
            evaluate_and_save(f"sql_context/ctx.parquet", target_directory=tmpdir)
            evaluate_and_save(f"sql_context/ctx.json", target_directory=tmpdir)
            evaluate_and_save(f"sql_context/ctx.ndjson", target_directory=tmpdir)

            evaluate_and_save(f"sql_context/process/result.csv", target_directory=tmpdir)
            evaluate_and_save(f"sql_context/process/result.parquet", target_directory=tmpdir)
            evaluate_and_save(f"sql_context/process/result.json", target_directory=tmpdir)
            evaluate_and_save(f"sql_context/process/result.ndjson", target_directory=tmpdir)

            df = evaluate(f"sql_context/process").get().collect().to_dict(as_series=False)
            assert df["a"] == [1, 3]
            assert df["b"] == [2, 4]
            assert df["c"] == [3, 7]

