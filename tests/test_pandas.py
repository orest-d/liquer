#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer parser.
'''
import pandas as pd
from liquer.query import evaluate
from liquer.parser import encode_token
import os.path
import inspect


class TestPandas:
    def test_from(self):
        import liquer.ext.lq_pandas as lqpd
        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test.csv")
        state = evaluate(f"df_from-{filename}")
        df = state.get()
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1, 3]
        assert list(df.b) == [2, 4]

    def test_append(self):
        import liquer.ext.lq_pandas as lqpd
        filename = encode_token(os.path.dirname(
            inspect.getfile(self.__class__))+"/test.csv")
        state = evaluate(f"df_from-{filename}/append_df-{filename}")
        df = state.get()
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1, 3, 1, 3]
        assert list(df.b) == [2, 4, 2, 4]
