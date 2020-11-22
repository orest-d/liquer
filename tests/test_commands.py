#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer argument parser and command registry.
'''
import pytest
from liquer.commands import *
from liquer.state import State


class TestArgumentParser:
    def test_argument_parser(self):
        parser = GENERIC_AP + INT_AP + FLOAT_AP + BOOLEAN_AP
        metadata = [None, None, None, None]
        assert parser.parse(metadata, ["abc", "123", "23.4", "T"]) == (
            ["abc", 123, 23.4, True], [])
        assert parser.parse(metadata, ["abc", "123", "23.4", "T", "xxx"]) == (
            ["abc", 123, 23.4, True], ["xxx"])

    def test_argument_parse_meta(self):
        parser = GENERIC_AP + INT_AP + FLOAT_AP + BOOLEAN_AP
        metadata = [111, 222, 333, 444]
        assert parser.parse_meta(metadata, ["abc", "123", "23.4", "T", "xxx"]) == (
            ["abc", 123, 23.4, True], [("abc",111), (123,222), (23.4,333), (True,444)], ["xxx"])

    def test_argument_parse_meta_with_context(self):
        parser = GENERIC_AP + CONTEXT_AP + INT_AP + FLOAT_AP + BOOLEAN_AP
        metadata = [111, "ctx", 222, 333, 444]
        class MyContext:
            raw_query="query"
        context=MyContext()
        assert parser.parse_meta(metadata, ["abc", "123", "23.4", "T", "xxx"], context=context) == (
            ["abc", context, 123, 23.4, True], [("abc",111), (context,"ctx"), (123,222), (23.4,333), (True,444)], ["xxx"])

    def test_argument_parser_add(self):
        parser = GENERIC_AP + INT_AP
        parser += FLOAT_AP
        parser += BOOLEAN_AP
        metadata = [None, None, None, None]
        assert parser.parse(metadata, ["abc", "123", "23.4", "T"]) == (
            ["abc", 123, 23.4, True], [])

    def test_list_argument_parser(self):
        parser = GENERIC_AP + INT_AP + FLOAT_AP + BOOLEAN_AP + LIST_AP
        metadata = [None, None, None, None, None]
        assert parser.parse(metadata, ["abc", "123", "23.4", "T"]) == (
            ["abc", 123, 23.4, True, []], [])
        assert parser.parse(metadata, ["abc", "123", "23.4", "T", "1234", "2345"]) == (
            ["abc", 123, 23.4, True, ["1234", "2345"]], [])


class TestCommands:
    def test_from_callable(self):
        def test_callable(state, a, b: bool, c=123):
            pass
        meta = command_metadata_from_callable(test_callable)
        assert meta.name == "test_callable"
        assert meta.arguments[0]["name"] == "a"
        assert meta.arguments[0]["type"] == None
        assert meta.arguments[1]["name"] == "b"
        assert meta.arguments[1]["type"] == "bool"
        assert meta.arguments[2]["name"] == "c"
        assert meta.arguments[2]["type"] == "int"

    def test_parser_from_callable(self):
        def test_callable(state, a, b: bool, c=123):
            pass
        meta = command_metadata_from_callable(test_callable)
        parser = argument_parser_from_command_metadata(meta)
        assert parser.parse(meta.arguments, ["abc", "T", "234"]) == (
            ["abc", True, 234], [])

    def test_parser_from_callable(self):
        def test_callable(state, a, b: bool, c=123):
            pass
        meta = command_metadata_from_callable(test_callable)
        parser = argument_parser_from_command_metadata(meta)
        assert parser.parse(meta.arguments, ["abc", "T", "234"]) == (
            ["abc", True, 234], [])

    def test_command(self):
        reset_command_registry()
        @command
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a+b
        result = command_registry().executables["root"]["test_callable"](State(), "1")
        assert result.get() == 124

    def test_first_command(self):
        reset_command_registry()
        @first_command
        def test_callable(a: int, b=123):
            return a+b
        result = command_registry().executables["root"]["test_callable"](State(), "1")
        assert result.get() == 124

#    def test_evaluate_command(self):
#        reset_command_registry()
#        @command
#        def test_callable(state, a: int, b=123):  # has state as a first argument
#            return a+b
#        cmd = ["test_callable", "1"]
#        result = command_registry().evaluate_command(
#            State(), cmd)
#        assert result.get() == 124
#        assert result.metadata["commands"][-1] == cmd

#    def test_evaluate_command_with_attributes(self):
#        reset_command_registry()
#        @command(ABC="def")
#        def test_callable(state, a: int, b=123):  # has state as a first argument
#            return a+b
#        cmd = ["test_callable", "1"]
#        result = command_registry().evaluate_command(
#            State(), cmd)
#        assert result.get() == 124
#        assert result.metadata["commands"][-1] == cmd
#        assert result.metadata["attributes"]["ABC"] == "def"

#    def test_evaluate_chaining_attributes(self):
#        reset_command_registry()
#        @command(ABC="def")
#        def test_callable1(state, a: int, b=123):  # has state as a first argument
#            return a+b
#        @command
#        def test_callable2(state):  # has state as a first argument
#            return state
#        cmd1 = ["test_callable1", "1"]
#        cmd2 = ["test_callable2"]
#        state1 = command_registry().evaluate_command(
#            State(), cmd1)
#        assert state1.get() == 124
#        assert state1.metadata["attributes"]["ABC"] == "def"
#        state2 = command_registry().evaluate_command(
#            state1, cmd2)
#        assert state2.get() == 124
#        assert state2.metadata["attributes"]["ABC"] == "def"

    def test_evaluate_chaining_exceptions(self):
        import importlib
        from liquer import evaluate
        import liquer.ext.basic
        from liquer.commands import reset_command_registry
        reset_command_registry() # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.basic)

        @command(ABC="def", ns="testns", context_menu="menu")
        def test_callable1(state, a: int, b=123):  # has state as a first argument
            return a+b
        @command
        def test_callable2(state):  # has state as a first argument
            return state
        state1 = evaluate("ns-testns/test_callable1-1")
        assert state1.get() == 124
        assert state1.metadata["attributes"]["ABC"] == "def"
        assert state1.metadata["attributes"]["ns"] == "testns"
        assert state1.metadata["attributes"]["context_menu"] == "menu"
        state2 = evaluate("ns-testns/test_callable1-1/test_callable2")
        assert state2.get() == 124
        assert state2.metadata["attributes"]["ABC"] == "def"
        assert state2.metadata["attributes"].get("ns")!="testns"
        assert "context_menu" not in state2.metadata["attributes"]

#    def test_state_command(self):
#        reset_command_registry()
#        @command
#        def statecommand(state):  # has state as a first argument
#            assert isinstance(state, State)
#            return 123+state.get()
#        assert command_registry().evaluate_command(
#            State().with_data(1), ["statecommand"]).get() == 124

#    def test_nonstate_command(self):
#        reset_command_registry()
#        @command
#        def nonstatecommand(x: int):  # has state as a first argument
#            assert x == 1
#            return 123+x
#        assert command_registry().evaluate_command(
#            State().with_data(1), ["nonstatecommand"]).get() == 124

    def test_as_dict(self):
        reset_command_registry()
        @command
        def somecommand(x: int):  # has state as a first argument
            return 123+x
        assert "somecommand" in command_registry().as_dict()["root"]

    def test_duplicate_registration(self):
        reset_command_registry()
        def somecommand(x: int):  # has state as a first argument
            return 123+x
        command(somecommand)
        command(somecommand)
        assert "somecommand" in command_registry().as_dict()["root"]

    def test_changing_attributes(self):
        reset_command_registry()
        def somecommand(x: int):  # has state as a first argument
            return 123+x
        command(somecommand)
        assert "abc" not in command_registry().metadata["root"]["somecommand"].attributes
        command(abc="def")(somecommand)
        assert "def" == command_registry().metadata["root"]["somecommand"].attributes["abc"]

    def test_registration_modification(self):
        import importlib
        import liquer.ext.basic
        from liquer.commands import reset_command_registry
        reset_command_registry() # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.basic)

        assert "flag" in command_registry().as_dict()["root"]

        try:
            @command
            def flag(name):
                return f"New definition of flag called with {name}"
            redefined=True
        except:
            redefined=False
        assert not redefined

        try:
            @first_command(modify_command=True)
            def flag(name):
                return f"New definition of flag called with {name}"
            redefined=True
        except:
            redefined=False
        assert redefined

        # Cleanup
        reset_command_registry() # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.basic)

    def test_registration_namespace(self):
        import importlib
        from liquer import evaluate
        import liquer.ext.basic
        from liquer.commands import reset_command_registry
        reset_command_registry() # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.basic)

        assert "flag" in command_registry().as_dict()["root"]

        try:
            @command(ns="new")
            def flag(state, name):
                return f"New definition of flag called with {name}"
            redefined=True
        except:
            redefined=False

        assert redefined
#        assert evaluate("/flag-test-f/flag-test/state_variable-test").get() == True
#        assert evaluate("/flag-test-f/ns-root/flag-test/state_variable-test").get() == True
        assert evaluate("/flag-test-f/ns-new/flag-test/state_variable-test").get() == False

        # Cleanup
        reset_command_registry() # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.basic)

class TestRemoteCommandsRegistry:
    def test_encode_decode_registration(self):
        def f(x):
            return x*102
        metadata = command_metadata_from_callable(
            f, has_state_argument=False, attributes={})
        b = RemoteCommandRegistry.encode_registration(f, metadata)
        assert b[0]==b"B"[0]

        r_f, r_metadata, r_modify = RemoteCommandRegistry.decode_registration(b)
        assert r_f(3) == 306

    def test_encode_decode_registration_base64(self):
        def f(x):
            return x*102
        metadata = command_metadata_from_callable(
            f, has_state_argument=False, attributes={})
        b = RemoteCommandRegistry.encode_registration_base64(f, metadata)
        assert b[0]==b"E"[0]

        r_f, r_metadata, r_modify = RemoteCommandRegistry.decode_registration(b)
        assert r_f(3) == 306

    def test_serialized_registration(self):
        from liquer import evaluate
        reset_command_registry()
        def f(x:int):
            return x*102
        metadata = command_metadata_from_callable(
            f, has_state_argument=False, attributes={})
        b = command_registry().encode_registration(f, metadata)
        enable_remote_registration()
        command_registry().register_remote_serialized(b)
        assert evaluate("f-3").get() == 306
        reset_command_registry()
        disable_remote_registration()
 