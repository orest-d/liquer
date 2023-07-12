#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer polars support.
"""
import pandas as pd
import polars as pl
from liquer.query import evaluate, evaluate_and_save
from liquer.parser import encode_token
from liquer.cache import set_cache, FileCache
import os.path
import inspect
import tempfile
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
