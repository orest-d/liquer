#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer OpenPyxl support.
"""
import pandas as pd
from liquer.query import evaluate, evaluate_and_save
from liquer.parser import encode_token
from liquer.cache import set_cache, FileCache
import os.path
import inspect
import tempfile
from liquer.state import set_var
from liquer.store import set_store, MemoryStore
import importlib


class TestOpenpyxl:
    @classmethod
    def setup_class(cls):
        from liquer.commands import reset_command_registry
        import liquer.ext.lq_pandas  # register pandas commands and state type
        import liquer.ext.lq_openpyxl  # register openpyxl commands and state type

        reset_command_registry()  # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.lq_pandas)
        importlib.reload(liquer.ext.lq_openpyxl)

    @classmethod
    def teardown_class(cls):
        from liquer.commands import reset_command_registry

        reset_command_registry()

    def test_workbook(self):
        store = MemoryStore()
        set_store(store)

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        evaluate_and_save(f"df_from-{filename}/test.xlsx",target_resource_directory="testdir")
        df = evaluate("testdir/test.xlsx/-/workbook/workbook_sheet_df").get()
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1, 3]
        assert list(df.b) == [2, 4]

