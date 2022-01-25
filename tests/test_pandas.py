#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer pandas support.
"""
import pandas as pd
from liquer import *
from liquer.query import evaluate, evaluate_and_save
from liquer.parser import encode_token
from liquer.cache import set_cache, FileCache
import os.path
import inspect
import tempfile
from liquer.state import set_var
from liquer.store import set_store, MemoryStore
from liquer.constants import *
import importlib
from liquer.recipes import RecipeSpecStore


class TestPandas:
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

    def test_from(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        state = evaluate(f"df_from-{filename}")
        df = state.get()
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1, 3]
        assert list(df.b) == [2, 4]

    def test_append(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
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
            filename = encode_token(
                os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
            )
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

    def test_df_from(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        state = evaluate(f"df_from-{filename}")
        df = state.get()
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1,3]
        assert list(df.b) == [2,4]
        assert state.type_identifier == "dataframe"

    def test_eq(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
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

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test_hxl.csv"
        )
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

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        df = evaluate(f"df_from-{filename}/qsplit_df-a").get()
        assert "a" in df.columns
        assert "b" not in df.columns
        assert list(df.a) == [1, 3]
        assert list(df["query"]) == [
            f"df_from-{filename}/eq-a-1",
            f"df_from-{filename}/eq-a-3",
        ]

    def test_qsplit2(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        df = evaluate(f"df_from-{filename}/qsplit_df-a-b").get()
        assert list(df.a) == [1, 3]
        assert list(df.b) == [2, 4]
        assert list(df["query"]) == [
            f"df_from-{filename}/eq-a-1-b-2",
            f"df_from-{filename}/eq-a-3-b-4",
        ]

    def test_split(self):
        import importlib
        import liquer.ext.lq_pandas  # register pandas commands and state type
        import liquer.ext.basic
        from liquer.commands import reset_command_registry

        reset_command_registry()  # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.lq_pandas)
        importlib.reload(liquer.ext.basic)
        set_var("server", "http://localhost")
        set_var("api_path", "/q/")

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        df = evaluate(f"df_from-{filename}/split_df-a").get()
        assert "a" in df.columns
        assert "b" not in df.columns
        assert list(df.a) == [1, 3]
        assert list(df["query"]) == [
            f"df_from-{filename}/eq-a-1",
            f"df_from-{filename}/eq-a-3",
        ]
        assert list(df["link"]) == [
            f"http://localhost/q/df_from-{filename}/eq-a-1",
            f"http://localhost/q/df_from-{filename}/eq-a-3",
        ]

    def test_tsplit(self):
        import importlib
        import liquer.ext.lq_pandas  # register pandas commands and state type
        import liquer.ext.basic
        from liquer.commands import reset_command_registry

        reset_command_registry()  # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.lq_pandas)
        importlib.reload(liquer.ext.basic)
        set_var("server", "http://localhost")
        set_var("api_path", "/q/")

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test_hxl.csv"
        )
        df = evaluate(f"df_from-{filename}/tsplit_df-a").get()
        assert "a" in df.columns
        assert "b" not in df.columns
        assert list(df.a) == ["#indicator +num +aaa", "1", "3"]
        assert list(df["query"])[1:] == [
            f"df_from-{filename}/teq-a-1",
            f"df_from-{filename}/teq-a-3",
        ]
        assert list(df["link"])[1:] == [
            f"http://localhost/q/df_from-{filename}/teq-a-1",
            f"http://localhost/q/df_from-{filename}/teq-a-3",
        ]

    def test_columns_info(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type
        from liquer.state_types import encode_state_data, decode_state_data

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        assert evaluate(f"df_from-{filename}/df_columns").get() == ["a", "b"]
        assert evaluate(f"df_from-{filename}/columns_info").get()["columns"] == [
            "a",
            "b",
        ]
        assert evaluate(f"df_from-{filename}/columns_info").get()["has_tags"] == False
        assert (
            evaluate(f"df_from-{filename}/columns_info")
            .get()["types"]["a"]
            .startswith("int")
        )
        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test_hxl.csv"
        )
        assert evaluate(f"df_from-{filename}/df_columns").get() == ["a", "b"]
        assert evaluate(f"df_from-{filename}/columns_info").get()["columns"] == [
            "a",
            "b",
        ]
        assert evaluate(f"df_from-{filename}/columns_info").get()["has_tags"] == True
        assert (
            evaluate(f"df_from-{filename}/columns_info").get()["tags"]["a"]
            == "#indicator +num +aaa"
        )
        assert (
            evaluate(f"df_from-{filename}/columns_info").get()["tags"]["b"]
            == "#indicator +num +bbb"
        )
        info = evaluate(f"df_from-{filename}/columns_info").get()
        b, mime, tid = encode_state_data(info)
        assert info == decode_state_data(b, tid)

    def test_head(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        df = evaluate(f"df_from-{filename}/head_df-1").get()
        assert list(df.a) == [1]
        assert list(df.b) == [2]

    def test_save_parquet(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        evaluate_and_save(f"df_from-{filename}/head_df-1/test.parquet")

    def test_save_feather(self):
        import liquer.ext.lq_pandas  # register pandas commands and state type

        filename = encode_token(
            os.path.dirname(inspect.getfile(self.__class__)) + "/test.csv"
        )
        evaluate_and_save(f"df_from-{filename}/head_df-1/test.feather")

    def test_dr(self):
        import pandas as pd
        import liquer.ext.basic
        from liquer.commands import reset_command_registry

        reset_command_registry()  # prevent double-registration
        importlib.reload(liquer.ext.basic)
        importlib.reload(liquer.ext.lq_pandas)

        store = MemoryStore()
        set_store(store)
        store.store("data.csv", b"a,b\n1,2\n3,4", {})
        df = evaluate("data.csv/-/dr").get()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert len(df.columns) == 2
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1, 3]
        assert list(df.b) == [2, 4]

    def test_dr1(self):
        import pandas as pd
        import liquer.ext.basic
        from liquer.commands import reset_command_registry

        reset_command_registry()  # prevent double-registration
        importlib.reload(liquer.ext.basic)
        importlib.reload(liquer.ext.lq_pandas)

        store = MemoryStore()
        set_store(store)
        store.store("data.csv", b"a,b\n1,2\n3,4", dict(type_identifier="dataframe"))
        df = evaluate("data.csv/-/dr").get()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert len(df.columns) == 2
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1, 3]
        assert list(df.b) == [2, 4]

    def test_dr2(self):
        import pandas as pd
        import liquer.ext.basic
        from liquer.commands import reset_command_registry

        reset_command_registry()  # prevent double-registration
        importlib.reload(liquer.ext.basic)
        importlib.reload(liquer.ext.lq_pandas)

        store = MemoryStore()
        set_store(store)
        store.store("data", b"a,b\n1,2\n3,4", {})
        df = evaluate("data/-/dr-dataframe-csv").get()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert len(df.columns) == 2
        assert "a" in df.columns
        assert "b" in df.columns
        assert list(df.a) == [1, 3]
        assert list(df.b) == [2, 4]
        reset_command_registry()

    def test_concat_recipe(self):
        import pandas as pd
        import liquer.ext.basic
        from liquer.commands import reset_command_registry

        reset_command_registry()  # prevent double-registration
        importlib.reload(liquer.ext.basic)
        importlib.reload(liquer.ext.lq_pandas)
        import liquer.store as st

        @first_command
        def hello(offset=0):
            return pd.DataFrame(dict(a=[1+offset,2+offset],b=[3+offset,4+offset]))

        substore = st.MemoryStore()
        substore.store(
            "recipes.yaml",
            """
RECIPES:
  - filename: hello.parquet
    type: pandas_concat
    concat:
    - hello
    - query: hello-10
      column: test
      value: extra
""",
            {},
        )
        store = RecipeSpecStore(substore)
        set_store(store)
        assert "hello.parquet" in store.keys()
        df = evaluate("hello.parquet/-/dr").get()
        assert sorted(df.columns) == ["a", "b", "test"]
        assert list(df.a) == [1,2,11,12]
        assert list(df.b) == [3,4,13,14]
        assert list(df.test) == [None, None, "extra", "extra"]

        assert store.get_metadata("hello.parquet")["status"] == Status.READY.value
        assert store.get_metadata("hello.parquet")["recipes_key"] == "recipes.yaml"
        assert store.get_metadata("hello.parquet")["has_recipe"] == True
        assert store.get_metadata("hello.parquet")["recipes_directory"] == ""
        assert store.get_metadata("hello.parquet")["recipe_name"] == "recipes.yaml/-Ryaml/RECIPES/0#hello.parquet"
        assert store.get_metadata("hello.parquet")["data_characteristics"]["description"] == "Dataframe with 3 columns and 4 rows."

        set_store(None)
        reset_command_registry()
