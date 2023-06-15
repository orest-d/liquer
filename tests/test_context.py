#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer execution context.
"""
import pytest
from liquer.context import *
from liquer.recipes import *
from liquer.parser import ActionRequest
from liquer.state import State, set_var
from liquer.commands import reset_command_registry, command, first_command
from liquer import evaluate
from liquer.store import set_store

class TestContext:
    def test_evaluate_action(self):
        reset_command_registry()

        @command
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a + b

        context = get_context()
        action = ActionRequest.from_arguments("test_callable", "1")
        result = context.evaluate_action(State(), action)
        assert not result.is_volatile()
        assert result.get() == 124
        assert result.metadata["commands"][-1] == ["test_callable", "1"]

    def test_evaluate_action_with_arguments(self):
        reset_command_registry()

        @command
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a + b

        context = get_context()
        action = ActionRequest.from_arguments("test_callable", "1")
        result = context.evaluate_action(State(), action, extra_parameters=[234])
        assert result.is_volatile()
        assert result.get() == 235
        assert result.metadata["commands"][-1] == ["test_callable", "1"]

    def test_evaluate_action_with_arguments_dictionary(self):
        reset_command_registry()

        @command
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a + b

        context = get_context()
        action = ActionRequest.from_arguments("test_callable", "1")
        result = context.evaluate_action(State(), action, extra_parameters={"b":234})
        assert result.is_volatile()
        assert result.get() == 235
        assert result.metadata["commands"][-1] == ["test_callable", "1"]

    def test_evaluate_query_with_arguments(self):
        reset_command_registry()

        @command
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a + b

        result = get_context().evaluate("test_callable-1")
        assert not result.is_volatile()
        assert result.get() == 124

        result = get_context().evaluate("test_callable-1", extra_parameters=[234])
        assert result.is_volatile()
        assert result.get() == 235

    def test_evaluate_query_with_arguments_dict(self):
        reset_command_registry()

        @command
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a + b

        result = get_context().evaluate("test_callable-1")
        assert not result.is_volatile()
        assert result.get() == 124

        result = get_context().evaluate("test_callable-1", extra_parameters={"b":234})
        assert result.is_volatile()
        assert result.get() == 235

    def test_evaluate_command_with_attributes(self):
        reset_command_registry()

        @command(ABC="def")
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a + b

        context = get_context()
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

        context = get_context()
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
             get_context()
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
             get_context()
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
        def varcommand_state(state,context=None):
            is_initial = state.vars.get("test_var") == "INITIAL"
            state.vars["test_var"] = "MODIFIED"
            return is_initial

        @command
        def check1(state, context=None):
            print(f"Check1: ", state.vars["test_var"])
            return state.vars["test_var"] == "MODIFIED"

        @command
        def check2(state, context=None):
            print(f"Check2: ", context.vars.test_var)
            return context.vars.test_var == "MODIFIED"

        assert get_context().evaluate("varcommand").get() == True
        assert get_context().evaluate("varcommand_state").get() == True
        assert get_context().evaluate("check1").get() == False
        assert get_context().evaluate("check2").get() == False
        assert get_context().evaluate("varcommand/check1").get() == True
        assert get_context().evaluate("varcommand/check2").get() == True
        assert get_context().evaluate("varcommand_state/check1").get() == True
        assert get_context().evaluate("varcommand_state/check2").get() == True

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
        set_store(store)
        assert "hello1.txt" in store.keys()
        assert "subdir/hello2.txt" in store.keys()
        assert "x/hello3.txt" in store.keys()
        assert "x/subdir/hello4.txt" in store.keys()

        assert store.get_bytes("hello1.txt") == b"Hello, RECIPES"
        assert store.get_bytes("subdir/hello2.txt") == b"Hello, subdir"
        assert store.get_bytes("x/hello3.txt") == b"Hello, RECIPES_X"
        assert store.get_bytes("x/subdir/hello4.txt") == b"Hello, subdir_x"
        set_store(None)

    def test_context_key(self):
        import liquer.store as st

        reset_command_registry()

        @first_command
        def hello(x, context=None):
            s=f"Hello, {x} cwd_key:{repr(context.cwd_key)} evaluated_key:{repr(context.evaluated_key)}"
            print("++++++",s)
            print("CONTEXT IN hello:",id(context))
            return s

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
        store = RecipeSpecStore(substore)
        set_store(store)
        assert "hello1.txt" in store.keys()
        assert "subdir/hello2.txt" in store.keys()

        assert store.get_bytes("hello1.txt") == b"Hello, RECIPES cwd_key:'' evaluated_key:'hello1.txt'"
        assert store.get_bytes("subdir/hello2.txt") == b"Hello, subdir cwd_key:'subdir' evaluated_key:'subdir/hello2.txt'"
        set_store(None)

    def test_relative_path(self):
        import liquer.store as st

        reset_command_registry()

        @command
        def c(x):
            return x
        
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
  - hello1.txt/-/c/hello1copy0.txt
  - subdir/hello2.txt/-/c/hello2copy0.txt
  - ./hello2.txt/-/c/hello2copy.txt
  - ../hello1.txt/-/c/hello1copy.txt
""",
            {},
        )
        store = RecipeSpecStore(substore)
        st.set_store(store)
        assert "hello1.txt" in store.keys()
        assert "subdir/hello2.txt" in store.keys()
        assert "subdir/hello1copy0.txt" in store.keys()
        assert "subdir/hello2copy0.txt" in store.keys()
        assert "subdir/hello1copy.txt" in store.keys()
        assert "subdir/hello2copy.txt" in store.keys()

        assert store.get_bytes("hello1.txt") == b"Hello, RECIPES"
        assert store.get_bytes("subdir/hello2.txt") == b"Hello, subdir"
        assert store.get_bytes("subdir/hello1copy0.txt") == b"Hello, RECIPES"
        assert store.get_bytes("subdir/hello2copy0.txt") == b"Hello, subdir"
        assert store.get_bytes("subdir/hello1copy.txt") == b"Hello, RECIPES"
        assert store.get_bytes("subdir/hello2copy.txt") == b"Hello, subdir"
        st.set_store(None)

    def test_evaluate_template_with_relative_path(self):
        import liquer.store as st

        reset_command_registry()

        @command
        def c(x):
            return x
        
        @first_command
        def hello(x):
            return f"Hello, {x}"

        @first_command
        def template1():
            return f"Template1 $-R/./hello.txt$"

        @first_command
        def template2():
            return f"Template2 $-R/../hello.txt$"

        @command
        def evaluate(txt, context=None):
            return context.evaluate_template(txt, path=context.cwd_key)

        substore = st.MemoryStore()
        substore.store(
            "recipes.yaml",
            """
RECIPES:
  - hello-RECIPES/hello.txt
  - template1/evaluate/template1.txt

subdir:
  - hello-subdir/hello.txt
  - template1/evaluate/template1.txt
  - template2/evaluate/template2.txt
""",
            {},
        )
        store = RecipeSpecStore(substore)
        st.set_store(store)
        assert "hello.txt" in store.keys()
        assert "template1.txt" in store.keys()
        assert "subdir/hello.txt" in store.keys()
        assert "subdir/template1.txt" in store.keys()
        assert "subdir/template2.txt" in store.keys()

        assert store.get_bytes("hello.txt") == b"Hello, RECIPES"
        assert store.get_bytes("subdir/hello.txt") == b"Hello, subdir"
        assert store.get_bytes("template1.txt") == b"Template1 b'Hello, RECIPES'"
        assert store.get_bytes("subdir/template1.txt") == b"Template1 b'Hello, subdir'"
        assert store.get_bytes("subdir/template2.txt") == b"Template2 b'Hello, RECIPES'"
        st.set_store(None)

    def test_status(self):
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
        store = RecipeSpecStore(substore)
        set_store(store)

        assert "hello1.txt" in store.get_bytes(store.STATUS_FILE).decode("utf-8")
        assert "recipe " in store.get_bytes(store.STATUS_FILE).decode("utf-8")
        assert store.get_bytes("hello1.txt") == b"Hello, RECIPES"
        assert "hello1.txt" in store.get_bytes(store.STATUS_FILE).decode("utf-8")
        assert "ready " in store.get_bytes(store.STATUS_FILE).decode("utf-8")
        assert store.get_bytes("subdir/hello2.txt") == b"Hello, subdir"
        assert "hello2.txt" in store.get_bytes("subdir/"+store.STATUS_FILE).decode("utf-8")
        assert "ready " in store.get_bytes("subdir/"+store.STATUS_FILE).decode("utf-8")

        set_store(None)

    def test_clean_recipes(self):
        import importlib
        from liquer import evaluate
        import liquer.ext.basic
        import liquer.ext.meta
        import liquer.store as st
        from liquer.commands import reset_command_registry

        reset_command_registry()  # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.basic)
        importlib.reload(liquer.ext.meta)

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
        store = RecipeSpecStore(substore)
        store_backup = st.get_store()
        st.set_store(store)
        try:
            assert store.get_metadata("hello1.txt")["status"] == Status.RECIPE.value
            assert store.get_metadata("subdir/hello2.txt")["status"] == Status.RECIPE.value

            assert store.get_bytes("hello1.txt") == b"Hello, RECIPES"
            assert store.get_bytes("subdir/hello2.txt") == b"Hello, subdir"

            assert store.get_metadata("hello1.txt")["status"] == Status.READY.value
            assert store.get_metadata("subdir/hello2.txt")["status"] == Status.READY.value

            assert evaluate("-R-meta/subdir/-/ns-meta/clean_recipes").get()["removed"] == ["subdir/hello2.txt"]

            assert store.get_metadata("hello1.txt")["status"] == Status.READY.value
            assert store.get_metadata("subdir/hello2.txt")["status"] == Status.RECIPE.value



        finally:
            st.set_store(store_backup)


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
        import liquer.constants as consts

        reset_command_registry()

        @first_command
        def hello(x):
            return f"Hello, {x}"

        @first_command
        def error():
            raise Exception("Error")

        substore = st.MemoryStore()
        substore.store(
            "recipes.yaml",
            """
RECIPES:
  - query: hello-RECIPES/hello1.txt
    title: "Hello 1"
    description: "This is hello 1."
  - query: error/error.txt
    title: "Error example"
    description: "Should fail."
subdir:
  - query: hello-subdir/hello.txt
    filename: hello2.txt
    title: "Hello 2"
    description: "This is hello 2."
""",
            {},
        )
        store = RecipeSpecStore(substore)
        set_store(store)
        assert "hello1.txt" in store.keys()
        assert "subdir/hello2.txt" in store.keys()

        assert store.get_metadata("hello1.txt")["status"] == consts.Status.RECIPE.value
        assert store.get_metadata("hello1.txt")["title"] == "Hello 1"
        assert store.get_metadata("hello1.txt")["description"] == "This is hello 1."
        assert store.get_bytes("hello1.txt") == b"Hello, RECIPES"
        assert store.get_metadata("hello1.txt")["status"] == consts.Status.READY.value
        assert store.get_metadata("hello1.txt")["title"] == "Hello 1"
        assert store.get_metadata("hello1.txt")["description"] == "This is hello 1."

        assert store.get_metadata("error.txt")["status"] == consts.Status.RECIPE.value
        try:
            assert store.get_bytes("error.txt") == b"Hello, RECIPES"
        except:
            pass
        print(store.get_metadata("error.txt"))
        assert store.get_metadata("error.txt")["status"] == consts.Status.ERROR.value

        assert store.get_metadata("subdir/hello2.txt")["status"] == consts.Status.RECIPE.value
        assert store.get_metadata("subdir/hello2.txt")["title"] == "Hello 2"
        assert (
            store.get_metadata("subdir/hello2.txt")["description"] == "This is hello 2."
        )
        assert store.get_bytes("subdir/hello2.txt") == b"Hello, subdir"
        assert store.get_metadata("subdir/hello2.txt")["status"] == consts.Status.READY.value
        assert store.get_metadata("subdir/hello2.txt")["title"] == "Hello 2"
        assert (
            store.get_metadata("subdir/hello2.txt")["description"] == "This is hello 2."
        )
        set_store(None)

    def test_indexer(self):
        import liquer.indexer as ix

        reset_command_registry()
        ix.reset_index_registry()

        @first_command
        def hello(x):
            return f"Hello, {x}"

        assert get_context().evaluate("hello-world").get() == "Hello, world"
        assert get_context().evaluate("hello-world").metadata.get("tools") is None

        ix.init_indexer_registry()

        assert get_context().evaluate("hello-world").metadata.get("tools") is not None
