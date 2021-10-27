#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer execution context.
"""
import pytest
from liquer.context import *
from liquer.parser import ActionRequest
from liquer.state import State, set_var
from liquer.commands import reset_command_registry, command, first_command


class TestContext:
    def test_evaluate_action(self):
        reset_command_registry()

        @command
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a + b

        context = Context()
        action = ActionRequest.from_arguments("test_callable", "1")
        result = context.evaluate_action(State(), action)
        assert result.get() == 124
        assert result.metadata["commands"][-1] == ["test_callable", "1"]

    def test_evaluate_command_with_attributes(self):
        reset_command_registry()

        @command(ABC="def")
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a + b

        context = Context()
        action = ActionRequest.from_arguments("test_callable", "1")
        result = context.evaluate_action(State(), action)
        assert result.get() == 124
        assert result.metadata["commands"][-1] == ["test_callable", "1"]
        assert result.metadata["attributes"]["ABC"] == "def"

    def test_evaluate_chaining_attributes(self):
        reset_command_registry()

        @command(ABC="def")
        def test_callable1(state, a: int, b=123):  # has state as a first argument
            return a + b

        @command
        def test_callable2(state):  # has state as a first argument
            return state

        context = Context()
        action1 = ActionRequest.from_arguments("test_callable1", "1")
        action2 = ActionRequest.from_arguments("test_callable2")

        state1 = context.evaluate_action(State(), action1)
        assert state1.get() == 124
        assert state1.metadata["attributes"]["ABC"] == "def"

        state2 = context.evaluate_action(state1, action2)
        assert state2.get() == 124
        assert state2.metadata["attributes"]["ABC"] == "def"

    def test_state_command(self):
        reset_command_registry()

        @command
        def statecommand(state):  # has state as a first argument
            assert isinstance(state, State)
            return 123 + state.get()

        assert (
            Context()
            .evaluate_action(State().with_data(1), ActionRequest("statecommand"))
            .get()
            == 124
        )

    def test_nonstate_command(self):
        reset_command_registry()

        @command
        def nonstatecommand(x: int):  # has state as a first argument
            assert x == 1
            return 123 + x

        assert (
            Context()
            .evaluate_action(State().with_data(1), ActionRequest("nonstatecommand"))
            .get()
            == 124
        )

    def test_vars_context(self):
        reset_command_registry()
        set_var("test_var", "INITIAL")

        @first_command
        def varcommand(context=None):
            is_initial = context.vars.test_var == "INITIAL"
            context.vars.test_var = "MODIFIED"
            return is_initial

        @command
        def check1(state, context=None):
            print(f"Check1: ", state.vars["test_var"])
            return state.vars["test_var"] == "MODIFIED"

        @command
        def check2(state, context=None):
            print(f"Check2: ", context.vars.test_var)
            return context.vars.test_var == "MODIFIED"

        assert Context().evaluate("varcommand").get() == True
        assert Context().evaluate("check1").get() == False
        assert Context().evaluate("check2").get() == False
        assert Context().evaluate("varcommand/check1").get() == True
        assert Context().evaluate("varcommand/check2").get() == True

    def test_vars(self):
        v = Vars()
        assert len(v) == 0
        v.x = 123
        assert dict(v) == {"x": 123}
        assert v.get_modified() == {"x": 123}
        v = Vars(x=1234)
        assert len(v) == 1
        assert v.get_modified() == {}
        v.y = 123
        assert dict(v) == {"x": 1234, "y": 123}
        assert v.get_modified() == {"y": 123}


class TestRecipes:
    def test_recipes(self):
        import liquer.store as st

        reset_command_registry()

        @first_command
        def hello(x):
            return f"Hello, {x}"

        substore = st.MemoryStore()
        substore.store(
            "recipes.yaml",
            """
RECIPES:
  - hello-RECIPES/hello1.txt
subdir:
  - hello-subdir/hello2.txt
""",
            {},
        )
        substore.store(
            "x/recipes.yaml",
            """
RECIPES:
  - hello-RECIPES_X/hello3.txt
subdir:
  - hello-subdir_x/hello4.txt
""",
            {},
        )
        store = RecipeSpecStore(substore)
        assert "hello1.txt" in store.keys()
        assert "subdir/hello2.txt" in store.keys()
        assert "x/hello3.txt" in store.keys()
        assert "x/subdir/hello4.txt" in store.keys()

        assert store.get_bytes("hello1.txt") == b"Hello, RECIPES"
        assert store.get_bytes("subdir/hello2.txt") == b"Hello, subdir"
        assert store.get_bytes("x/hello3.txt") == b"Hello, RECIPES_X"
        assert store.get_bytes("x/subdir/hello4.txt") == b"Hello, subdir_x"

    def test_ignore(self):
        import liquer.store as st

        reset_command_registry()

        @first_command
        def hello(x):
            return f"Hello, {x}"

        substore = st.MemoryStore()
        substore.store(".a/recipes.yaml", "", {})
        substore.store("a/b", "", {})
        substore.store("a/.b", "", {})
        substore.store(".a/b", "", {})
        substore.store(".a/.b", "", {})
        store = RecipeSpecStore(substore)
        assert "a/b" in store.keys()
        assert "a/.b" not in store.keys()
        assert ".a/b" not in store.keys()
        assert ".a/.b" not in store.keys()

    def test_recipes_advanced(self):
        import liquer.store as st

        reset_command_registry()

        @first_command
        def hello(x):
            return f"Hello, {x}"

        substore = st.MemoryStore()
        substore.store(
            "recipes.yaml",
            """
RECIPES:
  - query: hello-RECIPES/hello1.txt
    title: "Hello 1"
    description: "This is hello 1."
subdir:
  - query: hello-subdir/hello.txt
    filename: hello2.txt
    title: "Hello 2"
    description: "This is hello 2."
""",
            {},
        )
        store = RecipeSpecStore(substore)
        assert "hello1.txt" in store.keys()
        assert "subdir/hello2.txt" in store.keys()

        assert store.get_metadata("hello1.txt")["title"] == "Hello 1"
        assert store.get_metadata("hello1.txt")["description"] == "This is hello 1."
        assert store.get_bytes("hello1.txt") == b"Hello, RECIPES"
        assert store.get_metadata("hello1.txt")["title"] == "Hello 1"
        assert store.get_metadata("hello1.txt")["description"] == "This is hello 1."

        assert store.get_metadata("subdir/hello2.txt")["title"] == "Hello 2"
        assert (
            store.get_metadata("subdir/hello2.txt")["description"] == "This is hello 2."
        )
        assert store.get_bytes("subdir/hello2.txt") == b"Hello, subdir"
        assert store.get_metadata("subdir/hello2.txt")["title"] == "Hello 2"
        assert (
            store.get_metadata("subdir/hello2.txt")["description"] == "This is hello 2."
        )
