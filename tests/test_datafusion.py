#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer datafusion support.
"""
import pandas as pd
from liquer.commands import command, first_command
from liquer.query import evaluate, evaluate_and_save
from liquer.parser import encode_token
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
        import liquer.ext.lq_pandas  # register pandas commands and state type
        import liquer.ext.lq_datafusion  # register pandas commands and state type

        reset_command_registry()  # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.lq_pandas)
        importlib.reload(liquer.ext.lq_datafusion)

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
            def execution_context():
                ctx = daf.ExecutionContext()
                ctx.register_parquet("a",str(path))
                return ctx
            @command
            def process(ctx):
                return ctx.sql("SELECT a, b, a+b AS c FROM a")
            evaluate_and_save(f"execution_context/process/result.parquet", target_directory=tmpdir)        

            df = evaluate(f"execution_context/process/datafusion_to_pandas").get()
            assert "a" in df.columns
            assert "b" in df.columns
            assert "c" in df.columns
            assert list(df.a) == [1, 3]
            assert list(df.b) == [2, 4]
            assert list(df.c) == [3, 7]
