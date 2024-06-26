#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer HXL support.
See https://github.com/HXLStandard/libhxl-python
"""
import pandas as pd
from liquer.query import evaluate
from liquer.parser import encode_token
from liquer.cache import set_cache, FileCache
import importlib
import os.path
import inspect
import tempfile


class TestHXL:
    @classmethod
    def setup_class(cls):
        from liquer.commands import reset_command_registry
        import liquer.ext.lq_pandas  # register pandas commands and state type

        reset_command_registry()  # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.lq_pandas)

    @classmethod
    def teardown_class(cls):
        from liquer.commands import reset_command_registry

        reset_command_registry()

    def test_from(self, httpserver):
        import liquer.ext.lq_hxl  # register HXL commands and state type

        test_hxl = open(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test_hxl.csv"
        ).read()

        httpserver.expect_request("/test_hxl.csv").respond_with_data(test_hxl)
        url = encode_token(httpserver.url_for("/test_hxl.csv"))
        state = evaluate(f"hxl_from-{url}")
        data = state.get()
        assert data.columns[0].header == "a"
        assert data.columns[0].display_tag == "#indicator+num+aaa"
        assert data.columns[1].header == "b"
        assert data.columns[1].display_tag == "#indicator+num+bbb"

    def test_from_with_cache(self, httpserver):
        import liquer.ext.lq_hxl  # register HXL commands and state type

        test_hxl = open(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test_hxl.csv"
        ).read()

        httpserver.expect_request("/test_hxl.csv").respond_with_data(test_hxl)
        url = encode_token(httpserver.url_for("/test_hxl.csv"))
        query = f"hxl_from-{url}"
        with tempfile.TemporaryDirectory() as cachepath:
            set_cache(FileCache(cachepath))
            state = evaluate(query)
            data = state.get()
            assert data.columns[0].header == "a"
            assert data.columns[0].display_tag == "#indicator+num+aaa"
            assert data.columns[1].header == "b"
            assert data.columns[1].display_tag == "#indicator+num+bbb"
            state = evaluate(query)
            data = state.get()
            assert data.columns[0].header == "a"
            assert data.columns[0].display_tag == "#indicator+num+aaa"
            assert data.columns[1].header == "b"
            assert data.columns[1].display_tag == "#indicator+num+bbb"
        set_cache(None)

    def test_hxl2df(self, httpserver):
        import liquer.ext.lq_hxl  # register HXL commands and state type

        test_hxl = open(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test_hxl.csv"
        ).read()

        httpserver.expect_request("/test_hxl.csv").respond_with_data(test_hxl)
        url = encode_token(httpserver.url_for("/test_hxl.csv"))
        df = evaluate(f"hxl_from-{url}/hxl2df").get()
        assert list(df.columns) == ["a", "b"]
        assert list(df.a[1:]) == ["1", "3"]
        assert list(df.b[1:]) == ["2", "4"]

    def test_df2hxl(self):
        import liquer.ext.lq_hxl  # register HXL commands and state type
        import liquer.ext.lq_pandas  # register pandas commands and state type

        path = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test_hxl.csv"
        )
        data = evaluate(f"df_from-{path}/df2hxl").get()
        assert data.columns[0].header == "a"
        assert data.columns[0].display_tag == "#indicator+num+aaa"
        assert data.columns[1].header == "b"
        assert data.columns[1].display_tag == "#indicator+num+bbb"

    def test_set_all_tags(self):
        import liquer.ext.lq_hxl  # register HXL commands and state type
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        data = evaluate(
            f"df_from-{filename}/set_all_tags-indicator+a-indicator+b/df2hxl"
        ).get()
        assert data.columns[0].header == "a"
        assert data.columns[0].display_tag == "#indicator+a"
        assert data.columns[1].header == "b"
        assert data.columns[1].display_tag == "#indicator+b"
        df = evaluate(f"df_from-{filename}/set_all_tags-indicator+a-indicator+b").get()
        assert list(df.a) == ["#indicator+a", 1, 3]
        assert list(df.b) == ["#indicator+b", 2, 4]
        df = evaluate(f"df_from-{filename}/set_all_tags-indicator+a").get()
        assert list(df.a) == ["#indicator+a", 1, 3]
        assert list(df.b) == ["", 2, 4]

    def test_set_tags(self):
        import liquer.ext.lq_hxl  # register HXL commands and state type
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        data = evaluate(
            f"df_from-{filename}/set_tags-b-indicator+b-a-indicator+a/df2hxl"
        ).get()
        assert data.columns[0].header == "a"
        assert data.columns[0].display_tag == "#indicator+a"
        assert data.columns[1].header == "b"
        assert data.columns[1].display_tag == "#indicator+b"
        df = evaluate(f"df_from-{filename}/set_tags-b-indicator+b").get()
        assert list(df.a) == ["", 1, 3]
        assert list(df.b) == ["#indicator+b", 2, 4]
