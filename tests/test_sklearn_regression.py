#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer pandas support.
'''
import pandas as pd
from liquer.commands import command, first_command
from liquer.query import evaluate
import pytest

class TestRegression:
    def test_linear(self):
        import importlib
        import liquer.ext.basic
        import liquer.ext.lq_pandas
        import liquer.ext.lq_sklearn_regression
        from liquer.commands import reset_command_registry
        reset_command_registry() # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.basic)
        importlib.reload(liquer.ext.lq_pandas)
        importlib.reload(liquer.ext.lq_sklearn_regression)

        @first_command
        def test1():
            return pd.DataFrame(dict(x=[1,2,3],Y=[10,20,30]))
        @first_command
        def test2():
            return pd.DataFrame(dict(x=[1,2,3],Y=[30,40,50]))
        @first_command
        def test3():
            return pd.DataFrame(dict(x1=[1,2,3],x2=[0,0,1],Y=[30,40,55]))
        
        df = evaluate("ns-sklearn/test1/linear_regression").get()
        assert list(df.x)[0] == pytest.approx(10.0)
        df = evaluate("ns-sklearn/test2/linear_regression").get()
        assert list(df.x)[0] == pytest.approx(10.0)
        assert list(df.intercept)[0] == pytest.approx(20.0)
        df = evaluate("ns-sklearn/test3/linear_regression").get()
        assert list(df.x1)[0] == pytest.approx(10.0)
        assert list(df.x2)[0] == pytest.approx(5.0)
        assert list(df.intercept)[0] == pytest.approx(20.0)

    def test_ridge(self):
        import importlib
        import liquer.ext.basic
        import liquer.ext.lq_pandas
        import liquer.ext.lq_sklearn_regression
        from liquer.commands import reset_command_registry
        reset_command_registry() # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.basic)
        importlib.reload(liquer.ext.lq_pandas)
        importlib.reload(liquer.ext.lq_sklearn_regression)

        @first_command
        def test1():
            return pd.DataFrame(dict(x=[1,2,3],Y=[10,20,30]))
        @first_command
        def test2():
            return pd.DataFrame(dict(x=[1,2,3],Y=[30,40,50]))
        @first_command
        def test3():
            return pd.DataFrame(dict(x1=[1,2,3],x2=[0,0,1],Y=[30,40,55]))
        
        df = evaluate("ns-sklearn/test1/ridge").get()
        assert list(df.x)[0] == pytest.approx(9.52381)
        df = evaluate("ns-sklearn/test2/ridge").get()
        assert list(df.x)[0] == pytest.approx(9.52381)
        assert list(df.intercept)[0] == pytest.approx(20.952381)
        df = evaluate("ns-sklearn/test3/ridge").get()
        assert list(df.x1)[0] == pytest.approx(9.562842)
        assert list(df.x2)[0] == pytest.approx(4.918033)
        assert list(df.intercept)[0] == pytest.approx(20.901639)
