#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer parser.
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
        result = command_registry().executables["test_callable"](State(), "1")
        assert result.get() == 124

    def test_first_command(self):
        reset_command_registry()
        @first_command
        def test_callable(a: int, b=123):
            return a+b
        result = command_registry().executables["test_callable"](State(), "1")
        assert result.get() == 124

    def test_evaluate_command(self):
        reset_command_registry()
        @command
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a+b
        cmd = ["test_callable", "1"]
        result = command_registry().evaluate_command(
            State(), cmd)
        assert result.get() == 124
        assert result.commands[-1] == cmd

    def test_state_command(self):
        reset_command_registry()
        @command
        def statecommand(state):  # has state as a first argument
            assert isinstance(state, State)
            return 123+state.get()
        assert command_registry().evaluate_command(
            State().with_data(1), ["statecommand"]).get() == 124

    def test_nonstate_command(self):
        reset_command_registry()
        @command
        def nonstatecommand(x: int):  # has state as a first argument
            assert x == 1
            return 123+x
        assert command_registry().evaluate_command(
            State().with_data(1), ["nonstatecommand"]).get() == 124
