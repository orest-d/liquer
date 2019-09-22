#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer pandas support.
'''
import pandas as pd
from liquer.query import evaluate
from liquer.parser import encode_token
from liquer.cache import set_cache, FileCache
import os.path
import inspect
import tempfile
from liquer.state import set_var


class TestPandas:
    def test_from(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type
        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test.csv")
        state = evaluate(f"df_from-{filename}")
        df = state.get()
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1, 3]
        assert list(df.b) == [2, 4]

    def test_append(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type
        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test.csv")
        state = evaluate(f"df_from-{filename}/append_df-{filename}")
        df = state.get()
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1, 3, 1, 3]
        assert list(df.b) == [2, 4, 2, 4]

    def test_append_with_cache(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type
        with tempfile.TemporaryDirectory() as cachepath:
            set_cache(FileCache(cachepath))
            filename = encode_token(os.path.dirname(
                inspect.getfile(self.__class__))+"/test.csv")
            df = evaluate(f"df_from-{filename}/append_df-{filename}").get()
            assert "a" in df.columns
            assert "b" in df.columns
            assert list(df.a) == [1, 3, 1, 3]
            assert list(df.b) == [2, 4, 2, 4]
            df = evaluate(f"df_from-{filename}/append_df-{filename}").get()
            assert "a" in df.columns
            assert "b" in df.columns
            assert list(df.a) == [1, 3, 1, 3]
            assert list(df.b) == [2, 4, 2, 4]
        set_cache(None)

    def test_eq(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type
        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test.csv")
        state = evaluate(f"df_from-{filename}/eq-a-1")
        df = state.get()
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1]
        assert list(df.b) == [2]
        df = evaluate(f"df_from-{filename}/eq-a-3-b-4").get()
        assert list(df.a) == [3]
        assert list(df.b) == [4]
        df = evaluate(f"df_from-{filename}/eq-a-1-b-4").get()
        assert list(df.a) == []
        assert list(df.b) == []

    def test_teq(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type
        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test_hxl.csv")
        state = evaluate(f"df_from-{filename}/teq-a-1")
        df = state.get()
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == ["#indicator +num +aaa", "1"]
        assert list(df.b) == ["#indicator +num +bbb", "2"]
        df = evaluate(f"df_from-{filename}/teq-a-3-b-4").get()
        assert list(df.a) == ["#indicator +num +aaa", "3"]
        assert list(df.b) == ["#indicator +num +bbb", "4"]
        df = evaluate(f"df_from-{filename}/teq-a-1-b-4").get()
        assert list(df.a) == ["#indicator +num +aaa"]
        assert list(df.b) == ["#indicator +num +bbb"]

    def test_qsplit1(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type
        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test.csv")
        df = evaluate(f"df_from-{filename}/qsplit_df-a").get()
        assert "a" in df.columns
        assert "b" not in df.columns
        assert list(df.a) == [1, 3]
        assert list(df["query"]) == [
            f"df_from-{filename}/eq-a-1", f"df_from-{filename}/eq-a-3"]

    def test_qsplit2(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type
        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test.csv")
        df = evaluate(f"df_from-{filename}/qsplit_df-a-b").get()
        assert list(df.a) == [1, 3]
        assert list(df.b) == [2, 4]
        assert list(df["query"]) == [
            f"df_from-{filename}/eq-a-1-b-2", f"df_from-{filename}/eq-a-3-b-4"]

    def test_split(self):
        import importlib
        import liquer.ext.lq_pandas  # register pandas commands and state type
        import liquer.ext.basic
        from liquer.commands import reset_command_registry
        reset_command_registry() # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.lq_pandas)
        importlib.reload(liquer.ext.basic)
        set_var("server", "http://localhost")
        set_var("api_path", "/q/")

        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test.csv")
        df = evaluate(f"df_from-{filename}/split_df-a").get()
        assert "a" in df.columns
        assert "b" not in df.columns
        assert list(df.a) == [1, 3]
        assert list(df["query"]) == [
            f"df_from-{filename}/eq-a-1", f"df_from-{filename}/eq-a-3"]
        assert list(df["link"]) == [
            f"http://localhost/q/df_from-{filename}/eq-a-1",
            f"http://localhost/q/df_from-{filename}/eq-a-3"]

    def test_tsplit(self):
        import importlib
        import liquer.ext.lq_pandas  # register pandas commands and state type
        import liquer.ext.basic
        from liquer.commands import reset_command_registry
        reset_command_registry() # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.lq_pandas)
        importlib.reload(liquer.ext.basic)
        set_var("server", "http://localhost")
        set_var("api_path", "/q/")

        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test_hxl.csv")
        df = evaluate(f"df_from-{filename}/tsplit_df-a").get()
        assert "a" in df.columns
        assert "b" not in df.columns
        assert list(df.a) == ["#indicator +num +aaa", "1", "3"]
        assert list(df["query"])[1:] == [
            f"df_from-{filename}/teq-a-1",
            f"df_from-{filename}/teq-a-3"]
        assert list(df["link"])[1:] == [
            f"http://localhost/q/df_from-{filename}/teq-a-1",
            f"http://localhost/q/df_from-{filename}/teq-a-3"]

    def test_columns_info(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type
        from liquer.state_types import encode_state_data, decode_state_data
        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test.csv")
        assert evaluate(f"df_from-{filename}/df_columns").get() == ["a", "b"]
        assert evaluate(
            f"df_from-{filename}/columns_info").get()["columns"] == ["a", "b"]
        assert evaluate(
            f"df_from-{filename}/columns_info").get()["has_tags"] == False
        assert evaluate(
            f"df_from-{filename}/columns_info").get()["types"]["a"].startswith("int")
        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test_hxl.csv")
        assert evaluate(f"df_from-{filename}/df_columns").get() == ["a", "b"]
        assert evaluate(
            f"df_from-{filename}/columns_info").get()["columns"] == ["a", "b"]
        assert evaluate(
            f"df_from-{filename}/columns_info").get()["has_tags"] == True
        assert evaluate(
            f"df_from-{filename}/columns_info").get()["tags"]["a"] == "#indicator +num +aaa"
        assert evaluate(
            f"df_from-{filename}/columns_info").get()["tags"]["b"] == "#indicator +num +bbb"
        info = evaluate(f"df_from-{filename}/columns_info").get()
        b, mime, tid = encode_state_data(info)
        assert info == decode_state_data(b, tid)

    def test_head(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type
        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test.csv")
        df = evaluate(f"df_from-{filename}/head_df-1").get()
        assert list(df.a) == [1]
        assert list(df.b) == [2]
