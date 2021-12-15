#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer dependencies module.
"""
import pytest
from liquer.dependencies import Dependencies
from liquer import *
from liquer.commands import reset_command_registry, command_registry
from liquer.state import State

class TestDependencies:
    def test_create(self):
        m = Dependencies()
        assert "commands" in m.as_dict()
    def test_command(self):
        reset_command_registry()

        @command
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a + b

        ns, _command, command_metadata = command_registry().resolve_command(State(),"test_callable")
        m = Dependencies()
        m.add_command_dependency(ns, command_metadata)
        assert "ns-root/test_callable" in m.as_dict()["commands"]
